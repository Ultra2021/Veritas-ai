"""Question bank strategy for the Interview Director.

Defines the abstraction the Interview Director uses to source interview
questions. The static implementation is deterministic; a Gemini-backed
strategy can replace it in a later module without changing the director.
"""

from abc import ABC, abstractmethod


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
