"""Question bank strategy for the Interview Director.

Defines the abstraction the Interview Director uses to source interview
questions. The static implementation is deterministic; the Gemini-backed
strategy generates fresh questions using structured output and degrades
gracefully to the static bank whenever Gemini is unavailable.
"""

import json
import re
from abc import ABC, abstractmethod

import google.generativeai as genai


class QuestionBank(ABC):
    """Strategy interface for sourcing interview questions."""

    @abstractmethod
    def questions_for(self, competency: str) -> list[str]:
        """Return the scenario questions available for a competency."""

    @abstractmethod
    def followup_for(self, competency: str) -> str:
        """Return a deeper follow-up question for a competency."""


class StaticQuestionBank(QuestionBank):
    """Deterministic question bank used until Gemini is integrated."""

    _QUESTIONS: dict[str, list[str]] = {
        "Embeddings": [
            "What are embeddings and why are they useful?",
            "How would you compare two embedding models?",
            "How would you debug poor retrieval quality?",
        ],
        "Docker": [
            "Explain Docker containers.",
            "Why would a container continuously restart?",
            "How would you deploy a FastAPI application using Docker?",
        ],
        "RAG": [
            "Explain how Retrieval-Augmented Generation works.",
            "How would you build a RAG pipeline for a healthcare chatbot?",
            "How would you measure retrieval quality in production?",
        ],
        "Vector Databases": [
            "How do vector databases index and search high-dimensional embeddings?",
            "When would you prefer a managed vector database over a self-hosted one?",
            "How would you keep a vector index in sync with your source data?",
        ],
        "Multi-Agent Orchestration": [
            "How would you coordinate multiple agents working toward a shared goal?",
            "When would multiple agents provide more value than a single agent?",
            "How would you handle failures in one agent of a multi-agent system?",
        ],
        "Prompt Engineering": [
            "What makes a well-engineered prompt, and how would you iterate on it?",
            "How would you measure whether one prompt is better than another?",
            "How would you design few-shot examples for a healthcare chatbot?",
        ],
        "Function Calling": [
            "How does function calling let an LLM interact with external tools?",
            "How would you validate structured output from a model?",
            "What happens when a model calls a tool with invalid arguments?",
        ],
        "Security": [
            "What security considerations matter when exposing an AI chatbot over an API?",
            "How would you protect a chatbot against prompt injection?",
            "How would you handle PII in conversation history?",
        ],
        "technicalKnowledge": [
            "Walk me through a technical project you are most proud of.",
            "How would you debug a performance regression in production?",
            "How would you design a system for high availability?",
        ],
        "communication": [
            "Explain a complex technical concept to a non-technical stakeholder.",
            "How would you document an API for other engineers?",
            "How would you communicate a technical decision to your manager?",
        ],
        "problemSolving": [
            "Describe a difficult problem you solved and how you approached it.",
            "How would you troubleshoot a system that is intermittently failing?",
            "How would you decide between two viable technical approaches?",
        ],
        "leadership": [
            "Tell me about a time you led a team through a challenging situation.",
            "How do you mentor a junior engineer who is stuck?",
            "How would you handle conflicting priorities across teams?",
        ],
        "learningAbility": [
            "Describe a skill you picked up quickly and how you approached learning it.",
            "How do you stay current with new technologies?",
            "What do you do when a technology you know becomes outdated?",
        ],
    }

    _FOLLOWUPS: dict[str, str] = {
        "Embeddings": "How would you evaluate whether your embedding model produces good representations?",
        "Docker": "How would you handle container orchestration and health checks in production?",
        "RAG": "When would you choose hybrid retrieval over semantic search?",
        "Vector Databases": "When would you prefer a managed vector database over a self-hosted one?",
        "Multi-Agent Orchestration": "When would multiple agents provide more value than a single agent?",
        "Prompt Engineering": "How would you measure whether one prompt is better than another?",
        "Function Calling": "How would you validate structured output from a model?",
        "Security": "How would you protect a chatbot against prompt injection?",
        "technicalKnowledge": "Can you go deeper into how you would implement that in a production system?",
        "communication": "How would you adapt that explanation for a less technical audience?",
        "problemSolving": "What alternatives did you consider, and why did you choose that approach?",
        "leadership": "How did you handle disagreement within your team in that situation?",
        "learningAbility": "What was the hardest part of learning that, and how did you overcome it?",
    }

    _DEFAULT_FOLLOWUP: str = "Can you expand on that and describe how you would apply it in practice?"

    def questions_for(self, competency: str) -> list[str]:
        """Return the scenario questions for a competency, if any."""
        return self._QUESTIONS.get(competency, [])

    def followup_for(self, competency: str) -> str:
        """Return the deeper follow-up question for a competency."""
        return self._FOLLOWUPS.get(competency, self._DEFAULT_FOLLOWUP)


class GeminiQuestionBank(QuestionBank):
    """Gemini-backed question bank with deterministic fallback.

    Generates scenario and follow-up questions using Gemini's structured
    output (``response_mime_type="application/json"`` with a
    ``response_schema``), caching the result per competency so a session
    sees stable questions. When no API key is configured, generation
    fails, or the response cannot be parsed, every method falls back to a
    ``StaticQuestionBank`` so the director never breaks.
    """

    _DEFAULT_MODEL = "gemini-2.0-flash"

    _QUESTIONS_SCHEMA: dict = {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {"type": "string"},
            }
        },
        "required": ["questions"],
    }

    _FOLLOWUP_SCHEMA: dict = {
        "type": "object",
        "properties": {"question": {"type": "string"}},
        "required": ["question"],
    }

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = _DEFAULT_MODEL,
        fallback: QuestionBank | None = None,
    ) -> None:
        """Initialize the bank with a key, model, and fallback strategy.

        The Gemini model is only constructed when ``api_key`` is provided;
        otherwise the bank behaves exactly like its fallback.
        """
        self._fallback = fallback or StaticQuestionBank()
        self._cache: dict[str, list[str]] = {}
        self._followup_cache: dict[str, str] = {}
        self._model = None
        if api_key:
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(
                model_name,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=512,
                    response_mime_type="application/json",
                    response_schema=self._QUESTIONS_SCHEMA,
                ),
            )

    def _generate(self, prompt: str, schema: dict) -> str:
        """Return a raw structured response, or an empty string on failure.

        Any exception during configuration, generation, or parsing results
        in an empty string so callers can fall back to the static bank.
        """
        if self._model is None:
            return ""
        try:
            response = self._model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=512,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            return response.text
        except Exception:
            return ""

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Parse a JSON object from a model response, tolerating fences."""
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?|```$", "", cleaned).strip()
        return json.loads(cleaned)

    def questions_for(self, competency: str) -> list[str]:
        """Return generated scenario questions, cached per competency.

        Falls back to the static bank when generation is unavailable or
        yields no usable questions.
        """
        if competency in self._cache:
            return self._cache[competency]
        questions: list[str] = []
        prompt = (
            f"Generate three interview questions that probe the candidate's "
            f"competency in '{competency}'. Return ONLY a JSON object with a "
            f"'questions' array of strings."
        )
        raw = self._generate(prompt, self._QUESTIONS_SCHEMA)
        if raw:
            try:
                questions = [
                    str(item).strip()
                    for item in self._parse_json(raw).get("questions", [])
                    if str(item).strip()
                ]
            except (ValueError, TypeError, KeyError):
                questions = []
        if not questions:
            questions = self._fallback.questions_for(competency)
        self._cache[competency] = questions
        return questions

    def followup_for(self, competency: str) -> str:
        """Return a generated follow-up question, cached per competency.

        Falls back to the static bank when generation is unavailable or
        yields no usable question.
        """
        if competency in self._followup_cache:
            return self._followup_cache[competency]
        question = ""
        prompt = (
            f"Ask one deeper follow-up question about the candidate's "
            f"competency in '{competency}'. Return ONLY a JSON object with a "
            f"'question' string."
        )
        raw = self._generate(prompt, self._FOLLOWUP_SCHEMA)
        if raw:
            try:
                question = str(self._parse_json(raw).get("question", "")).strip()
            except (ValueError, TypeError, KeyError):
                question = ""
        if not question:
            question = self._fallback.followup_for(competency)
        self._followup_cache[competency] = question
        return question
