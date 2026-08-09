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

import random
import types
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from agents.question_bank import QuestionBank, StaticQuestionBank
from models.interview_state import (
    CompetencyState,
    ConversationMessage,
    InterviewStage,
    InterviewState,
)
from services.curriculum_service import CurriculumService
from utils.relevance import is_irrelevant_or_gibberish

MAX_FOLLOWUPS_PER_COMPETENCY = 2
MIN_DISTINCT_CURRICULUM_DAYS = 4
MIN_QUESTIONS_TO_COMPLETE = 8
MAX_QUESTIONS_TO_COMPLETE = 20


def _session_seed(session_id: UUID | str) -> int:
    """Safely convert a UUID or string session ID into a deterministic seed integer."""
    if isinstance(session_id, UUID):
        return int(session_id)
    try:
        return int(UUID(str(session_id)))
    except Exception:
        return sum(ord(c) for c in str(session_id))


class FollowUpExhaustedError(ValueError):
    """Raised when no unique follow-up question is available for a competency."""


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

    def _ask_question(
        self, state: InterviewState, question: str, competency: str, bridge: str = ""
    ) -> str:
        """Record a new interviewer question in the session state."""
        state.currentQuestion = question
        state.currentCompetency = competency
        state.currentQuestionId = self._next_question_id(state)
        full_text = f"{bridge}\n\n{question}".strip() if bridge else question
        state.conversationHistory.append(
            ConversationMessage(role="interviewer", message=full_text)
        )
        return state.currentQuestionId

    def _asked_questions(self, state: InterviewState) -> set[str]:
        """Return the set of interviewer questions already asked."""
        asked = set()
        for message in state.conversationHistory:
            if message.role == "interviewer":
                asked.add(message.message)
                if "\n\n" in message.message:
                    asked.add(message.message.split("\n\n")[-1].strip())
        return asked

    def _build_bridge(
        self,
        state: InterviewState,
        competency: str,
        is_followup: bool = True,
        prev_competency: str | None = None,
    ) -> str:
        """Build a natural, human-sounding interviewer transition bridge."""
        rng = random.Random(
            _session_seed(state.sessionId) + len(state.conversationHistory)
        )

        answer = state.currentAnswer.strip() if state.currentAnswer else ""
        is_irrelevant, reason_type = is_irrelevant_or_gibberish(
            answer, competency=competency
        )

        latest_eval = (
            state.evidenceEvaluations[-1]
            if state.evidenceEvaluations
            else None
        )

        # 1. Switching competencies (pivot)
        if not is_followup and prev_competency and prev_competency != competency:
            if is_irrelevant or (latest_eval and latest_eval.evidenceScore == 0):
                transitions = [
                    f"Pivoting now to our next topic, {competency}:",
                    f"Let me shift gears to {competency}:",
                    f"Next up, I'd like to explore {competency}:",
                    f"Switching topics to {competency}:",
                ]
            else:
                transitions = [
                    f"Great overview on {prev_competency}! Pivoting now to {competency}:",
                    f"Thanks for walking me through your approach to {prev_competency}. Let's shift gears to {competency}:",
                    f"Understood regarding {prev_competency}. Moving on to our next topic, {competency}:",
                    f"Next up, I'd like to explore {competency}:",
                    f"Switching topics to {competency}:",
                    f"Let's talk about {competency}:",
                ]
            return rng.choice(transitions)

        # 2. Irrelevant, gibberish, evasive, or empty answer
        if is_irrelevant or not answer or (latest_eval and latest_eval.evidenceScore == 0):
            if reason_type == "evasion" or "don't know" in answer.lower() or "not sure" in answer.lower() or "idk" in answer.lower():
                evasion_openers = [
                    f"No worries at all—let me reframe this for {competency}:",
                    f"That's completely fine. Let me ask about {competency} from a different angle:",
                    f"Understood! Let's explore {competency} with a fresh scenario:",
                ]
                return rng.choice(evasion_openers)
            else:
                irrelevant_openers = [
                    f"That response doesn't seem relevant to the technical question asked. Let's focus back on {competency}:",
                    f"I didn't catch a technical explanation in your response. Let me refocus on {competency}:",
                    f"Please stay focused on the technical evaluation. Re-approaching {competency}:",
                    f"That doesn't address the technical question. Moving back to {competency}:",
                    f"Let's keep our discussion focused on the technical implementation details for {competency}:",
                ]
                return rng.choice(irrelevant_openers)

        # 3. Legitimate answer with strengths / gaps
        if latest_eval is not None:
            if latest_eval.strengths and any(
                "shows" in s.lower() or "reasoning" in s.lower() or "knowledge" in s.lower()
                for s in latest_eval.strengths
            ):
                strength_openers = [
                    f"Good point on that implementation detail! Building on your response for {competency}:",
                    f"Solid explanation. Taking that a step further for {competency}:",
                    f"Makes total sense. Expanding on your point:",
                    f"That's a helpful perspective. Following up on that:",
                    "",  # Direct question with no prefix
                ]
                return rng.choice(strength_openers)

            if latest_eval.gaps:
                gap = (
                    latest_eval.gaps[0]
                    .replace(" not addressed", "")
                    .replace(" not explained", "")
                    .strip()
                )
                if (
                    gap
                    and not gap.lower().startswith("evidence for")
                    and not gap.lower().startswith("no technical answer")
                    and not gap.lower().startswith("candidate provided an off-topic")
                ):
                    gap_openers = [
                        f"Got it. Focusing on {gap}:",
                        f"Looking closely at {gap}:",
                        f"Understood. Digging into {gap} for a moment:",
                        f"Taking a closer look at {gap}:",
                        f"On the topic of {gap}:",
                        f"Probing a bit into {gap}:",
                        "",  # Direct question with no prefix
                    ]
                    return rng.choice(gap_openers)

        general_openers = [
            f"Got it. Following up on {competency}:",
            f"Let's probe a bit deeper:",
            f"Understood. Building on that:",
            f"Taking a closer look at {competency}:",
            "",  # Direct question with no prefix
        ]
        return rng.choice(general_openers)

    def _next_question_for(self, state: InterviewState, competency: str) -> str:
        """Return the next unasked question from the bank for a competency."""
        questions = self._question_bank.questions_for(competency, state)
        if questions:
            offset = _session_seed(state.sessionId) % len(questions)
            ordered = questions[offset:] + questions[:offset]
            for question in ordered:
                if not QuestionBank._is_asked_question(question, state):
                    return question

        return self._fallback_question(competency, state)

    def _fallback_question(self, competency: str, state: InterviewState) -> str:
        """Return a deterministic fallback question when the bank is spent."""
        for question in self._fallback_questions(competency):
            if not QuestionBank._is_asked_question(question, state):
                return question
        return f"Tell me more about your technical experience with {competency}."

    def _fallback_questions(self, competency: str) -> list[str]:
        """Return deterministic fallback questions for a competency."""
        curriculum_topics = {
            topic.title for topic in self._curriculum_service.get_topics()
        }
        if competency in curriculum_topics:
            return [
                f"Explain the key concepts behind {competency}.",
                f"Walk me through a concrete example of applying {competency}.",
            ]
        return [
            f"Tell me more about your experience with {competency}.",
            f"What is your most relevant project involving {competency}?",
        ]

    def start_interview(self, state: InterviewState) -> InterviewResponse:
        """Begin an interview for the session."""
        profile = self._candidate_service.get_candidate(state.candidateId)
        summary = self._candidate_service.get_candidate_summary(state.candidateId)
        competency = self._resolve_competency(state) or "technicalKnowledge"

        rng = random.Random(_session_seed(state.sessionId))
        welcome_templates = [
            (
                f"Welcome, {profile.member.name}! Thanks for taking the time to speak with me today. "
                f"Looking at your background as a {summary.jobRole} with {summary.yearsExperience} years of experience, "
                f"I'm excited to explore your technical work from the AI cohort. "
                f"To kick things off, let's start with {competency}:"
            ),
            (
                f"Hi {profile.member.name}, great to meet you! "
                f"Given your hands-on role as a {summary.jobRole} with {summary.yearsExperience} years of experience, "
                f"I'm looking forward to our technical discussion today. "
                f"Let me begin by asking you about {competency}:"
            ),
            (
                f"Welcome, {profile.member.name}! "
                f"With {summary.yearsExperience} years of experience in {summary.jobRole} roles, "
                f"I'd love to dive into some realistic technical scenarios from your cohort journey. "
                f"First up, let's discuss {competency}:"
            ),
        ]
        welcome = rng.choice(welcome_templates)
        question = self._next_question_for(state, competency)

        self._announce(state, welcome)
        self._ask_question(state, question, competency, bridge=welcome)
        state.interviewStage = "interviewing"

        return InterviewResponse(
            reply=welcome,
            question=question,
            currentCompetency=competency,
            interviewStage="interviewing",
        )

    def generate_next_question(self, state: InterviewState) -> InterviewResponse:
        """Generate the next interview question."""
        prev_competency = state.currentCompetency
        competency = self._resolve_competency(state) or "technicalKnowledge"
        question = self._next_question_for(state, competency)
        bridge = self._build_bridge(
            state, competency, is_followup=False, prev_competency=prev_competency
        )
        self._ask_question(state, question, competency, bridge=bridge)
        return InterviewResponse(
            reply=bridge,
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
        if not question or QuestionBank._is_asked_question(question, state):
            raise FollowUpExhaustedError(
                f"No unique follow-up question available for competency '{competency}'."
            )
        bridge = self._build_bridge(state, competency, is_followup=True)
        self._ask_question(state, question, competency, bridge=bridge)
        return InterviewResponse(
            reply=bridge,
            question=question,
            currentCompetency=competency,
            interviewStage="interviewing",
        )

    def _is_eligible(self, entry: CompetencyState) -> bool:
        """A competency is interviewable until verified or follow-up budget spent."""
        if entry.status == "verified":
            return False
        if (
            entry.status == "needs_followup"
            and entry.attempts > MAX_FOLLOWUPS_PER_COMPETENCY
        ):
            return False
        return True

    def covered_curriculum_days(self, state: InterviewState) -> set[int]:
        """Return the distinct curriculum days the candidate has explored.

        A day counts as covered once the candidate has answered at least one
        question for a competency mapped to that day. Follow-up questions
        never expand coverage because they stay on the current competency.
        Competencies without a mapped day never count toward coverage.
        """
        return {
            entry.day
            for entry in state.competencies
            if entry.day is not None and entry.attempts > 0
        }

    def select_next_competency(self, state: InterviewState) -> CompetencyState | None:
        """Select the next competency to interview.

        Prefers ``pending`` competencies, skips verified and
        follow-up-exhausted ones, and uses the curriculum to prioritize
        curriculum-mapped topics. Before the minimum number of distinct
        curriculum days has been covered, competencies on uncovered days
        are prioritized so the interview spreads across the curriculum.
        Once the coverage threshold is met, normal status/name ordering
        resumes. Returns ``None`` when every competency has been verified
        or exhausted.

        The very first selection (no curriculum day covered yet) rotates
        the otherwise alphabetical ordering by a deterministic session
        seed, so different sessions may open with different competencies
        from the candidate's seeded set. Later selections keep the
        uncovered-day prioritization and alphabetical ordering unchanged.
        """
        curriculum_topics = {
            topic.title for topic in self._curriculum_service.get_topics()
        }
        available = [
            entry for entry in state.competencies if self._is_eligible(entry)
        ]

        covered = self.covered_curriculum_days(state)
        if len(covered) < MIN_DISTINCT_CURRICULUM_DAYS:
            uncovered = [
                entry
                for entry in available
                if entry.day is None or entry.day not in covered
            ]
            if uncovered:
                available = uncovered

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
            if not covered and len(matches) > 1:
                offset = _session_seed(state.sessionId) % len(matches)
                matches = matches[offset:] + matches[:offset]
            return matches[0]


        return None

    def _resolve_competency(self, state: InterviewState) -> str | None:
        """Resolve the competency for the next question.

        Keeps the current competency while it is still eligible (not
        verified and not follow-up-exhausted), otherwise selects the next
        one. Returns ``None`` when nothing remains interviewable.
        """
        if state.currentCompetency:
            current = next(
                (
                    entry
                    for entry in state.competencies
                    if entry.competency == state.currentCompetency
                    and self._is_eligible(entry)
                ),
                None,
            )
            if current is not None:
                return current.competency

        selected = self.select_next_competency(state)
        if selected is not None:
            return selected.competency
        return None

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
