"""Unit tests for the Evidence Engine (Module 6)."""

import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.evidence_engine import EvidenceEngine, MockEvidenceEvaluator
from models.evidence import EvidenceEvaluation
from models.interview_state import CompetencyState, InterviewState


STRONG_ANSWER = (
    "I built a document retrieval system with a vector database and a clean API layer. "
    "The architecture was designed to scale horizontally, for example by sharding the "
    "database across nodes. We added caching because we needed to stay under 200ms in "
    "production, and we therefore chose a hybrid approach as a trade-off between latency "
    "and accuracy."
)

WEAK_ANSWER = "I like computers."

EMPTY_ANSWER = ""


class TestEvidenceEngine:
    """Organized around the seven required test scenarios."""

    def _make_state(
        self,
        competency: str = "technicalKnowledge",
        question: str = "Walk me through a technical project you are most proud of.",
    ) -> InterviewState:
        return InterviewState(
            sessionId=uuid4(),
            candidateId="CAND-001",
            currentCompetency=competency,
            currentQuestion=question,
            currentQuestionId="Q1",
        )

    def _evaluate(self, state: InterviewState, answer: str):
        engine = EvidenceEngine()
        evaluation = engine.evaluate_answer(state, answer)
        engine.update_competency(state, evaluation)
        engine.update_interview_dna(state, evaluation)
        return engine, evaluation

    # 1. Strong answer
    def test_strong_answer_is_verified(self):
        state = self._make_state()
        engine, evaluation = self._evaluate(state, STRONG_ANSWER)
        assert evaluation.evidenceScore >= 80
        assert evaluation.verified is True
        assert evaluation.followUpRequired is False
        assert evaluation.nextAction == "NEXT_COMPETENCY"

    # 2. Weak answer
    def test_weak_answer_needs_followup(self):
        state = self._make_state()
        engine, evaluation = self._evaluate(state, WEAK_ANSWER)
        assert evaluation.evidenceScore < 80
        assert evaluation.verified is False
        assert evaluation.followUpRequired is True
        assert evaluation.nextAction == "FOLLOW_UP"

    # 3. Empty answer
    def test_empty_answer_very_low_and_followup(self):
        state = self._make_state()
        engine, evaluation = self._evaluate(state, EMPTY_ANSWER)
        assert evaluation.evidenceScore == 0
        assert evaluation.verified is False
        assert evaluation.followUpRequired is True
        assert evaluation.nextAction == "FOLLOW_UP"
        assert evaluation.reason == "No answer provided."

    # 4. Existing competency is updated, not duplicated
    def test_update_competency_updates_existing(self):
        state = self._make_state()
        state.competencies.append(
            CompetencyState(competency="technicalKnowledge", status="in_progress", attempts=1)
        )
        engine = EvidenceEngine()
        evaluation = engine.evaluate_answer(state, STRONG_ANSWER)
        entry = engine.update_competency(state, evaluation)
        assert len(state.competencies) == 1
        assert entry.attempts == 2
        assert entry.evidenceScore == evaluation.evidenceScore
        assert entry.status == "verified"

    # 5. New competency is created
    def test_update_competency_creates_new(self):
        state = self._make_state(competency="RAG", question="Explain how RAG works.")
        engine = EvidenceEngine()
        evaluation = engine.evaluate_answer(
            state, "RAG retrieves context and augments the prompt for generation."
        )
        entry = engine.update_competency(state, evaluation)
        assert len(state.competencies) == 1
        assert entry.competency == "RAG"
        assert entry.attempts == 1

    # 6. Hiring confidence stays within 0-100
    def test_hiring_confidence_within_bounds(self):
        state = self._make_state()
        engine, evaluation = self._evaluate(state, STRONG_ANSWER)
        confidence = engine.calculate_hiring_confidence(state)
        assert 0 <= confidence <= 100
        assert state.hiringConfidence == confidence

        # weak evidence lowers confidence but stays in bounds
        weak_state = self._make_state(question="Follow-up.")
        engine.update_competency(
            state, engine.evaluate_answer(weak_state, WEAK_ANSWER)
        )
        confidence = engine.calculate_hiring_confidence(state)
        assert 0 <= confidence <= 100

    def test_hiring_confidence_empty_state_is_zero(self):
        state = self._make_state()
        engine = EvidenceEngine()
        assert engine.calculate_hiring_confidence(state) == 0

    # 7. Interview DNA stays within 0-100 and maps correctly
    def test_interview_dna_within_bounds_and_mapping(self):
        state = self._make_state()
        engine, evaluation = self._evaluate(state, STRONG_ANSWER)
        dna = state.interviewDNA
        assert dna.technicalKnowledge == evaluation.technicalScore
        assert dna.communication == evaluation.communicationScore
        assert dna.problemSolving == evaluation.reasoningScore
        for value in (
            dna.technicalKnowledge,
            dna.communication,
            dna.problemSolving,
            dna.leadership,
            dna.learningAbility,
        ):
            assert 0 <= value <= 100
        # leadership/learningAbility preserved (not fabricated)
        assert dna.leadership == 0
        assert dna.learningAbility == 0

    def test_needs_followup_and_next_action(self):
        engine = EvidenceEngine()
        state = self._make_state()
        weak = engine.evaluate_answer(state, WEAK_ANSWER)
        assert engine.needs_followup(weak) is True
        assert engine.get_next_action(weak) == "FOLLOW_UP"
        strong = engine.evaluate_answer(state, STRONG_ANSWER)
        assert engine.needs_followup(strong) is False
        assert engine.get_next_action(strong) == "NEXT_COMPETENCY"

    def test_evaluation_traceability(self):
        state = self._make_state(competency="Docker", question="Explain Docker containers.")
        engine = EvidenceEngine()
        evaluation = engine.evaluate_answer(
            state, "A Docker container packages an image with its runtime and layers."
        )
        engine.update_competency(state, evaluation)
        assert evaluation.questionId == "Q1"
        assert evaluation.question == "Explain Docker containers."
        assert state.evidenceEvaluations[-1] is evaluation

    def test_evaluation_model_bounds(self):
        from pydantic import ValidationError

        try:
            EvidenceEvaluation(
                competency="c",
                evidenceScore=150,
                technicalScore=0,
                reasoningScore=0,
                completenessScore=0,
                communicationScore=0,
                verified=False,
                followUpRequired=True,
                nextAction="FOLLOW_UP",
            )
        except ValidationError:
            assert True
        else:
            raise AssertionError("out-of-range score should be rejected")

    def test_curriculum_keywords_wireup(self):
        from services.curriculum_service import CurriculumService

        state = self._make_state(
            competency="Embeddings",
            question="What are embeddings and why are they useful?",
        )
        engine = EvidenceEngine(
            curriculum_service=CurriculumService(
                str(Path(__file__).resolve().parent.parent.parent / "curriculum.json")
            )
        )
        evaluation = engine.evaluate_answer(
            state, "Embeddings map tokens into semantic vector space."
        )
        assert isinstance(evaluation, EvidenceEvaluation)
        assert 0 <= evaluation.evidenceScore <= 100
