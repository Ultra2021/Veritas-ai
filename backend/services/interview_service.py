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
from agents.interview_director import (
    MAX_FOLLOWUPS_PER_COMPETENCY,
    MAX_QUESTIONS_TO_COMPLETE,
    MIN_DISTINCT_CURRICULUM_DAYS,
    MIN_QUESTIONS_TO_COMPLETE,
    FollowUpExhaustedError,
    InterviewDirector,
)
from models.evidence import EvidenceEvaluation
from models.interview_response import FeedbackData, InterviewTurnResponse
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


class InsufficientQuestionError(InterviewServiceError):
    """Raised when no eligible competency remains before the minimum
    question and curriculum-day coverage requirements are met.

    The deterministic handling for a curriculum that cannot supply enough
    questions across enough days: the interview never completes early, but
    it also never loops forever.
    """


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

    def start_interview(
        self, candidate_id: str, session_id: UUID | str | None = None
    ) -> InterviewTurnResponse:
        """Begin an interview for a candidate and return the first turn.

        Validates the candidate, creates the session, seeds the competency
        ledger from the candidate's curriculum topics, asks the Interview
        Director for the first question, and persists the state.
        """
        self._candidate_service.get_candidate(candidate_id)

        state = self._session_service.create_session(candidate_id, sessionId=session_id)
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
                CompetencyState(
                    competency=competency,
                    status="pending",
                    day=topic.day,
                )
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

        presented = self._questions_presented(state)

        # Check adaptive completion rules:
        # 1. Hard stop at 20 questions
        # 2. Complete at >= 8 questions if evidence is sufficient
        if presented >= MAX_QUESTIONS_TO_COMPLETE:
            self._session_service.mark_completed(session_id)
            self._session_service.update_session(state)
            return self._build_response(state, evidence=evaluation)

        if (
            presented >= MIN_QUESTIONS_TO_COMPLETE
            and not evaluation.followUpRequired
            and self._evidence_engine.is_evidence_sufficient(state)
        ):
            self._session_service.mark_completed(session_id)
            self._session_service.update_session(state)
            return self._build_response(state, evidence=evaluation)

        if action == "FOLLOW_UP":
            entry = self._current_competency_state(state)
            if entry is not None and entry.attempts > MAX_FOLLOWUPS_PER_COMPETENCY:
                action = "NEXT_COMPETENCY"
            else:
                try:
                    self._director.generate_followup_question(state)
                except FollowUpExhaustedError:
                    action = "NEXT_COMPETENCY"
                else:
                    state.metadata.totalFollowUps += 1

        if action == "VERIFY":
            entry = self._current_competency_state(state)
            if entry is not None and entry.attempts > MAX_FOLLOWUPS_PER_COMPETENCY:
                action = "NEXT_COMPETENCY"
            else:
                self._director.generate_next_question(state)

        if action == "NEXT_COMPETENCY":
            covered_days = len(self._director.covered_curriculum_days(state))
            at_minimum = (
                presented >= MIN_QUESTIONS_TO_COMPLETE
                and covered_days >= MIN_DISTINCT_CURRICULUM_DAYS
            )
            next_comp = self._director.select_next_competency(state)

            if at_minimum and (next_comp is None or self._evidence_engine.is_evidence_sufficient(state)):
                self._session_service.mark_completed(session_id)
            elif next_comp is None:
                raise InsufficientQuestionError(
                    f"Cannot continue: no eligible competency remains after "
                    f"{presented} question(s) across {covered_days} curriculum "
                    f"day(s); a minimum of {MIN_QUESTIONS_TO_COMPLETE} questions "
                    f"across {MIN_DISTINCT_CURRICULUM_DAYS} distinct curriculum "
                    f"days is required."
                )
            else:
                self._director.generate_next_question(state)

        self._session_service.update_session(state)
        return self._build_response(state, evidence=evaluation)

    def end_interview(self, session_id: UUID) -> InterviewTurnResponse:
        """End an active interview session early and mark it as completed."""
        state = self._session_service.get_session(session_id)
        if not state.completed:
            self._evidence_engine.calculate_hiring_confidence(state)
            self._session_service.mark_completed(session_id)
            self._session_service.update_session(state)
        return self._build_response(state)

    def _current_competency_state(
        self,
        state: InterviewState,
    ) -> CompetencyState | None:
        """Return the ledger entry for the current competency, if any."""
        if not state.currentCompetency:
            return None
        return next(
            (
                entry
                for entry in state.competencies
                if entry.competency == state.currentCompetency
            ),
            None,
        )

    @staticmethod
    def _questions_presented(state: InterviewState) -> int:
        """Return the number of questions actually presented to the candidate.

        ``conversationHistory`` is authoritative: every presented question
        (initial scenario or follow-up) is recorded as an interviewer
        message. System, candidate, and evaluator messages never count, so
        failed or rejected generations that never reached the candidate
        are excluded.
        """
        return sum(
            1 for message in state.conversationHistory if message.role == "interviewer"
        )

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

    def _build_feedback(self, state: InterviewState) -> FeedbackData:
        """Build structured feedback per technical-spec.md upon interview completion."""
        strengths: list[str] = []
        gaps: list[str] = []
        next_steps: list[str] = []

        for eval_item in state.evidenceEvaluations:
            for s in eval_item.strengths:
                if s and s not in strengths:
                    strengths.append(s)
            for g in eval_item.gaps:
                if g and g not in gaps:
                    gaps.append(g)

        verified_comps = [c for c in state.competencies if c.status == "verified"]
        pending_comps = [c for c in state.competencies if c.status != "verified"]

        if not strengths:
            for c in verified_comps:
                strengths.append(f"Verified competency: {c.competency}")
        if not strengths:
            strengths.append("Demonstrated foundational technical knowledge across cohort topics.")

        if not gaps:
            for c in pending_comps:
                gaps.append(f"Requires deeper evidence: {c.competency}")
        if not gaps:
            gaps.append("Maintain architectural depth and edge-case handling in responses.")

        for c in pending_comps[:3]:
            next_steps.append(f"Review hands-on implementation and system design for {c.competency}.")
        if not next_steps:
            next_steps.append("Advance to production system deployment, observability, and scaling.")

        questions_count = self._questions_presented(state)
        confidence = state.hiringConfidence if state.hiringConfidence is not None else 70
        summary = (
            f"Candidate completed {questions_count} interview turn(s) across the 31-day AI Cohort curriculum. "
            f"Verified {len(verified_comps)} of {len(state.competencies)} targeted competencies with a hiring confidence score of {confidence}%."
        )

        return FeedbackData(
            summary=summary,
            strengths=strengths[:5],
            gaps=gaps[:5],
            next=next_steps[:5],
        )

    def _build_response(
        self,
        state: InterviewState,
        evidence: EvidenceEvaluation | None = None,
    ) -> InterviewTurnResponse:
        """Build the frontend & spec-facing response from the shared state."""
        if evidence is None and state.evidenceEvaluations:
            evidence = state.evidenceEvaluations[-1]

        done = state.completed
        if done:
            reply = (
                "Thank you so much for walking me through all those architectural decisions! "
                "That completes the technical portion of our interview."
            )
        else:
            last_interviewer_msgs = [
                m.message for m in state.conversationHistory if m.role == "interviewer"
            ]
            reply = last_interviewer_msgs[-1] if last_interviewer_msgs else state.currentQuestion

        feedback = self._build_feedback(state) if done else None

        return InterviewTurnResponse(
            sessionId=state.sessionId,
            candidateId=state.candidateId,
            questionId=state.currentQuestionId,
            question=state.currentQuestion,
            reply=reply,
            currentCompetency=state.currentCompetency,
            interviewStage=state.interviewStage,
            evidence=evidence,
            competencies=state.competencies,
            hiringConfidence=state.hiringConfidence,
            interviewDNA=state.interviewDNA,
            done=done,
            feedback=feedback,
        )

