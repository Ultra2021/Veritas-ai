"""Agent 2: the Evidence Engine.

Evaluates candidate answers, tracks evidence for competencies, updates
competency state, interview DNA, and hiring confidence, and tells the
Interview Director what to do next. Evaluation is deterministic (mock)
until Gemini is integrated.

The Evidence Engine may update competency evidence/status, interview
DNA, and hiring confidence. It never generates questions, never talks to
the candidate, and never makes hire/reject decisions.
"""

import re
from abc import ABC, abstractmethod
from collections.abc import Sequence

from models.evidence import EvidenceEvaluation, NextAction
from models.interview_state import CompetencyState, InterviewDNA, InterviewState
from services.curriculum_service import CurriculumService

_VERIFICATION_THRESHOLD = 80

_STOPWORDS: frozenset[str] = frozenset(
    {
        "the", "a", "an", "and", "or", "for", "to", "of", "in", "on",
        "with", "that", "this", "is", "are", "was", "were", "be", "it",
        "as", "at", "by", "you", "your", "what", "how", "why", "when",
        "which", "would", "should", "could", "do", "does", "did",
        "describe", "explain", "tell", "me", "about", "walk", "through",
        "most", "over", "into", "them", "they", "their", "will", "can",
        "have", "has", "had", "not", "from", "than", "then", "after",
        "before", "using", "used", "use",
    }
)


class EvidenceEvaluator(ABC):
    """Strategy interface for evaluating candidate answers.

    The mock implementation uses deterministic keyword rules; a
    Gemini-backed implementation will replace it in a later module.
    """

    @abstractmethod
    def evaluate(
        self,
        *,
        competency: str,
        question: str,
        answer: str,
        keywords: Sequence[str] = (),
    ) -> EvidenceEvaluation:
        """Evaluate an answer and return an ``EvidenceEvaluation``."""


class MockEvidenceEvaluator(EvidenceEvaluator):
    """Deterministic rule-based evaluator.

    This is NOT a real AI evaluation system. It applies lightweight
    heuristics so the platform can be exercised end-to-end until Gemini
    is integrated:

    - empty or very short answers yield low evidence
    - competency keyword matches raise the technical score
    - reasoning indicators (``because``, ``therefore``, ...) raise reasoning
    - longer, example-rich answers raise completeness
    - answer/question term overlap raises the evidence score
    """

    _KEYWORDS: dict[str, tuple[str, ...]] = {
        "Embeddings": ("embedding", "vector", "token", "semantic", "dimension", "cosine"),
        "Docker": ("container", "image", "docker", "vm", "virtual", "layer", "runtime", "port"),
        "RAG": ("retriev", "rag", "generation", "context", "augment", "search", "chunk"),
        "Vector Databases": ("vector", "index", "chroma", "pinecone", "search", "metric", "hnsw"),
        "Multi-Agent Orchestration": ("agent", "orchestrat", "router", "delegate", "coordinat", "workflow"),
        "Prompt Engineering": ("prompt", "few-shot", "zero-shot", "template", "system", "output"),
        "Function Calling": ("function", "tool", "schema", "structured", "call", "parameter"),
        "Security": ("security", "auth", "injection", "privacy", "guardrail", "pii", "sanitiz", "encrypt"),
        "technicalKnowledge": (
            "system", "design", "api", "database", "architecture",
            "production", "scal", "cache",
        ),
        "communication": ("explain", "document", "stakeholder", "audience", "clear", "communicat", "report"),
        "problemSolving": ("problem", "solve", "debug", "root", "troubleshoot", "approach", "analyz", "test"),
        "leadership": ("lead", "team", "mentor", "guide", "direction", "conflict", "prioritiz"),
        "learningAbility": ("learn", "study", "skill", "adapt", "practice", "course", "new"),
    }

    _REASONING_INDICATORS: tuple[str, ...] = (
        "because",
        "therefore",
        "for example",
        "trade-off",
        "since",
        "thus",
        "hence",
        "consequently",
        "as a result",
        "however",
        "although",
    )

    def _significant_terms(self, text: str) -> set[str]:
        """Return the meaningful lowercase terms of a text."""
        return {
            term
            for term in re.findall(r"[a-z']+", text.lower())
            if term not in _STOPWORDS and len(term) > 3
        }

    def _directness(self, answer: str, question: str) -> int:
        """How directly the answer addresses the question (0-100)."""
        question_terms = self._significant_terms(question)
        if not question_terms:
            return 50
        matches = len(question_terms & self._significant_terms(answer))
        return round(matches / len(question_terms) * 100)

    def _keyword_hits(self, answer: str, keywords: Sequence[str]) -> int:
        """Count how many competency keywords appear in the answer."""
        lowered = answer.lower()
        return sum(1 for keyword in keywords if keyword in lowered)

    def _reasoning_hits(self, answer: str) -> int:
        """Count reasoning indicators in the answer."""
        lowered = answer.lower()
        return sum(lowered.count(indicator) for indicator in self._REASONING_INDICATORS)

    def _completeness(self, words: int, answer: str) -> int:
        """Score answer completeness from length and explanation markers."""
        if words >= 60:
            score = 100
        elif words >= 40:
            score = 80
        elif words >= 20:
            score = 60
        elif words >= 8:
            score = 40
        else:
            score = 20
        if re.search(r"\d", answer):
            score = min(100, score + 10)
        if "for example" in answer.lower():
            score = min(100, score + 10)
        return score

    def _communication(self, words: int, answer: str) -> int:
        """Score communication from length and sentence structure."""
        sentences = [part for part in re.split(r"[.!?]+", answer) if part.strip()]
        return min(100, words * 3 + (10 if len(sentences) >= 2 else 0))

    def evaluate(
        self,
        *,
        competency: str,
        question: str,
        answer: str,
        keywords: Sequence[str] = (),
    ) -> EvidenceEvaluation:
        """Evaluate an answer using deterministic heuristics."""
        text = (answer or "").strip()
        words = len(text.split())
        all_keywords = (*self._KEYWORDS.get(competency, ()), *keywords)

        if not text:
            return EvidenceEvaluation(
                competency=competency,
                evidenceScore=0,
                technicalScore=0,
                reasoningScore=0,
                completenessScore=0,
                communicationScore=0,
                verified=False,
                followUpRequired=True,
                nextAction="FOLLOW_UP",
                reason="No answer provided.",
                strengths=[],
                gaps=["No substantive answer given."],
                question=question,
            )

        technical = min(100, self._keyword_hits(text, all_keywords) * 25)
        reasoning = min(100, self._reasoning_hits(text) * 20)
        completeness = self._completeness(words, text)
        communication = self._communication(words, text)
        directness = self._directness(text, question)

        evidence = round(
            0.25 * technical
            + 0.25 * reasoning
            + 0.25 * completeness
            + 0.15 * communication
            + 0.10 * directness
        )

        verified = evidence >= _VERIFICATION_THRESHOLD
        next_action: NextAction = "NEXT_COMPETENCY" if verified else "FOLLOW_UP"

        strengths: list[str] = []
        if technical >= 60:
            strengths.append("Shows relevant technical knowledge.")
        if reasoning >= 60:
            strengths.append("Reasoning is explicit and well structured.")
        if completeness >= 60:
            strengths.append("Provides a complete, well-developed answer.")
        if not strengths:
            strengths.append("Answer was given but evidence is limited.")

        gaps: list[str] = []
        if technical < 60:
            gaps.append(f"Lacks specific technical depth on {competency}.")
        if reasoning < 60:
            gaps.append("Reasoning could be made more explicit.")
        if completeness < 60:
            gaps.append("Answer would benefit from more explanation or examples.")
        if not verified:
            gaps.append("Evidence for this competency is not yet sufficient.")

        return EvidenceEvaluation(
            competency=competency,
            evidenceScore=evidence,
            technicalScore=technical,
            reasoningScore=reasoning,
            completenessScore=completeness,
            communicationScore=communication,
            verified=verified,
            followUpRequired=not verified,
            nextAction=next_action,
            reason=(
                f"Evidence score {evidence}/100 from keyword relevance, "
                "reasoning indicators, and answer completeness."
            ),
            strengths=strengths,
            gaps=gaps,
            question=question,
        )


class EvidenceEngine:
    """Evaluates candidate answers and updates interview state."""

    def __init__(
        self,
        evaluator: EvidenceEvaluator | None = None,
        curriculum_service: CurriculumService | None = None,
    ) -> None:
        """Initialize the engine with an evaluator strategy.

        ``evaluator`` defaults to ``MockEvidenceEvaluator`` and may be
        swapped for a Gemini-backed strategy later. ``curriculum_service``
        optionally enriches evaluation with curriculum context.
        """
        self._evaluator: EvidenceEvaluator = evaluator or MockEvidenceEvaluator()
        self._curriculum_service = curriculum_service

    def evaluate_answer(self, state: InterviewState, answer: str) -> EvidenceEvaluation:
        """Evaluate the candidate's latest answer.

        Evaluates against the current competency and question, attaching
        ``currentQuestionId``/``currentQuestion`` for traceability. The
        mock evaluator uses deterministic heuristics; the candidate
        profile and richer conversation context will be used by the
        Gemini-backed evaluator later.
        """
        competency = state.currentCompetency or ""
        question = state.currentQuestion or ""
        keywords = self._curriculum_keywords(competency)
        evaluation = self._evaluator.evaluate(
            competency=competency,
            question=question,
            answer=answer,
            keywords=keywords,
        )
        evaluation.questionId = state.currentQuestionId
        evaluation.question = question
        return evaluation

    def _curriculum_keywords(self, competency: str) -> list[str]:
        """Return objective keywords when the competency matches a topic."""
        if self._curriculum_service is None:
            return []
        for topic in self._curriculum_service.get_topics():
            if topic.title.lower() == competency.lower():
                day = self._curriculum_service.get_day(topic.day)
                terms: set[str] = set()
                for objective in day.objectives:
                    for term in re.findall(r"[a-z']+", objective.lower()):
                        if len(term) > 4 and term not in _STOPWORDS:
                            terms.add(term)
                return sorted(terms)
        return []

    def update_competency(
        self,
        state: InterviewState,
        evaluation: EvidenceEvaluation,
    ) -> CompetencyState:
        """Update or create the competency ledger entry for an evaluation.

        Existing entries are updated in place (no duplicates); new
        competencies are appended. The evaluation is also recorded in
        ``state.evidenceEvaluations`` for Interview Replay.
        """
        entry = next(
            (
                competency_state
                for competency_state in state.competencies
                if competency_state.competency == evaluation.competency
            ),
            None,
        )
        if entry is None:
            entry = CompetencyState(competency=evaluation.competency)
            state.competencies.append(entry)

        entry.evidenceScore = evaluation.evidenceScore
        entry.attempts += 1
        entry.status = "verified" if evaluation.verified else "needs_followup"
        entry.notes = evaluation.reason
        state.evidenceEvaluations.append(evaluation)
        return entry

    def calculate_hiring_confidence(self, state: InterviewState) -> int:
        """Return the interview evidence-confidence metric (0-100).

        Average of all evaluated competency evidence scores. This is NOT
        a hiring decision, and it never uses personal or demographic
        information.
        """
        scores = [
            competency_state.evidenceScore
            for competency_state in state.competencies
            if competency_state.attempts > 0
        ]
        confidence = round(sum(scores) / len(scores)) if scores else 0
        state.hiringConfidence = confidence
        return confidence

    def update_interview_dna(
        self,
        state: InterviewState,
        evaluation: EvidenceEvaluation,
    ) -> InterviewDNA:
        """Update interview DNA from evaluation scores.

        Maps ``technicalScore`` -> ``technicalKnowledge``,
        ``communicationScore`` -> ``communication``, and
        ``reasoningScore`` -> ``problemSolving``. ``leadership`` and
        ``learningAbility`` are preserved because the mock evaluator
        cannot reasonably assess them.
        """
        dna = state.interviewDNA
        dna.technicalKnowledge = evaluation.technicalScore
        dna.communication = evaluation.communicationScore
        dna.problemSolving = evaluation.reasoningScore
        return dna

    def needs_followup(self, evaluation: EvidenceEvaluation) -> bool:
        """Return whether the interviewer should ask a follow-up question."""
        return evaluation.followUpRequired

    def get_next_action(self, evaluation: EvidenceEvaluation) -> NextAction:
        """Return the action the Interview Director should take next."""
        return evaluation.nextAction
