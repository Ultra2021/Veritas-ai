"""Agent 1: the Interview Director.

The Interview Director acts like a professional interviewer. It reads
the candidate profile, curriculum, and interview state, then generates
the next question and decides which competency to explore next.

It NEVER evaluates candidate answers, NEVER scores or updates evidence,
and NEVER decides whether a candidate should be hired — those belong
exclusively to the Evidence Engine.

Questions are sourced from a swappable ``QuestionBank`` strategy, so an
LLM-backed bank (Gemini or Groq) can replace the static one without
changing the director's logic.
"""

import types

from pydantic import BaseModel, ConfigDict

from agents.question_bank import QuestionBank, StaticQuestionBank
from models.interview_state import (
    CompetencyState,
    ConversationMessage,
    InterviewStage,
    InterviewState,
)
from services.curriculum_service import CurriculumService


class InterviewResponse(BaseModel):
    """Structured, JSON-serializable contract for FastAPI and the frontend.

    Exposes ``reply``, ``question``, ``currentCompetency``, and
    ``interviewStage`` directly so the Next.js frontend can render the
    response without additional transformation.
    """

    model_config = ConfigDict(extra="forbid")

    reply: str = ""
    question: str = ""
    currentCompetency: str | None = None
    interviewStage: InterviewStage | None = None


class InterviewDirector:
    """Conducts interviews by sourcing questions from a QuestionBank."""

    def __init__(
        self,
        candidate_service: types.ModuleType,
        curriculum_service: CurriculumService,
        question_bank: QuestionBank | None = None,
    ) -> None:
        """Initialize the director with its data and question dependencies.

        ``candidate_service`` is the ``candidate_service`` module exposing
        ``get_candidate`` and ``get_candidate_summary``; ``curriculum_service``
        is a ``CurriculumService`` instance. ``question_bank`` defaults to a
        ``StaticQuestionBank`` and may be swapped for a Gemini-backed strategy.
        """
        self._candidate_service = candidate_service
        self._curriculum_service = curriculum_service
        self._question_bank: QuestionBank = question_bank or StaticQuestionBank()

    def _next_question_id(self, state: InterviewState) -> str:
        """Return the next deterministic question id for a session."""
        interviewer_messages = [
            message
            for message in state.conversationHistory
            if message.role == "interviewer"
        ]
        return f"Q{len(interviewer_messages) + 1}"

    def _announce(self, state: InterviewState, message: str) -> None:
        """Append a system message to the conversation history."""
        state.conversationHistory.append(
            ConversationMessage(role="system", message=message)
        )

    def _ask_question(self, state: InterviewState, question: str, competency: str) -> str:
        """Record a new interviewer question in the session state."""
        state.currentQuestion = question
        state.currentCompetency = competency
        state.currentQuestionId = self._next_question_id(state)
        state.conversationHistory.append(
            ConversationMessage(role="interviewer", message=question)
        )
        return state.currentQuestionId

    def _asked_questions(self, state: InterviewState) -> set[str]:
        """Return the set of interviewer questions already asked."""
        return {
            message.message
            for message in state.conversationHistory
            if message.role == "interviewer"
        }

    def _next_question_for(self, state: InterviewState, competency: str) -> str:
        """Return the next unasked question from the bank for a competency."""
        for question in self._question_bank.questions_for(competency, state):
            if question not in self._asked_questions(state):
                return question
        return self._fallback_question(competency)

    def _fallback_question(self, competency: str) -> str:
        """Return a deterministic fallback question when the bank is empty."""
        curriculum_topics = {
            topic.title for topic in self._curriculum_service.get_topics()
        }
        if competency in curriculum_topics:
            return f"Explain the key concepts behind {competency}."
        return f"Tell me more about your experience with {competency}."

    def start_interview(self, state: InterviewState) -> InterviewResponse:
        """Begin an interview for the session.

        Reads the candidate profile and summary, determines the first
        competency, generates a welcome message and first question, and
        records them in the session state.
        """
        profile = self._candidate_service.get_candidate(state.candidateId)
        summary = self._candidate_service.get_candidate_summary(state.candidateId)

        competency = self._resolve_competency(state) or "technicalKnowledge"
        welcome = (
            f"Welcome, {profile.member.name}. Let's explore your background as a "
            f"{summary.jobRole} with {summary.yearsExperience} years of experience."
        )
        question = self._next_question_for(state, competency)

        self._announce(state, welcome)
        self._ask_question(state, question, competency)
        state.interviewStage = "interviewing"

        return InterviewResponse(
            reply=welcome,
            question=question,
            currentCompetency=competency,
            interviewStage="interviewing",
        )

    def generate_next_question(self, state: InterviewState) -> InterviewResponse:
        """Generate the next interview question.

        Uses the current competency when still active, otherwise selects
        the next competency. Questions come from the ``QuestionBank`` and
        are never repeated within a session.
        """
        competency = self._resolve_competency(state) or "technicalKnowledge"
        question = self._next_question_for(state, competency)
        self._ask_question(state, question, competency)
        return InterviewResponse(
            reply="",
            question=question,
            currentCompetency=competency,
            interviewStage="interviewing",
        )

    def generate_followup_question(self, state: InterviewState) -> InterviewResponse:
        """Generate a deeper follow-up question for the current competency."""
        selected = self.select_next_competency(state)
        competency = (
            state.currentCompetency
            or (selected.competency if selected else "technicalKnowledge")
        )
        question = self._question_bank.followup_for(competency, state)
        self._ask_question(state, question, competency)
        return InterviewResponse(
            reply="",
            question=question,
            currentCompetency=competency,
            interviewStage="interviewing",
        )

    def select_next_competency(self, state: InterviewState) -> CompetencyState | None:
        """Select the next competency to interview.

        Prefers ``pending`` competencies, skips verified ones, uses the
        curriculum to prioritize curriculum-mapped topics, and never
        repeats verified competencies. Returns ``None`` when every
        competency has been verified.
        """
        curriculum_topics = {
            topic.title for topic in self._curriculum_service.get_topics()
        }
        available = [
            entry for entry in state.competencies if entry.status != "verified"
        ]

        for status in ("pending", "needs_followup", "in_progress"):
            matches = [entry for entry in available if entry.status == status]
            if not matches:
                continue
            matches.sort(
                key=lambda entry: (
                    entry.competency not in curriculum_topics,
                    entry.competency,
                )
            )
            return matches[0]
        return None

    def _resolve_competency(self, state: InterviewState) -> str | None:
        """Resolve the competency for the next question.

        Keeps the current competency while it is still active, otherwise
        selects the next one; falls back to the recorded current
        competency when nothing remains.
        """
        if state.currentCompetency:
            current = next(
                (
                    entry
                    for entry in state.competencies
                    if entry.competency == state.currentCompetency
                    and entry.status != "verified"
                ),
                None,
            )
            if current is not None:
                return current.competency

        selected = self.select_next_competency(state)
        if selected is not None:
            return selected.competency
        return state.currentCompetency

    def generate_mock_question(self, competency: str) -> str:
        """Return the first deterministic question for a competency.

        Delegates to the ``QuestionBank``; falls back to a curriculum- or
        template-derived question when the bank has no entry.
        """
        questions = self._question_bank.questions_for(competency)
        if questions:
            return questions[0]
        return self._fallback_question(competency)

    def end_interview(self, state: InterviewState) -> InterviewResponse:
        """End the interview and hand off to evaluation.

        Advances the session stage to ``evaluating`` so the Evidence
        Engine and frontend know the questioning phase is complete. No
        feedback is generated here; evaluation belongs to the Evidence
        Engine.
        """
        state.interviewStage = "evaluating"
        return InterviewResponse(
            reply="Interview completed.",
            currentCompetency=state.currentCompetency,
            interviewStage="evaluating",
        )
