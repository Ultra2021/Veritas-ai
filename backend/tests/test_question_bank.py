"""Unit tests for the Gemini-backed QuestionBank (Module 9)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.question_bank import GeminiQuestionBank, StaticQuestionBank
from services.curriculum_service import CurriculumService

API_KEY = "test-api-key"


class _FakeResponse:
    """Minimal stand-in for a Gemini generation response."""

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeModel:
    """Records the last prompt and returns scripted responses."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.prompts: list[str] = []

    def generate_content(self, prompt: str, generation_config=None) -> _FakeResponse:
        self.prompts.append(prompt)
        if not self._responses:
            raise RuntimeError("no scripted response left")
        return _FakeResponse(self._responses.pop(0))


def _bank_with_model(responses: list[str]) -> tuple[GeminiQuestionBank, _FakeModel]:
    model = _FakeModel(responses)
    bank = GeminiQuestionBank(
        api_key=API_KEY,
        fallback=StaticQuestionBank(),
    )
    bank._model = model
    return bank, model


class TestGeminiQuestionBank:
    """Exercises generation, fallback, caching, and parsing behavior."""

    def test_no_api_key_falls_back_to_static(self):
        bank = GeminiQuestionBank()
        assert bank._model is None
        assert bank.questions_for("RAG") == StaticQuestionBank().questions_for("RAG")
        assert bank.followup_for("RAG") == StaticQuestionBank().followup_for("RAG")

    def test_questions_generated_with_structured_output(self):
        bank, model = _bank_with_model(
            [json.dumps({"questions": ["Q1?", "Q2?", "Q3?"]})]
        )
        questions = bank.questions_for("RAG")
        assert questions == ["Q1?", "Q2?", "Q3?"]
        assert "RAG" in model.prompts[0]
        assert "questions" in model.prompts[0]

    def test_followup_generated_with_structured_output(self):
        bank, model = _bank_with_model([json.dumps({"question": "Go deeper?"})])
        assert bank.followup_for("RAG") == "Go deeper?"
        assert "question" in model.prompts[0]

    def test_caches_results_per_competency(self):
        bank, model = _bank_with_model(
            [json.dumps({"questions": ["Q1?"]})]
        )
        first = bank.questions_for("RAG")
        second = bank.questions_for("RAG")
        assert first == second
        assert len(model.prompts) == 1

    def test_falls_back_when_generation_raises(self):
        bank, model = _bank_with_model([])
        assert bank.questions_for("RAG") == StaticQuestionBank().questions_for("RAG")
        assert model.prompts

    def test_falls_back_when_response_is_invalid_json(self):
        bank, _ = _bank_with_model(["this is not json"])
        assert bank.questions_for("RAG") == StaticQuestionBank().questions_for("RAG")

    def test_falls_back_when_schema_is_unexpected(self):
        bank, _ = _bank_with_model([json.dumps({"unexpected": True})])
        assert bank.questions_for("RAG") == StaticQuestionBank().questions_for("RAG")

    def test_parses_json_wrapped_in_code_fence(self):
        payload = json.dumps({"questions": ["Q1?"]})
        bank, _ = _bank_with_model([f"```json\n{payload}\n```"])
        assert bank.questions_for("RAG") == ["Q1?"]

    def test_dedupes_blank_questions(self):
        bank, _ = _bank_with_model(
            [json.dumps({"questions": ["  ", "Q1?", ""]})]
        )
        assert bank.questions_for("RAG") == ["Q1?"]

    def test_respects_custom_fallback(self):
        class _EmptyBank(StaticQuestionBank):
            def questions_for(self, competency: str) -> list[str]:
                return []

            def followup_for(self, competency: str) -> str:
                return "Custom fallback?"

        bank = GeminiQuestionBank(fallback=_EmptyBank())
        assert bank.questions_for("RAG") == []
        assert bank.followup_for("RAG") == "Custom fallback?"

    def test_configure_and_model_created_with_api_key(self, monkeypatch):
        configured: list[str] = []

        def fake_configure(api_key: str) -> None:
            configured.append(api_key)

        def fake_model(*args, **kwargs):
            return _FakeModel([])

        monkeypatch.setattr(
            "agents.question_bank.genai.configure", fake_configure
        )
        monkeypatch.setattr(
            "agents.question_bank.genai.GenerativeModel", fake_model
        )
        bank = GeminiQuestionBank(api_key=API_KEY)
        assert configured == [API_KEY]
        assert bank._model is not None


class TestStaticQuestionBankCurriculum:
    """The static bank must cover every curriculum competency with real,
    non-repeating scenario questions and competency-specific follow-ups."""

    def test_static_capstone_question_exists(self):
        bank = StaticQuestionBank()
        competency = "Capstone Project & Final Demo"
        questions = bank.questions_for(competency)
        assert questions
        assert questions[0] == (
            "Describe how you would design and demonstrate an end-to-end capstone "
            "project, including architecture, implementation, testing, and deployment."
        )
        assert len(set(questions)) == len(questions)

        followups = bank.followups_for(competency)
        assert followups == [
            "Walk me through a concrete technical decision in your capstone and explain the trade-off you would make.",
            "What failure or limitation would you expect in that capstone, and how would you test or mitigate it?",
        ]
        assert bank.followup_for(competency) == followups[0]

    def test_static_bank_covers_all_curriculum_competencies(self):
        bank = StaticQuestionBank()
        curriculum = CurriculumService(
            str(Path(__file__).resolve().parent.parent.parent / "curriculum.json")
        )
        competencies = {topic.title for topic in curriculum.get_topics()}
        assert competencies, "curriculum.json should define topics"
        missing = [
            competency
            for competency in competencies
            if not bank.questions_for(competency)
        ]
        assert missing == []
