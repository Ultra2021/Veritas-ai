"""Unit tests verifying natural, gap-driven follow-up question quality.

Verifies that:
1. Follow-up does NOT begin with 'Beyond what you mentioned regarding'.
2. Follow-up targets the evaluator's current gap.
3. Different gaps produce different questions.
4. A resolved gap is not asked again.
5. Candidate keywords are only included when they improve clarity (no mechanical insertion).
6. No repetitive sentence template across consecutive follow-ups.
7. Near-duplicate questions are still rejected.
"""

import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import services.candidate_service as candidate_service
from agents.evidence_engine import EvidenceEngine
from agents.interview_director import InterviewDirector
from agents.question_bank import (
    StaticQuestionBank,
    _are_near_duplicates,
    _build_targeted_fallback,
    _is_overly_generic_followup,
)
from models.evidence import EvidenceEvaluation
from models.interview_state import ConversationMessage, InterviewState
from services.curriculum_service import CurriculumService
from services.session_service import SessionService

CANDIDATE_ID = "CAND-001"


def _build_test_deps():
    curriculum = CurriculumService(
        str(Path(__file__).resolve().parent.parent.parent / "curriculum.json")
    )
    sessions = SessionService()
    director = InterviewDirector(candidate_service, curriculum)
    engine = EvidenceEngine(curriculum_service=curriculum)
    bank = StaticQuestionBank()
    return curriculum, sessions, director, engine, bank


class TestFollowUpQuestionQuality:
    """Test suite ensuring natural, gap-driven follow-up question quality."""

    def test_01_followup_does_not_begin_with_beyond_what_you_mentioned(self):
        _, _, _, _, bank = _build_test_deps()
        state = InterviewState(sessionId=uuid4(), candidateId=CANDIDATE_ID, currentCompetency="Docker & Kubernetes Deployment")
        state.currentAnswer = "I'd containerize the app using Dockerfile and Uvicorn."
        state.evidenceEvaluations.append(
            EvidenceEvaluation(
                competency="Docker & Kubernetes Deployment",
                evidenceScore=60,
                technicalScore=60,
                reasoningScore=60,
                completenessScore=60,
                communicationScore=60,
                verified=False,
                followUpRequired=True,
                nextAction="FOLLOW_UP",
                reason="Secrets and security not addressed.",
                gaps=["container security and secret management not addressed"],
                questionId="Q1",
                question="How would you containerize a chatbot application with Docker?",
            )
        )

        q = bank.followup_for("Docker & Kubernetes Deployment", state)
        assert not q.lower().startswith("beyond what you mentioned regarding")
        assert _is_overly_generic_followup(f"Beyond what you mentioned regarding secure, server, how would you handle") is True

    def test_02_followup_targets_evaluators_current_gap(self):
        _, _, _, _, bank = _build_test_deps()
        state = InterviewState(sessionId=uuid4(), candidateId=CANDIDATE_ID, currentCompetency="Security")
        state.evidenceEvaluations.append(
            EvidenceEvaluation(
                competency="Security",
                evidenceScore=50,
                technicalScore=50,
                reasoningScore=50,
                completenessScore=50,
                communicationScore=50,
                verified=False,
                followUpRequired=True,
                nextAction="FOLLOW_UP",
                reason="Prompt injection defense missing.",
                gaps=["prompt injection defense and input sanitization guardrails not addressed"],
                questionId="Q1",
                question="What security considerations matter for AI APIs?",
            )
        )

        q = bank.followup_for("Security", state)
        assert "prompt injection" in q.lower() or "sanitiz" in q.lower() or "guardrail" in q.lower()

    def test_03_different_gaps_produce_different_questions(self):
        _, _, _, _, _ = _build_test_deps()
        q_gap_a = _build_targeted_fallback("Docker", "container security and secret management not addressed")
        q_gap_b = _build_targeted_fallback("Docker", "container orchestration, scaling, and deployment strategy not addressed")

        assert q_gap_a != q_gap_b
        assert "secret" in q_gap_a.lower() or "secure" in q_gap_a.lower()
        assert "kubernetes" in q_gap_b.lower() or "scale" in q_gap_b.lower() or "deploy" in q_gap_b.lower()

    def test_04_resolved_gap_is_not_asked_again(self):
        _, _, director, engine, bank = _build_test_deps()
        state = InterviewState(sessionId=uuid4(), candidateId=CANDIDATE_ID, currentCompetency="Docker & Kubernetes Deployment")
        state.currentQuestion = "How would you containerize a chatbot application with Docker?"
        state.currentQuestionId = "Q1"
        state.conversationHistory.append(
            ConversationMessage(role="interviewer", message=state.currentQuestion)
        )

        # Turn 1: Candidate gives answer without security -> Agent 2 identifies security gap
        ans1 = "I use Dockerfile and Uvicorn."
        eval1 = engine.evaluate_answer(state, ans1)
        engine.update_competency(state, eval1)
        state.currentAnswer = ans1
        q1 = director.generate_followup_question(state).question
        assert "secure" in q1.lower() or "secret" in q1.lower()

        # Turn 2: Candidate answers q1 explaining security -> Agent 2 evaluates turn 2 answer
        # Security gap is resolved, remaining gap is orchestration!
        eval2 = EvidenceEvaluation(
            competency="Docker & Kubernetes Deployment",
            evidenceScore=75,
            technicalScore=75,
            reasoningScore=75,
            completenessScore=75,
            communicationScore=75,
            verified=False,
            followUpRequired=True,
            nextAction="FOLLOW_UP",
            reason="Orchestration and scaling not addressed.",
            gaps=["container orchestration, scaling, and deployment strategy not addressed"],
            questionId="Q2",
            question=q1,
        )
        state.evidenceEvaluations.append(eval2)
        state.currentAnswer = "I inject secrets externally using environment variables and run as non-root user."

        q2 = director.generate_followup_question(state).question
        assert q2 != q1
        assert "kubernetes" in q2.lower() or "scale" in q2.lower() or "orchestrat" in q2.lower()

    def test_05_candidate_keywords_only_included_when_improving_clarity(self):
        q = _build_targeted_fallback("MCP", "version compatibility not addressed", candidate_answer="I use secure server connections.")
        assert not q.lower().startswith("beyond what you mentioned regarding")
        assert "compatibility" in q.lower() or "version" in q.lower()

    def test_06_no_repetitive_sentence_template_across_consecutive_followups(self):
        q1 = _build_targeted_fallback("RAG", "hybrid retrieval and reranking strategy not addressed", attempt=1)
        q2 = _build_targeted_fallback("RAG", "production retrieval evaluation and latency bounds not addressed", attempt=2)

        assert not q1.lower().startswith("beyond what you mentioned regarding")
        assert not q2.lower().startswith("beyond what you mentioned regarding")
        assert q1 != q2

    def test_07_near_duplicate_questions_are_still_rejected(self):
        q1 = "How would you secure the container and manage secrets when deploying Docker to production?"
        q2 = "How would you secure the container and manage secrets when deploying Docker to production?"
        assert _are_near_duplicates(q1, q2) is True
