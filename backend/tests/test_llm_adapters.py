"""Unit tests for the LLM adapters and provider selection (Module 9C).

Covers ``LLMQuestionBank`` and ``LLMEvidenceEvaluator`` fallback behavior
plus the composition-root provider selection. No live LLM APIs are
called.
"""

import json
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.evidence_engine import (
    EvidenceEngine,
    LLMEvidenceEvaluator,
    MockEvidenceEvaluator,
)
from agents.interview_director import InterviewDirector
from agents.question_bank import LLMQuestionBank, StaticQuestionBank
from models.evidence import EvidenceEvaluation
from models.interview_state import ConversationMessage, InterviewState
from services.curriculum_service import CurriculumService
from services.llm_provider import LLMProvider
from services.session_service import SessionService

_CURRICULUM = CurriculumService(
    str(Path(__file__).resolve().parent.parent.parent / "curriculum.json")
)

VALID_EVALUATION = {
    "competency": "technicalKnowledge",
    "evidenceScore": 92,
    "technicalScore": 95,
    "reasoningScore": 90,
    "completenessScore": 90,
    "communicationScore": 88,
    "verified": True,
    "followUpRequired": False,
    "nextAction": "NEXT_COMPETENCY",
    "reason": "Strong technical depth with clear reasoning and examples.",
    "strengths": ["Technical depth", "Clear reasoning"],
    "gaps": [],
}


class _FakeProvider(LLMProvider):
    """Scripted provider that records the context it receives."""

    def __init__(
        self,
        questions: list[str] | None = None,
        followup: str | None = None,
        evaluation: dict | None = None,
    ) -> None:
        self.questions = questions
        self.followup = followup
        self.evaluation = evaluation
        self.question_calls: list[dict] = []
        self.followup_calls: list[dict] = []
        self.evaluation_calls: list[dict] = []

    def questions_for(self, **kwargs):
        self.question_calls.append(kwargs)
        return self.questions

    def followup_for(self, **kwargs):
        self.followup_calls.append(kwargs)
        return self.followup

    def evaluate_answer(self, **kwargs):
        self.evaluation_calls.append(kwargs)
        return self.evaluation


class _RaisingProvider(LLMProvider):
    """Provider whose methods always raise."""

    def questions_for(self, **kwargs):
        raise RuntimeError("boom")

    def followup_for(self, **kwargs):
        raise RuntimeError("boom")

    def evaluate_answer(self, **kwargs):
        raise RuntimeError("boom")


class TestLLMQuestionBank:
    """QuestionBank adapter delegation and fallback."""

    def test_no_provider_falls_back_to_static(self):
        bank = LLMQuestionBank()
        assert bank.questions_for("RAG") == StaticQuestionBank().questions_for("RAG")
        assert bank.followup_for("RAG") == StaticQuestionBank().followup_for("RAG")

    def test_questions_delegated_to_provider(self):
        provider = _FakeProvider(questions=["Q1?", "Q2?"])
        bank = LLMQuestionBank(provider=provider)
        assert bank.questions_for("RAG") == ["Q1?", "Q2?"]
        assert provider.question_calls[0]["competency"] == "RAG"

    def test_followup_delegated_to_provider(self):
        provider = _FakeProvider(followup="Go deeper?")
        bank = LLMQuestionBank(provider=provider)
        assert bank.followup_for("RAG") == "Go deeper?"

    def test_caches_results_per_competency(self):
        provider = _FakeProvider(questions=["Q1?"])
        bank = LLMQuestionBank(provider=provider)
        assert bank.questions_for("RAG") == ["Q1?"]
        assert bank.questions_for("RAG") == ["Q1?"]
        assert len(provider.question_calls) == 1

    def test_fallback_followup_not_permanently_cached(self):
        provider = _FakeProvider(followup=None)
        bank = LLMQuestionBank(provider=provider)
        competency = "Capstone Project & Final Demo"
        state = InterviewState(sessionId=uuid4(), candidateId="CAND-001")

        variants = []
        for _ in range(len(bank._fallback.followups_for(competency))):
            question = bank.followup_for(competency, state)
            assert question, "fallback should keep yielding distinct variants"
            assert question not in variants
            variants.append(question)
            state.conversationHistory.append(
                ConversationMessage(role="interviewer", message=question)
            )

        assert len(set(variants)) == len(variants)
        assert competency not in bank._followup_cache
        assert bank.followup_for(competency, state) == ""

    def test_provider_none_falls_back_to_static(self):
        provider = _FakeProvider(questions=None)
        bank = LLMQuestionBank(provider=provider)
        assert bank.questions_for("RAG") == StaticQuestionBank().questions_for("RAG")
        assert bank.followup_for("RAG") == StaticQuestionBank().followup_for("RAG")

    def test_provider_empty_list_falls_back_to_static(self):
        provider = _FakeProvider(questions=[])
        bank = LLMQuestionBank(provider=provider)
        assert bank.questions_for("RAG") == StaticQuestionBank().questions_for("RAG")

    def test_provider_raising_falls_back_to_static(self):
        bank = LLMQuestionBank(provider=_RaisingProvider())
        assert bank.questions_for("RAG") == StaticQuestionBank().questions_for("RAG")
        assert bank.followup_for("RAG") == StaticQuestionBank().followup_for("RAG")

    def test_curriculum_and_conversation_context_passed(self):
        provider = _FakeProvider(questions=["Q1?"])
        bank = LLMQuestionBank(provider=provider, curriculum_service=_CURRICULUM)
        state = InterviewState(
            sessionId=uuid4(),
            candidateId="CAND-001",
            currentCompetency="Embeddings Explained",
            currentQuestion="What are embeddings?",
            interviewStage="interviewing",
        )
        bank.questions_for("Embeddings Explained", state)
        call = provider.question_calls[0]
        assert "Objectives:" in call["curriculum_context"]
        assert "What are embeddings?" in call["conversation_context"]
        assert "Interview stage: interviewing" in call["conversation_context"]

    def test_state_is_optional(self):
        provider = _FakeProvider(questions=["Q1?"])
        bank = LLMQuestionBank(provider=provider)
        assert bank.questions_for("RAG") == ["Q1?"]
        assert provider.question_calls[0]["conversation_context"] == ""

    def test_respects_custom_fallback(self):
        class _EmptyBank(StaticQuestionBank):
            def questions_for(self, competency, state=None):
                return []

            def followup_for(self, competency, state=None):
                return "Custom fallback?"

        bank = LLMQuestionBank(provider=_FakeProvider(), fallback=_EmptyBank())
        assert bank.questions_for("RAG") == []
        assert bank.followup_for("RAG") == "Custom fallback?"

    def test_dedupes_blank_questions(self):
        provider = _FakeProvider(questions=["  ", "Q1?", ""])
        bank = LLMQuestionBank(provider=provider)
        assert bank.questions_for("RAG") == ["Q1?"]


class TestLLMEvidenceEvaluator:
    """EvidenceEvaluator adapter delegation and fallback."""

    def _engine(self, provider=None):
        return EvidenceEngine(
            curriculum_service=_CURRICULUM,
            evaluator=LLMEvidenceEvaluator(provider=provider),
        )

    def _state(self):
        return InterviewState(
            sessionId=uuid4(),
            candidateId="CAND-001",
            currentCompetency="technicalKnowledge",
            currentQuestion="Walk me through a technical project.",
            currentQuestionId="Q1",
        )

    def test_no_provider_uses_deterministic(self):
        engine = self._engine()
        evaluation = engine.evaluate_answer(self._state(), "I like computers.")
        assert isinstance(evaluation, EvidenceEvaluation)
        assert evaluation.competency == "technicalKnowledge"
        assert evaluation.questionId == "Q1"

    def test_provider_evaluation_valid(self):
        provider = _FakeProvider(evaluation=dict(VALID_EVALUATION))
        engine = self._engine(provider)
        evaluation = engine.evaluate_answer(
            self._state(),
            "I built a vector search system with strong reasoning, for example "
            "because we chose a hybrid architecture, therefore we gained speed.",
        )
        assert isinstance(evaluation, EvidenceEvaluation)
        assert evaluation.evidenceScore == 92
        assert evaluation.verified is True
        assert evaluation.nextAction == "NEXT_COMPETENCY"
        assert evaluation.followUpRequired is False
        assert evaluation.questionId == "Q1"
        assert evaluation.question == "Walk me through a technical project."
        assert provider.evaluation_calls

    def test_provider_none_falls_back_to_deterministic(self):
        provider = _FakeProvider(evaluation=None)
        engine = self._engine(provider)
        state = self._state()
        evaluation = engine.evaluate_answer(state, "I like computers.")
        assert isinstance(evaluation, EvidenceEvaluation)
        assert evaluation.competency == "technicalKnowledge"

    def test_provider_raising_falls_back_to_deterministic(self):
        engine = self._engine(_RaisingProvider())
        state = self._state()
        evaluation = engine.evaluate_answer(state, "I like computers.")
        assert isinstance(evaluation, EvidenceEvaluation)
        expected = MockEvidenceEvaluator().evaluate(
            competency="technicalKnowledge",
            question=state.currentQuestion,
            answer="I like computers.",
            keywords=(),
            previous_evidence=(),
            curriculum_context="",
        )
        expected.questionId = "Q1"
        assert evaluation == expected

    def test_competency_always_from_engine(self):
        spoofed = dict(VALID_EVALUATION, competency="SomeInjectedCompetency")
        engine = self._engine(_FakeProvider(evaluation=spoofed))
        state = self._state()
        evaluation = engine.evaluate_answer(state, "Answer text here.")
        assert evaluation.competency == "technicalKnowledge"

    def test_flags_normalized_from_verified(self):
        incoherent = dict(
            VALID_EVALUATION,
            verified=True,
            followUpRequired=True,
            nextAction="FOLLOW_UP",
        )
        engine = self._engine(_FakeProvider(evaluation=incoherent))
        evaluation = engine.evaluate_answer(self._state(), "A strong answer.")
        assert evaluation.followUpRequired is False
        assert evaluation.nextAction == "NEXT_COMPETENCY"

    def test_invalid_payload_falls_back_to_deterministic(self):
        out_of_range = dict(VALID_EVALUATION, evidenceScore=150)
        engine = self._engine(_FakeProvider(evaluation=out_of_range))
        state = self._state()
        evaluation = engine.evaluate_answer(state, "I like computers.")
        assert isinstance(evaluation, EvidenceEvaluation)
        assert evaluation.competency == "technicalKnowledge"

    def test_context_passed_to_provider(self):
        provider = _FakeProvider(evaluation=dict(VALID_EVALUATION))
        engine = self._engine(provider)
        state = InterviewState(
            sessionId=uuid4(),
            candidateId="CAND-001",
            currentCompetency="Embeddings Explained",
            currentQuestion="What are embeddings and why are they useful?",
            currentQuestionId="Q1",
        )
        engine.evaluate_answer(
            state,
            "I built a vector database, for example because we needed fast search.",
        )
        call = provider.evaluation_calls[0]
        assert call["competency"] == "Embeddings Explained"
        assert call["question"] == "What are embeddings and why are they useful?"
        assert call["answer"]
        assert "Objectives:" in call["curriculum_context"]


class TestProviderSelection:
    """Composition-root selection of the active LLM provider."""

    def _routes(self, monkeypatch, provider, groq_key, gemini_key, model):
        import routes.interview as routes

        monkeypatch.setattr(routes.config, "LLM_PROVIDER", provider)
        monkeypatch.setattr(routes.config, "GROQ_API_KEY", groq_key)
        monkeypatch.setattr(routes.config, "GROQ_MODEL", model)
        monkeypatch.setattr(routes.config, "GEMINI_API_KEY", gemini_key)
        return routes

    def test_groq_provider_selected(self, monkeypatch):
        from services.llm_provider import GroqProvider

        routes = self._routes(
            monkeypatch, "groq", "test-key", None, "openai/gpt-oss-20b"
        )
        provider = routes._build_provider()
        assert isinstance(provider, GroqProvider)
        assert provider._client is not None

    def test_groq_missing_key_still_returns_provider_with_fallback(self, monkeypatch):
        from services.llm_provider import GroqProvider

        routes = self._routes(monkeypatch, "groq", None, None, "openai/gpt-oss-20b")
        provider = routes._build_provider()
        assert isinstance(provider, GroqProvider)
        assert provider._client is None
        assert provider.questions_for(competency="RAG") is None

    def test_gemini_selection_uses_existing_implementation(self, monkeypatch):
        from agents.evidence_engine import GeminiEvidenceEvaluator
        from agents.question_bank import GeminiQuestionBank

        routes = self._routes(
            monkeypatch, "gemini", None, "test-gemini-key", "openai/gpt-oss-20b"
        )
        assert routes._build_provider() is None
        bank = routes._build_question_bank(_CURRICULUM, None)
        evaluator = routes._build_evaluator(None)
        assert isinstance(bank, GeminiQuestionBank)
        assert isinstance(evaluator, GeminiEvidenceEvaluator)

    def test_unknown_provider_falls_back_to_deterministic(self, monkeypatch):
        routes = self._routes(monkeypatch, "nonsense", None, None, "openai/gpt-oss-20b")
        assert routes._build_provider() is None
        assert routes._build_question_bank(_CURRICULUM, None) is None
        assert routes._build_evaluator(None) is None

    def test_service_shares_single_provider(self, monkeypatch):
        from services.llm_provider import GroqProvider

        routes = self._routes(
            monkeypatch, "groq", "test-key", None, "openai/gpt-oss-20b"
        )
        service = routes._build_service(SessionService())
        assert isinstance(service._director._question_bank, LLMQuestionBank)
        assert isinstance(service._evidence_engine._evaluator, LLMEvidenceEvaluator)
        assert (
            service._director._question_bank._provider
            is service._evidence_engine._evaluator._provider
        )
        assert isinstance(
            service._director._question_bank._provider, GroqProvider
        )

    def test_director_accepts_llm_question_bank(self):
        import services.candidate_service as candidate_service

        director = InterviewDirector(
            candidate_service,
            _CURRICULUM,
            question_bank=LLMQuestionBank(provider=_FakeProvider(questions=["Q1?"])),
        )
        state = InterviewState(
            sessionId=uuid4(),
            candidateId="CAND-001",
            competencies=[],
        )
        assert director._question_bank.questions_for("RAG", state) == ["Q1?"]
