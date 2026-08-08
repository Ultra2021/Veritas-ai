"""Tests for answer-aware follow-up question quality, grammar, and deduplication."""

from uuid import uuid4

from agents.evidence_engine import EvidenceEngine, MockEvidenceEvaluator
from agents.interview_director import InterviewDirector
from agents.question_bank import (
    GeminiQuestionBank,
    LLMQuestionBank,
    StaticQuestionBank,
    _are_near_duplicates,
    _is_overly_generic_followup,
    _normalize_question_text,
)
from models.evidence import EvidenceEvaluation
from models.interview_state import (
    CompetencyState,
    ConversationMessage,
    InterviewState,
)
from services.curriculum_service import CurriculumService
from services.interview_service import InterviewService
from services.llm_provider import LLMProvider
from services.session_service import SessionService


class MockLLMProvider(LLMProvider):
    """Mock LLM provider returning answer-aware follow-ups."""

    def questions_for(
        self,
        *,
        competency: str,
        curriculum_context: str = "",
        conversation_context: str = "",
    ) -> list[str] | None:
        return [f"What is {competency}?", f"How do you use {competency}?"]

    def followup_for(
        self,
        *,
        competency: str,
        curriculum_context: str = "",
        conversation_context: str = "",
        candidate_answer: str = "",
        gaps: tuple[str, ...] | list[str] = (),
        strengths: tuple[str, ...] | list[str] = (),
        reason: str = "",
    ) -> str | None:
        gap_str = gaps[0] if gaps else "general"
        return f"Regarding {competency} and '{candidate_answer}', how do you implement automated testing for {gap_str}?"

    def evaluate_answer(
        self,
        *,
        competency: str,
        question: str,
        answer: str,
        keywords=(),
        previous_evidence=(),
        curriculum_context: str = "",
    ) -> dict | None:
        return None


class FailingLLMProvider(LLMProvider):
    """Mock LLM provider that always fails to force static fallback."""

    def questions_for(self, *, competency: str, curriculum_context: str = "", conversation_context: str = ""):
        return None

    def followup_for(self, *, competency: str, curriculum_context: str = "", conversation_context: str = "", candidate_answer: str = "", gaps=(), strengths=(), reason: str = ""):
        return None

    def evaluate_answer(self, *, competency: str, question: str, answer: str, keywords=(), previous_evidence=(), curriculum_context: str = ""):
        return None


def _create_test_state(competency: str = "Docker") -> InterviewState:
    """Create a minimal InterviewState for testing."""
    return InterviewState(
        sessionId=uuid4(),
        candidateId="CAND-001",
        currentCompetency=competency,
        currentQuestionId="Q1",
        currentQuestion=f"Explain {competency}.",
        competencies=[CompetencyState(competency=competency, status="pending")],
        conversationHistory=[
            ConversationMessage(role="interviewer", message=f"Explain {competency}.")
        ],
    )


def test_followup_uses_candidate_answer():
    """Verify generated follow-up uses candidate answer context."""
    bank = LLMQuestionBank(provider=MockLLMProvider())
    state = _create_test_state("Docker")
    state.currentAnswer = "I would use JWT authentication."
    eval_obj = EvidenceEvaluation(
        competency="Docker",
        evidenceScore=50,
        technicalScore=50,
        reasoningScore=50,
        completenessScore=50,
        communicationScore=50,
        verified=False,
        followUpRequired=True,
        nextAction="FOLLOW_UP",
        gaps=["token expiration"],
        strengths=["basic auth"],
        reason="Missing expiration detail.",
    )
    state.evidenceEvaluations.append(eval_obj)

    followup = bank.followup_for("Docker", state)
    assert "I would use JWT authentication" in followup or "token expiration" in followup


def test_followup_targets_evidence_gap():
    """Verify follow-up targets specific EvidenceEvaluation.gaps."""
    bank = StaticQuestionBank()
    state = _create_test_state("Security")
    state.currentAnswer = "I would use OAuth."
    eval_obj = EvidenceEvaluation(
        competency="Security",
        evidenceScore=50,
        technicalScore=50,
        reasoningScore=50,
        completenessScore=50,
        communicationScore=50,
        verified=False,
        followUpRequired=True,
        nextAction="FOLLOW_UP",
        gaps=["authentication token revocation"],
        strengths=["OAuth concepts"],
        reason="Token revocation was not discussed.",
    )
    state.evidenceEvaluations.append(eval_obj)

    followup = bank.followup_for("Security", state)
    assert "authentication token revocation" in followup.lower()


def test_different_answers_produce_different_followups():
    """Verify different answers and gaps produce distinct follow-up questions."""
    bank = StaticQuestionBank()

    state1 = _create_test_state("Embeddings")
    state1.currentAnswer = "I use cosine distance."
    state1.evidenceEvaluations.append(
        EvidenceEvaluation(
            competency="Embeddings",
            evidenceScore=50,
            technicalScore=50,
            reasoningScore=50,
            completenessScore=50,
            communicationScore=50,
            verified=False,
            followUpRequired=True,
            nextAction="FOLLOW_UP",
            gaps=["high dimension scaling"],
            strengths=["cosine similarity"],
        )
    )

    state2 = _create_test_state("Embeddings")
    state2.currentAnswer = "I use dot product."
    state2.evidenceEvaluations.append(
        EvidenceEvaluation(
            competency="Embeddings",
            evidenceScore=50,
            technicalScore=50,
            reasoningScore=50,
            completenessScore=50,
            communicationScore=50,
            verified=False,
            followUpRequired=True,
            nextAction="FOLLOW_UP",
            gaps=["vector index normalization"],
            strengths=["dot product"],
        )
    )

    followup1 = bank.followup_for("Embeddings", state1)
    followup2 = bank.followup_for("Embeddings", state2)

    assert followup1 != followup2
    assert "high dimension scaling" in followup1.lower()
    assert "vector index normalization" in followup2.lower()


def test_followup_is_not_cached_by_competency():
    """Verify follow-up generation does not cache questions by competency alone."""
    bank = LLMQuestionBank(provider=MockLLMProvider())

    state1 = _create_test_state("RAG")
    state1.currentAnswer = "Answer A"
    state1.evidenceEvaluations.append(
        EvidenceEvaluation(
            competency="RAG",
            evidenceScore=50,
            technicalScore=50,
            reasoningScore=50,
            completenessScore=50,
            communicationScore=50,
            verified=False,
            followUpRequired=True,
            nextAction="FOLLOW_UP",
            gaps=["gap_alpha"],
        )
    )

    state2 = _create_test_state("RAG")
    state2.currentAnswer = "Answer B"
    state2.evidenceEvaluations.append(
        EvidenceEvaluation(
            competency="RAG",
            evidenceScore=50,
            technicalScore=50,
            reasoningScore=50,
            completenessScore=50,
            communicationScore=50,
            verified=False,
            followUpRequired=True,
            nextAction="FOLLOW_UP",
            gaps=["gap_beta"],
        )
    )

    q1 = bank.followup_for("RAG", state1)
    q2 = bank.followup_for("RAG", state2)

    assert q1 != q2
    assert "gap_alpha" in q1
    assert "gap_beta" in q2


def test_followup_does_not_repeat_existing_question():
    """Verify an existing question in conversationHistory is rejected."""
    bank = StaticQuestionBank()
    state = _create_test_state("Docker")
    existing_question = "How would you handle container orchestration and health checks in production?"
    state.conversationHistory.append(
        ConversationMessage(role="interviewer", message=existing_question)
    )

    followup = bank.followup_for("Docker", state)
    assert _normalize_question_text(followup) != _normalize_question_text(existing_question)


def test_near_duplicate_questions_are_detected():
    """Verify near-duplicate questions differing by minor wording/punctuation are detected."""
    q1 = "How would you plan a safe rollout of a new model version without downtime?"
    q2 = "How would you roll out a new model version without downtime?"
    assert _are_near_duplicates(q1, q2) is True

    q3 = "What security considerations matter when exposing an AI chatbot over an API?"
    q4 = "What security considerations matter when exposing an AI chatbot over an API"
    assert _are_near_duplicates(q3, q4) is True

    q5 = "Explain Docker containers."
    q6 = "Why would a container continuously restart?"
    assert _are_near_duplicates(q5, q6) is False


def test_followup_explicitly_targets_gap():
    """Verify follow-up explicitly targets complex gap descriptions."""
    bank = StaticQuestionBank()
    state = _create_test_state("Monitoring, Logging & Observability")
    state.currentAnswer = "I'd monitor latency with metrics like p95 and p99 response times and set alerts when they exceed defined thresholds."
    eval_obj = EvidenceEvaluation(
        competency="Monitoring, Logging & Observability",
        evidenceScore=50,
        technicalScore=50,
        reasoningScore=50,
        completenessScore=50,
        communicationScore=50,
        verified=False,
        followUpRequired=True,
        nextAction="FOLLOW_UP",
        gaps=["automated detection of LLM response quality degradation"],
        strengths=["latency monitoring"],
        reason="Lacks response quality degradation detection.",
    )
    state.evidenceEvaluations.append(eval_obj)

    followup = bank.followup_for("Monitoring, Logging & Observability", state)
    assert "quality degradation" in followup.lower() or "llm response quality" in followup.lower()
    assert _is_overly_generic_followup(followup) is False


def test_followup_builds_on_candidate_answer():
    """Verify follow-up connects to specific concepts from candidate answer."""
    bank = LLMQuestionBank(provider=MockLLMProvider())
    state = _create_test_state("Monitoring, Logging & Observability")
    state.currentAnswer = "I'd monitor latency with metrics like p95 and p99 response times and error rates."
    eval_obj = EvidenceEvaluation(
        competency="Monitoring, Logging & Observability",
        evidenceScore=50,
        technicalScore=50,
        reasoningScore=50,
        completenessScore=50,
        communicationScore=50,
        verified=False,
        followUpRequired=True,
        nextAction="FOLLOW_UP",
        gaps=["automated detection of LLM response quality degradation"],
        strengths=["latency metrics"],
    )
    state.evidenceEvaluations.append(eval_obj)

    followup = bank.followup_for("Monitoring, Logging & Observability", state)
    assert followup != ""
    assert _is_overly_generic_followup(followup) is False


def test_followup_is_not_generic():
    """Verify generic follow-up patterns are rejected."""
    generic_q = "How would you handle that in practice?"
    assert _is_overly_generic_followup(generic_q) is True

    generic_q2 = "You demonstrated shows relevant technical knowledge, but reasoning could be made more explicit was not fully addressed. How would you handle that in practice?"
    assert _is_overly_generic_followup(generic_q2) is True

    specific_q = "How would you automatically detect degradation in LLM response quality over time?"
    assert _is_overly_generic_followup(specific_q) is False


def test_malformed_gap_does_not_produce_broken_grammar():
    """Verify malformed/fragment gaps produce clean, grammatically valid fallbacks."""
    bank = StaticQuestionBank()
    state = _create_test_state("Docker")
    state.currentAnswer = "I would run containers."
    eval_obj = EvidenceEvaluation(
        competency="Docker",
        evidenceScore=50,
        technicalScore=50,
        reasoningScore=50,
        completenessScore=50,
        communicationScore=50,
        verified=False,
        followUpRequired=True,
        nextAction="FOLLOW_UP",
        gaps=["reasoning could be made more explicit"],
        strengths=["shows relevant technical knowledge"],
        reason="Needs more explicit reasoning.",
    )
    state.evidenceEvaluations.append(eval_obj)

    followup = bank.followup_for("Docker", state)
    assert "demonstrated shows" not in followup.lower()
    assert "was not fully addressed" not in followup.lower()
    assert "how would you handle that in practice" not in followup.lower()
    assert "reasoning" in followup.lower() or "docker" in followup.lower()


def test_static_fallback_targets_gap():
    """Verify static fallback targets the gap when LLM provider fails."""
    bank = LLMQuestionBank(provider=FailingLLMProvider())
    state = _create_test_state("Security")
    state.currentAnswer = "I use HTTPS."
    eval_obj = EvidenceEvaluation(
        competency="Security",
        evidenceScore=50,
        technicalScore=50,
        reasoningScore=50,
        completenessScore=50,
        communicationScore=50,
        verified=False,
        followUpRequired=True,
        nextAction="FOLLOW_UP",
        gaps=["prompt injection guardrails"],
        strengths=["HTTPS usage"],
    )
    state.evidenceEvaluations.append(eval_obj)

    followup = bank.followup_for("Security", state)
    assert "prompt injection guardrails" in followup.lower() or "security" in followup.lower()
    assert _is_overly_generic_followup(followup) is False


def test_followup_remains_unique():
    """Verify improved follow-up passes duplicate protection."""
    bank = StaticQuestionBank()
    state = _create_test_state("Security")
    state.currentAnswer = "I use basic auth."
    eval_obj = EvidenceEvaluation(
        competency="Security",
        evidenceScore=50,
        technicalScore=50,
        reasoningScore=50,
        completenessScore=50,
        communicationScore=50,
        verified=False,
        followUpRequired=True,
        nextAction="FOLLOW_UP",
        gaps=["prompt injection protection"],
    )
    state.evidenceEvaluations.append(eval_obj)

    q1 = bank.followup_for("Security", state)
    assert q1 != ""
    state.conversationHistory.append(ConversationMessage(role="interviewer", message=q1))

    q2 = bank.followup_for("Security", state)
    assert _normalize_question_text(q1) != _normalize_question_text(q2)


def test_end_to_end_followup_quality():
    """Integration test: process_answer produces a non-empty, technical, gap-related follow-up."""
    from pathlib import Path

    curriculum_path = Path(__file__).resolve().parent.parent.parent / "curriculum.json"
    curriculum_service = CurriculumService(str(curriculum_path))
    session_service = SessionService()

    class CustomCandidateService:
        @staticmethod
        def get_candidate(candidate_id: str):
            class DummyProfile:
                class Member:
                    name = "Test Candidate"
                member = Member()
            return DummyProfile()

        @staticmethod
        def get_candidate_summary(candidate_id: str):
            class DummySummary:
                jobRole = "Engineer"
                yearsExperience = 5
            return DummySummary()

        @staticmethod
        def get_interview_topics(candidate_id: str):
            class Topic:
                def __init__(self, day, title):
                    self.day = day
                    self.title = title
            return [Topic(1, "Docker")]

    director = InterviewDirector(
        candidate_service=CustomCandidateService,
        curriculum_service=curriculum_service,
        question_bank=StaticQuestionBank(),
    )
    evidence_engine = EvidenceEngine(
        curriculum_service=curriculum_service,
        evaluator=MockEvidenceEvaluator(),
    )

    service = InterviewService(
        candidate_service=CustomCandidateService,
        curriculum_service=curriculum_service,
        session_service=session_service,
        director=director,
        evidence_engine=evidence_engine,
    )

    response = service.start_interview("CAND-001")
    turn_response = service.process_answer(response.sessionId, "I use docker run to start containers.")

    assert turn_response.question != ""
    assert turn_response.evidence is not None
    assert turn_response.evidence.followUpRequired is True
    assert _is_overly_generic_followup(turn_response.question) is False
