"""Question bank strategy for the Interview Director.

Defines the abstraction the Interview Director uses to source interview
questions. The static implementation is deterministic; the Gemini-backed
strategy generates fresh questions using structured output and degrades
gracefully to the static bank whenever Gemini is unavailable.

Deterministic fallbacks are competency-specific and never pin a single
string: ``followup_for`` rotates through the distinct variants available
for a competency, skipping anything already asked in the session, and
returns an empty string when the competency is exhausted so the
Interview Director can move on.
"""

import inspect
import json
import re
from abc import ABC, abstractmethod

import google.generativeai as genai

from models.interview_state import InterviewState
from services.curriculum_service import CurriculumService
from services.llm_provider import LLMProvider


def _method_accepts_state(method) -> bool:
    """Whether a bank method accepts the optional ``state`` argument.

    Custom fallback banks written against the original two-argument
    interface (``competency`` only) must keep working, so calls that
    include the session state are downgraded for them.
    """
    try:
        parameters = inspect.signature(method).parameters
    except (TypeError, ValueError):
        return False
    return any(
        param.kind == inspect.Parameter.VAR_KEYWORD
        or (param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and param.name == "state")
        for param in parameters.values()
    )


def _call_questions_for(fallback, competency: str, state) -> list[str]:
    """Call ``questions_for`` tolerating legacy fallback signatures."""
    if _method_accepts_state(fallback.questions_for):
        return fallback.questions_for(competency, state)
    return fallback.questions_for(competency)


def _call_followup_for(fallback, competency: str, state) -> str:
    """Call ``followup_for`` tolerating legacy fallback signatures."""
    if _method_accepts_state(fallback.followup_for):
        return fallback.followup_for(competency, state)
    return fallback.followup_for(competency)


class QuestionBank(ABC):
    """Strategy interface for sourcing interview questions.

    The optional ``state`` argument lets LLM-backed banks build adaptive
    questions from live interview context; deterministic banks use it to
    avoid repeating questions within a session.
    """

    @abstractmethod
    def questions_for(
        self,
        competency: str,
        state: InterviewState | None = None,
    ) -> list[str]:
        """Return the scenario questions available for a competency."""

    @abstractmethod
    def followup_for(
        self,
        competency: str,
        state: InterviewState | None = None,
    ) -> str:
        """Return a deeper follow-up question for a competency.

        Returns an empty string when every available variant has already
        been asked in ``state`` so callers can exhaust the competency.
        """

    @staticmethod
    def _asked_questions(state: InterviewState | None) -> set[str]:
        """Return the interviewer questions already asked in the session."""
        if state is None:
            return set()
        return {
            message.message
            for message in state.conversationHistory
            if message.role == "interviewer"
        }

    def followups_for(
        self,
        competency: str,
        state: InterviewState | None = None,
    ) -> list[str]:
        """Return the distinct follow-up variants available for a competency."""
        return [self.followup_for(competency, state)]


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
        "VS Code & Python Environment Setup": [
            "How would you set up a reproducible Python development environment for a new team member?",
            "What would you automate in your local development setup, and why?",
            "How would you diagnose environment or dependency conflicts in a Python project?",
        ],
        "Local LLM & AI Coding Assistant Setup": [
            "How would you set up a local LLM for development, and what factors would you consider?",
            "When would you prefer a local model over a hosted API for an AI coding assistant?",
            "How would you evaluate whether a local LLM is fast enough for interactive use?",
        ],
        "First AI Project, React Frontend & GitHub": [
            "How would you structure a first AI project with a React frontend?",
            "What would you include in the GitHub workflow for an AI project?",
            "How would you handle secrets and environment variables across frontend and backend?",
        ],
        "Reading & Processing Structured Data": [
            "How would you load and validate structured data from an external source?",
            "How would you handle malformed or missing fields in structured data?",
            "How would you design a pipeline to process structured data at scale?",
        ],
        "Reading & Processing Unstructured Data": [
            "How would you extract useful text from unstructured documents like PDFs?",
            "What challenges arise when processing unstructured data, and how would you handle them?",
            "How would you clean and normalize unstructured text for downstream use?",
        ],
        "Building the Knowledge Base": [
            "How would you design a knowledge base schema for a domain like healthcare?",
            "How would you keep a knowledge base consistent with changing source documents?",
            "How would you organize content so retrieval is accurate and fast?",
        ],
        "Embeddings Explained": [
            "How would you explain embeddings and why they are useful to a colleague?",
            "How would you choose and evaluate an embedding model for your data?",
            "How would you debug poor retrieval caused by weak embeddings?",
        ],
        "Vector Databases Overview": [
            "What would you consider when selecting a vector database for production?",
            "How do indexing and distance metrics affect retrieval quality and speed?",
            "When would you prefer a managed vector database over self-hosting one?",
        ],
        "Building & Populating the Vector Database": [
            "How would you design the ingestion pipeline that populates a vector database?",
            "How would you handle embeddings that are added, updated, or deleted?",
            "How would you ensure the vector index stays consistent with the source of truth?",
        ],
        "The Retrieval & Matching Engine": [
            "How would you design a retrieval engine that returns relevant results quickly?",
            "How would you combine semantic search with keyword or hybrid retrieval?",
            "How would you evaluate and tune retrieval quality against user queries?",
        ],
        "RAG End-to-End & LLM API Basics": [
            "How would you build an end-to-end RAG pipeline for a domain chatbot?",
            "How would you pass retrieved context to an LLM without exceeding limits?",
            "How would you measure whether RAG is actually improving answers?",
        ],
        "Prompt Engineering Fundamentals": [
            "What makes a well-engineered prompt, and how would you iterate on it?",
            "How would you measure whether one prompt is better than another?",
            "How would you design system and user prompts for a healthcare chatbot?",
        ],
        "Advanced Prompting: Function Calling & Structured Outputs": [
            "How does function calling let an LLM interact with external tools?",
            "How would you validate structured output from a model against a schema?",
            "What happens when a model calls a tool with invalid arguments, and how would you handle it?",
        ],
        "Fine-Tuning: Concepts & When to Use It": [
            "When would you choose fine-tuning over prompt engineering, and why?",
            "What data would you need to fine-tune a model responsibly?",
            "How would you evaluate a fine-tuned model against the base model?",
        ],
        "Fine-Tuning: Hands-On with LoRA & QLoRA": [
            "How would you fine-tune a model with LoRA, and what resources would it require?",
            "What hyperparameters matter most when fine-tuning, and how would you tune them?",
            "How would you detect overfitting during fine-tuning?",
        ],
        "Chatbot Backend & API Integration": [
            "How would you design the backend API for a chatbot?",
            "How would you handle authentication and rate limiting on chatbot endpoints?",
            "How would you structure the integration between the chatbot and an LLM provider?",
        ],
        "Chatbot Frontend Development": [
            "How would you build a responsive chat interface?",
            "How would you manage chat state and message history in the frontend?",
            "How would you handle errors and loading states in a chat UI?",
        ],
        "Full-Stack Integration & Streaming Responses": [
            "How would you integrate a streaming response end-to-end?",
            "How would you handle partial tokens arriving over the wire?",
            "How would you keep the UI responsive while streaming long answers?",
        ],
        "Response Formatting & Rich Outputs": [
            "How would you format model output for rich rendering like markdown or tables?",
            "How would you sanitize model output before rendering it to users?",
            "How would you handle formatting when the model returns malformed content?",
        ],
        "Conversation Memory & Context Management": [
            "How would you manage conversation history for a multi-turn chatbot?",
            "How would you summarize or truncate context when it grows too large?",
            "How would you persist memory across sessions for a user?",
        ],
        "Agentic Frameworks: LangChain Agents & Tool Use": [
            "How would you build an agent that uses tools through a framework like LangChain?",
            "How would you design the loop where an agent decides which tool to call?",
            "How would you prevent an agent from misusing a tool or going off-track?",
        ],
        "Model Context Protocol (MCP)": [
            "What is the Model Context Protocol, and what problem does it solve?",
            "How would you expose your chatbot's tools through MCP?",
            "How would you secure an MCP server that clients connect to?",
        ],
        "Agentic Chatbot Integration": [
            "How would you integrate agentic behavior into an existing chatbot?",
            "How would you let users opt into agentic features safely?",
            "How would you evaluate whether an agentic chatbot is actually helping users?",
        ],
        "Chatbot Evaluation & Testing": [
            "How would you evaluate chatbot answer quality systematically?",
            "How would you build an evaluation set of representative questions?",
            "How would you test edge cases like toxic input or PII in prompts?",
        ],
        "Performance Optimization & Cost Management": [
            "How would you reduce latency and cost of an LLM application?",
            "How would you decide between caching, smaller models, and better prompts?",
            "How would you track token usage and set budgets?",
        ],
        "Security, Privacy & Guardrails": [
            "What security considerations matter when exposing an AI chatbot over an API?",
            "How would you protect a chatbot against prompt injection?",
            "How would you handle PII and sensitive data in conversation history?",
        ],
        "Docker & Kubernetes Deployment": [
            "How would you containerize a chatbot application with Docker?",
            "How would you deploy and scale the application on Kubernetes?",
            "Why would a container restart unexpectedly, and how would you debug it?",
        ],
        "Monitoring, Logging & Observability": [
            "What metrics would you monitor for a production chatbot?",
            "How would you implement logging and tracing across an LLM pipeline?",
            "How would you alert on quality or latency degradation?",
        ],
        "Production Readiness & Final Testing": [
            "How would you prepare an AI application for production?",
            "How would you test for load, failure, and security before release?",
            "How would you plan a safe rollout of a new model or feature?",
        ],
        "Capstone Project & Final Demo": [
            "Describe how you would design and demonstrate an end-to-end capstone project, including architecture, implementation, testing, and deployment.",
            "How would you scope a capstone so it is achievable yet impressive?",
            "How would you present the capstone to stakeholders and handle questions?",
        ],
    }

    _FOLLOWUPS: dict[str, list[str]] = {
        "Embeddings": [
            "How would you evaluate whether your embedding model produces good representations?",
            "When would you choose a different embedding model or dimension, and why?",
        ],
        "Docker": [
            "How would you handle container orchestration and health checks in production?",
            "What would you include in a Docker image to make a container easy to debug?",
        ],
        "RAG": [
            "When would you choose hybrid retrieval over semantic search?",
            "How would you improve retrieval when the top results miss the intended answer?",
        ],
        "Vector Databases": [
            "When would you prefer a managed vector database over a self-hosted one?",
            "How would you migrate a vector database without downtime?",
        ],
        "Multi-Agent Orchestration": [
            "When would multiple agents provide more value than a single agent?",
            "How would you decide the responsibilities and boundaries between agents?",
        ],
        "Prompt Engineering": [
            "How would you measure whether one prompt is better than another?",
            "How would you iterate when a prompt works for some inputs but not others?",
        ],
        "Function Calling": [
            "How would you validate structured output from a model?",
            "How would you handle a model that invokes a tool with hallucinated arguments?",
        ],
        "Security": [
            "How would you protect a chatbot against prompt injection?",
            "How would you respond to a discovered vulnerability in the LLM integration?",
        ],
        "technicalKnowledge": [
            "Can you go deeper into how you would implement that in a production system?",
            "What trade-offs did you weigh, and how would you decide differently next time?",
        ],
        "communication": [
            "How would you adapt that explanation for a less technical audience?",
            "How would you know whether your audience actually understood the explanation?",
        ],
        "problemSolving": [
            "What alternatives did you consider, and why did you choose that approach?",
            "How would you verify your solution actually fixed the root cause?",
        ],
        "leadership": [
            "How did you handle disagreement within your team in that situation?",
            "How would you measure the impact of your leadership in that scenario?",
        ],
        "learningAbility": [
            "What was the hardest part of learning that, and how did you overcome it?",
            "How would you teach that same skill to someone else?",
        ],
        "VS Code & Python Environment Setup": [
            "Walk me through how you would configure a new developer's environment to match the team's tooling.",
            "What tools would you standardize on for Python environments, and what trade-offs do they have?",
        ],
        "Local LLM & AI Coding Assistant Setup": [
            "What hardware or resource constraints would you plan for when running a local LLM?",
            "How would you compare a local and a hosted assistant on latency, cost, and privacy?",
        ],
        "First AI Project, React Frontend & GitHub": [
            "Walk me through how you would version and review a pull request for an AI feature.",
            "What would you put in the README so a new contributor could run the project?",
        ],
        "Reading & Processing Structured Data": [
            "What validation rules would you apply before storing structured data?",
            "How would you handle schema changes in a data source you consume?",
        ],
        "Reading & Processing Unstructured Data": [
            "How would you detect and handle duplicate or near-duplicate content across documents?",
            "What would you do when document text extraction produces garbled output?",
        ],
        "Building the Knowledge Base": [
            "How would you decide what belongs in the knowledge base versus the raw corpus?",
            "How would you evaluate whether the knowledge base covers the questions users ask?",
        ],
        "Embeddings Explained": [
            "How would you measure whether one embedding model captures semantics better than another?",
            "When would you embed text at different granularities, and why?",
        ],
        "Vector Databases Overview": [
            "How would you benchmark candidate vector databases against your workload?",
            "What happens to retrieval quality when your vector index grows, and how would you handle it?",
        ],
        "Building & Populating the Vector Database": [
            "How would you re-embed existing documents when you change embedding models?",
            "How would you backfill a large corpus without disrupting serving?",
        ],
        "The Retrieval & Matching Engine": [
            "How would you diagnose queries that return irrelevant results?",
            "How would you test retrieval at scale for latency and accuracy?",
        ],
        "RAG End-to-End & LLM API Basics": [
            "How would you handle the case where retrieved context is irrelevant or conflicting?",
            "What would you do when an LLM API call fails mid-request?",
        ],
        "Prompt Engineering Fundamentals": [
            "How would you evaluate a prompt change to confirm it improved output quality?",
            "How would you structure a prompt to keep it robust across model versions?",
        ],
        "Advanced Prompting: Function Calling & Structured Outputs": [
            "How would you handle a model that invokes a tool with hallucinated arguments?",
            "How would you design the schema so the model reliably returns structured data?",
        ],
        "Fine-Tuning: Concepts & When to Use It": [
            "How would you prevent fine-tuning from degrading general capabilities?",
            "What risks would you consider before fine-tuning on sensitive data?",
        ],
        "Fine-Tuning: Hands-On with LoRA & QLoRA": [
            "Walk me through a training run and how you would monitor loss and evaluation metrics.",
            "How would you choose the rank and target modules for a LoRA adapter?",
        ],
        "Chatbot Backend & API Integration": [
            "How would you version and evolve the chatbot API without breaking clients?",
            "How would you handle long-running or streaming requests from the backend?",
        ],
        "Chatbot Frontend Development": [
            "How would you optimize the frontend when messages grow large?",
            "How would you make the chat UI accessible to a broad set of users?",
        ],
        "Full-Stack Integration & Streaming Responses": [
            "How would you reconnect or resume a stream that drops mid-response?",
            "How would you test streaming behavior across browsers and network conditions?",
        ],
        "Response Formatting & Rich Outputs": [
            "How would you render structured output such as code blocks reliably?",
            "What would you do when model output breaks the frontend layout?",
        ],
        "Conversation Memory & Context Management": [
            "How would you decide what to keep in memory versus what to discard?",
            "How would you handle sensitive information that should not persist in memory?",
        ],
        "Agentic Frameworks: LangChain Agents & Tool Use": [
            "How would you bound the number of steps an agent can take?",
            "How would you trace and debug a multi-step agent decision?",
        ],
        "Model Context Protocol (MCP)": [
            "How would you handle version compatibility between MCP clients and servers?",
            "How would you test that an MCP tool returns correctly structured results?",
        ],
        "Agentic Chatbot Integration": [
            "How would you fall back to a simpler mode when an agent fails?",
            "How would you surface agent actions to the user for transparency?",
        ],
        "Chatbot Evaluation & Testing": [
            "How would you measure whether a model or prompt change improves answers?",
            "How would you monitor answer quality in production over time?",
        ],
        "Performance Optimization & Cost Management": [
            "How would you profile where latency and cost actually go in the stack?",
            "How would you optimize while preserving answer quality?",
        ],
        "Security, Privacy & Guardrails": [
            "How would you design guardrails that block harmful output without blocking useful answers?",
            "How would you respond to a discovered vulnerability in the LLM integration?",
        ],
        "Docker & Kubernetes Deployment": [
            "How would you manage configuration and secrets across deployment environments?",
            "How would you roll out a new model version without downtime?",
        ],
        "Monitoring, Logging & Observability": [
            "How would you correlate a poor answer with the logs to find the root cause?",
            "What dashboards would you build for the interview pipeline, and why?",
        ],
        "Production Readiness & Final Testing": [
            "What would your pre-release checklist include, and how would you enforce it?",
            "How would you define rollback criteria for a bad release?",
        ],
        "Capstone Project & Final Demo": [
            "Walk me through a concrete technical decision in your capstone and explain the trade-off you would make.",
            "What failure or limitation would you expect in that capstone, and how would you test or mitigate it?",
        ],
    }

    _DEFAULT_FOLLOWUPS: tuple[str, ...] = (
        "Can you expand on that and describe how you would apply it in practice?",
        "Walk me through a specific example where you applied that in practice.",
        "What trade-offs would you weigh before applying that approach?",
    )

    def questions_for(
        self,
        competency: str,
        state: InterviewState | None = None,
    ) -> list[str]:
        """Return the scenario questions for a competency, if any."""
        return self._QUESTIONS.get(competency, [])

    def followup_for(
        self,
        competency: str,
        state: InterviewState | None = None,
    ) -> str:
        """Return the next unasked follow-up question for a competency.

        Returns an empty string when every variant has already been
        asked so the caller can exhaust the competency.
        """
        asked = self._asked_questions(state)
        candidates = self._FOLLOWUPS.get(competency, list(self._DEFAULT_FOLLOWUPS))
        for candidate in candidates:
            if candidate not in asked:
                return candidate
        return ""

    def followups_for(
        self,
        competency: str,
        state: InterviewState | None = None,
    ) -> list[str]:
        """Return all distinct follow-up variants for a competency."""
        return self._FOLLOWUPS.get(competency, list(self._DEFAULT_FOLLOWUPS))


class GeminiQuestionBank(QuestionBank):
    """Gemini-backed question bank with deterministic fallback.

    Generates scenario and follow-up questions using Gemini's structured
    output (``response_mime_type="application/json"`` with a
    ``response_schema``), caching only successful LLM-generated results
    per competency. When no API key is configured, generation fails, or
    the response cannot be parsed, every method falls back to a
    ``StaticQuestionBank``; a fallback result is never cached, so a
    transient failure cannot pin a single question for the session.
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

    def questions_for(
        self,
        competency: str,
        state: InterviewState | None = None,
    ) -> list[str]:
        """Return generated scenario questions, cached per competency.

        Only successfully generated questions are cached. Falls back to
        the static bank when generation is unavailable or yields no
        usable questions without caching the fallback.
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
            return _call_questions_for(self._fallback, competency, state)
        self._cache[competency] = questions
        return questions

    def followup_for(
        self,
        competency: str,
        state: InterviewState | None = None,
    ) -> str:
        """Return a generated follow-up question that has not been asked.

        A cached LLM result is reused while unique; once it has been
        asked, a fresh one is generated. Fallback results are returned
        for the current turn but never cached. Returns an empty string
        when no unique question is available.
        """
        asked = self._asked_questions(state)
        if (
            competency in self._followup_cache
            and self._followup_cache[competency] not in asked
        ):
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
        if question and question not in asked:
            self._followup_cache[competency] = question
            return question
        return self._next_static_followup(competency, state, asked)

    def _next_static_followup(
        self,
        competency: str,
        state: InterviewState | None,
        asked: set[str],
    ) -> str:
        """Return the first unasked static follow-up variant, if any."""
        fallback = _call_followup_for(self._fallback, competency, state)
        if fallback and fallback not in asked:
            return fallback
        for candidate in self._fallback.followups_for(competency, state):
            if candidate and candidate not in asked:
                return candidate
        return ""


class LLMQuestionBank(QuestionBank):
    """LLM-backed question bank with deterministic fallback.

    Delegates scenario and follow-up question generation to an
    ``LLMProvider``, enriching the request with curriculum context and
    live interview context (recent conversation, open competencies, and
    stage) when a session state is available. Only successful LLM
    results are cached; deterministic fallbacks are used for the current
    turn and never cached, so a provider failure cannot pin a single
    question for the session.
    """

    def __init__(
        self,
        provider: LLMProvider | None = None,
        fallback: QuestionBank | None = None,
        curriculum_service: CurriculumService | None = None,
    ) -> None:
        """Initialize the bank with a provider, fallback, and curriculum."""
        self._provider = provider
        self._fallback = fallback or StaticQuestionBank()
        self._curriculum_service = curriculum_service
        self._cache: dict[str, list[str]] = {}
        self._followup_cache: dict[str, str] = {}

    def _curriculum_context(self, competency: str) -> str:
        """Return a human-readable curriculum context for a competency."""
        if self._curriculum_service is None:
            return ""
        for topic in self._curriculum_service.get_topics():
            if topic.title.lower() == competency.lower():
                day = self._curriculum_service.get_day(topic.day)
                lines = [f"Title: {day.title}"]
                if day.tools:
                    lines.append("Tools: " + ", ".join(day.tools))
                lines.append("Objectives:")
                lines.extend(f"- {objective}" for objective in day.objectives)
                return "\n".join(lines)
        return ""

    def _conversation_context(self, state: InterviewState | None) -> str:
        """Return recent conversation and evidence context for the prompt."""
        if state is None:
            return ""
        lines = ["Recent conversation:"]
        for message in state.conversationHistory[-6:]:
            lines.append(f"{message.role}: {message.message}")
        if not state.conversationHistory and state.currentQuestion:
            lines.append(f"interviewer: {state.currentQuestion}")
        gaps = [
            f"- {entry.competency} (status={entry.status}, "
            f"evidence={entry.evidenceScore}/100)"
            for entry in state.competencies
            if entry.status != "verified"
        ]
        if gaps:
            lines.append("Open competencies / evidence gaps:")
            lines.extend(gaps)
        lines.append(f"Interview stage: {state.interviewStage}")
        return "\n".join(lines)

    def questions_for(
        self,
        competency: str,
        state: InterviewState | None = None,
    ) -> list[str]:
        """Return generated scenario questions, cached per competency.

        Only successfully generated questions are cached. Falls back to
        the static bank when the provider is unavailable or yields no
        usable questions without caching the fallback.
        """
        if competency in self._cache:
            return self._cache[competency]
        questions: list[str] = []
        if self._provider is not None:
            try:
                generated = self._provider.questions_for(
                    competency=competency,
                    curriculum_context=self._curriculum_context(competency),
                    conversation_context=self._conversation_context(state),
                )
            except Exception:
                generated = None
            if generated:
                questions = [
                    str(item).strip() for item in generated if str(item).strip()
                ]
        if not questions:
            return _call_questions_for(self._fallback, competency, state)
        self._cache[competency] = questions
        return questions

    def followup_for(
        self,
        competency: str,
        state: InterviewState | None = None,
    ) -> str:
        """Return a generated follow-up question that has not been asked.

        A cached LLM result is reused while unique; once it has been
        asked, a fresh one is generated. Fallback results are returned
        for the current turn but never cached. Returns an empty string
        when no unique question is available.
        """
        asked = self._asked_questions(state)
        if (
            competency in self._followup_cache
            and self._followup_cache[competency] not in asked
        ):
            return self._followup_cache[competency]
        question = ""
        if self._provider is not None:
            try:
                generated = self._provider.followup_for(
                    competency=competency,
                    curriculum_context=self._curriculum_context(competency),
                    conversation_context=self._conversation_context(state),
                )
            except Exception:
                generated = None
            if generated:
                question = str(generated).strip()
        if question and question not in asked:
            self._followup_cache[competency] = question
            return question
        return self._next_static_followup(competency, state, asked)

    def _next_static_followup(
        self,
        competency: str,
        state: InterviewState | None,
        asked: set[str],
    ) -> str:
        """Return the first unasked static follow-up variant, if any."""
        fallback = _call_followup_for(self._fallback, competency, state)
        if fallback and fallback not in asked:
            return fallback
        for candidate in self._fallback.followups_for(competency, state):
            if candidate and candidate not in asked:
                return candidate
        return ""
