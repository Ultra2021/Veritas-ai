"""Module 7: the orchestration layer connecting the existing agents.

``InterviewService`` wires the already-built components into one complete
interview workflow:

    CandidateService
            |
            v
    SessionService --> InterviewState
            |
            v
    InterviewDirector --> next question
            |
            v
        candidate answer
            |
            v
    EvidenceEngine --> EvidenceEvaluation
            |
            v
    InterviewState --> InterviewDirector --> next question / end

It owns the workflow only; it does NOT own AI reasoning. Question
generation is delegated to the InterviewDirector, answer evaluation to
the EvidenceEngine, and state persistence to the SessionService.
``InterviewState`` remains the single shared state object, and the
SessionService remains the source of truth for it.
"""

import types
from uuid import UUID

from agents.evidence_engine import EvidenceEngine
from agents.interview_director import InterviewDirector
from models.evidence import EvidenceEvaluation
from models.interview_response import InterviewTurnResponse
from models.interview_state import CompetencyState, InterviewState
from services.curriculum_service import CurriculumDayNotFoundError, CurriculumService
from services.session_service import SessionService


class InterviewServiceError(ValueError):
    """Base error raised by InterviewService failures."""


class InterviewCompletedError(InterviewServiceError):
    """Raised when an interaction is attempted on a completed interview."""


class MissingCurrentQuestionError(InterviewServiceError):
    """Raised when the session has no current question to answer."""


class EmptyAnswerError(InterviewServiceError):
    """Raised when a candidate answer is empty or whitespace."""


class InvalidEvaluationError(InterviewServiceError):
    """Raised when the Evidence Engine returns an unusable evaluation."""


_VALID_NEXT_ACTIONS = ("FOLLOW_UP", "NEXT_COMPETENCY", "VERIFY")


class InterviewService:
    """Thin orchestration of the dual-agent interview workflow.

    All dependencies are injected through the constructor so Module 8 can
    compose a fully configured service for FastAPI without touching the
    workflow logic.
    """

    def __init__(
        self,
        candidate_service: types.ModuleType,
        curriculum_service: CurriculumService,
        session_service: SessionService,
        director: InterviewDirector,
        evidence_engine: EvidenceEngine,
    ) -> None:
        """Initialize the service with its five collaborators.

        ``candidate_service`` is the ``candidate_service`` module exposing
        ``get_candidate`` and ``get_interview_topics``; the remaining
        dependencies are existing service/agent instances.
        """
        self._candidate_service = candidate_service
        self._curriculum_service = curriculum_service
        self._session_service = session_service
        self._director = director
        self._evidence_engine = evidence_engine

    def start_interview(self, candidate_id: str) -> InterviewTurnResponse:
        """Begin an interview for a candidate and return the first turn.

        Validates the candidate, creates the session, seeds the competency
        ledger from the candidate's curriculum topics, asks the Interview
        Director for the first question, and persists the state.
        """
        self._candidate_service.get_candidate(candidate_id)

        state = self._session_service.create_session(candidate_id)
        self._seed_competencies(state, candidate_id)
        self._director.start_interview(state)
        self._session_service.update_session(state)

        return self._build_response(state)

    def _seed_competencies(self, state: InterviewState, candidate_id: str) -> None:
        """Seed the competency ledger from the candidate's curriculum topics.

        Uses the curriculum topic title (matched by mission day) as the
        competency name so the Evidence Engine's curriculum keyword
        enrichment and the director's competency selection work against
        authoritative names. Falls back to the topic title when the day
        is not present in the curriculum.
        """
        for topic in self._candidate_service.get_interview_topics(candidate_id):
            competency = self._curriculum_topic_title(topic.day) or topic.title
            state.competencies.append(
                CompetencyState(competency=competency, status="pending")
            )

    def _curriculum_topic_title(self, day: int) -> str | None:
        try:
            return self._curriculum_service.get_topic_by_day(day).title
        except CurriculumDayNotFoundError:
            return None

    def process_answer(self, session_id: UUID, answer: str) -> InterviewTurnResponse:
        """Process one candidate answer and advance the interview.

        Core interview loop: stores the answer, evaluates it with the
        Evidence Engine, updates competency evidence / Interview DNA /
        hiring confidence, records an evaluator message, then either asks
        a follow-up, moves to the next competency, or ends the interview.
        """
        state = self._session_service.get_session(session_id)
        self._validate_interaction(state, answer)

        state.currentAnswer = answer
        self._session_service.append_message(session_id, "candidate", answer)

        evaluation = self._evidence_engine.evaluate_answer(state, answer)
        if evaluation is None or not isinstance(evaluation, EvidenceEvaluation):
            raise InvalidEvaluationError(
                f"Evidence Engine returned an invalid evaluation for session {session_id}."
            )

        self._evidence_engine.update_competency(state, evaluation)
        self._evidence_engine.update_interview_dna(state, evaluation)
        self._evidence_engine.calculate_hiring_confidence(state)

        self._session_service.append_message(
            session_id,
            "evaluator",
            f"Evidence score: {evaluation.evidenceScore}/100. {evaluation.reason}",
        )

        action = self._evidence_engine.get_next_action(evaluation)
        if action not in _VALID_NEXT_ACTIONS:
            raise InvalidEvaluationError(
                f"Evidence Engine returned unknown next action {action!r}."
            )

        if action == "FOLLOW_UP":
            self._director.generate_followup_question(state)
        elif self._director.select_next_competency(state) is None:
            self._session_service.mark_completed(session_id)
        else:
            self._director.generate_next_question(state)

        self._session_service.update_session(state)
        return self._build_response(state, evidence=evaluation)

    def _validate_interaction(self, state: InterviewState, answer: str) -> None:
        """Reject interactions on an invalid session or empty answer."""
        if state.completed:
            raise InterviewCompletedError(
                f"Interview for session {state.sessionId} is already completed."
            )
        if not state.currentQuestion or not state.currentQuestionId:
            raise MissingCurrentQuestionError(
                f"Session {state.sessionId} has no current question."
            )
        if not answer or not answer.strip():
            raise EmptyAnswerError("Candidate answer must not be empty.")

    def _build_response(
        self,
        state: InterviewState,
        evidence: EvidenceEvaluation | None = None,
    ) -> InterviewTurnResponse:
        """Build the frontend-facing response from the shared state."""
        if evidence is None and state.evidenceEvaluations:
            evidence = state.evidenceEvaluations[-1]
        return InterviewTurnResponse(
            sessionId=state.sessionId,
            questionId=state.currentQuestionId,
            question=state.currentQuestion,
            currentCompetency=state.currentCompetency,
            interviewStage=state.interviewStage,
            evidence=evidence,
            competencies=state.competencies,
            hiringConfidence=state.hiringConfidence,
            interviewDNA=state.interviewDNA,
            done=state.completed,
        )
