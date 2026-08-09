"""In-memory interview session store.

``SessionService`` owns the lifecycle of ``InterviewState`` objects
(create, read, update, delete) and provides the only write path for all
state mutations. No interview or evaluation logic lives here; the
Interview Director and Evidence Engine interact with the interview
exclusively through this service.
"""

import threading
from datetime import datetime, timezone
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

from models.interview_state import (
    CompetencyState,
    ConversationMessage,
    ConversationRole,
    InterviewState,
)


class SessionNotFoundError(ValueError):
    """Raised when a session does not exist in the store."""


class SkillNotFoundError(ValueError):
    """Raised when a competency is not present in the ledger."""


def _utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class SessionService:
    """Maintains interview sessions held in an in-memory dictionary."""

    def __init__(self) -> None:
        self._sessions: dict[UUID, InterviewState] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _to_uuid(session_id: UUID | str) -> UUID:
        """Coerce a UUID or string session id to a deterministic valid UUID."""
        if isinstance(session_id, UUID):
            return session_id
        try:
            return UUID(session_id)
        except (ValueError, AttributeError):
            return uuid5(NAMESPACE_DNS, str(session_id))

    @staticmethod
    def _touch(state: InterviewState, interaction: bool = False) -> None:
        """Refresh the session's ``updatedAt`` (and ``lastInteractionAt``)."""
        now = _utc_now()
        state.updatedAt = now
        if interaction:
            state.metadata.lastInteractionAt = now

    def create_session(
        self, candidateId: str, sessionId: UUID | str | None = None
    ) -> InterviewState:
        """Create and store a new interview session for a candidate."""
        now = _utc_now()
        sid: UUID | str = sessionId if sessionId is not None else uuid4()
        state = InterviewState(
            sessionId=sid,
            candidateId=candidateId,
            createdAt=now,
            updatedAt=now,
        )
        state.metadata.startedAt = now
        state.metadata.lastInteractionAt = now
        with self._lock:
            self._sessions[str(sid)] = state
            key_uuid = str(self._to_uuid(sid))
            self._sessions[key_uuid] = state
        return state

    def get_session(self, sessionId: UUID | str) -> InterviewState:
        """Return the stored session for ``sessionId``.

        Raises ``SessionNotFoundError`` if the session does not exist.
        """
        with self._lock:
            key_str = str(sessionId)
            if key_str in self._sessions:
                return self._sessions[key_str]
            key_uuid = str(self._to_uuid(sessionId))
            if key_uuid in self._sessions:
                return self._sessions[key_uuid]
            raise SessionNotFoundError(f"Session not found: {sessionId}")

    def update_session(self, state: InterviewState) -> InterviewState:
        """Persist the given session, refreshing its ``updatedAt``."""
        self._touch(state)
        with self._lock:
            self._sessions[str(state.sessionId)] = state
            key_uuid = str(self._to_uuid(state.sessionId))
            self._sessions[key_uuid] = state
        return state



    def delete_session(self, sessionId: UUID) -> None:
        """Remove the session from the store.

        Raises ``SessionNotFoundError`` if the session does not exist.
        """
        with self._lock:
            try:
                del self._sessions[sessionId]
            except KeyError as exc:
                raise SessionNotFoundError(f"Session not found: {sessionId}") from exc

    def append_message(
        self,
        sessionId: UUID,
        role: ConversationRole,
        message: str,
        timestamp: datetime | None = None,
    ) -> ConversationMessage:
        """Append a conversation message to a session.

        Automatically refreshes the session's ``updatedAt`` and the
        metadata ``lastInteractionAt``.
        """
        state = self.get_session(sessionId)
        record = ConversationMessage(
            role=role,
            message=message,
            timestamp=timestamp or _utc_now(),
        )
        with self._lock:
            state.conversationHistory.append(record)
            self._touch(state, interaction=True)
        return record

    def update_evidence(self, sessionId: UUID, competency_state: CompetencyState) -> CompetencyState:
        """Create or update a competency ledger entry.

        If an entry for the competency already exists it is replaced,
        otherwise a new entry is appended.
        """
        state = self.get_session(sessionId)
        with self._lock:
            for index, entry in enumerate(state.competencies):
                if entry.competency == competency_state.competency:
                    state.competencies[index] = competency_state
                    break
            else:
                state.competencies.append(competency_state)
            self._touch(state, interaction=True)
        return competency_state

    def verify_skill(self, sessionId: UUID, competency: str) -> InterviewState:
        """Mark a competency as verified in the ledger.

        Raises ``SkillNotFoundError`` if the competency is not tracked.
        """
        state = self.get_session(sessionId)
        with self._lock:
            for entry in state.competencies:
                if entry.competency == competency:
                    entry.status = "verified"
                    self._touch(state, interaction=True)
                    return state
            raise SkillNotFoundError(f"Competency not tracked: {competency}")

    def update_hiring_confidence(self, sessionId: UUID, value: int) -> InterviewState:
        """Store the hiring confidence score (0-100) for a session.

        Only stores the value; the score itself is computed by another
        module. Validated against the model bounds.
        """
        state = self.get_session(sessionId)
        with self._lock:
            state.hiringConfidence = value
            self._touch(state)
        return state

    def mark_completed(self, sessionId: UUID) -> InterviewState:
        """Mark the interview session as finished.

        Sets ``completed`` and advances ``interviewStage`` to
        ``completed``.
        """
        state = self.get_session(sessionId)
        with self._lock:
            state.completed = True
            state.interviewStage = "completed"
            self._touch(state)
        return state
