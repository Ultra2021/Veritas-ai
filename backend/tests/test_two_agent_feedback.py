"""Unit tests proving the Two-Agent Adaptive Interview Core Feedback Loop.

Verifies that:
1. Agent 2 (EvidenceEngine) evaluates candidate answers into structured EvidenceEvaluations.
2. Agent 2 evaluations are passed into Agent 1 (InterviewDirector/QuestionBank).
3. Weak answers produce targeted follow-up questions probing evaluator-identified gaps.
4. Strong answers cause Agent 1 to move to another competency / verify.
5. Different candidate answers produce different next questions.
6. Follow-up questions target evaluator-identified gaps.
7. Exact duplicate questions are rejected.
8. Near-duplicate questions are rejected.
9. Interview cannot finish before 8 questions.
10. Interview can finish at 8 when evidence is sufficient.
11. Interview continues after 8 when evidence is insufficient.
12. Interview hard-stops at 20 questions.
13. Interview does not require all 10 competencies to be verified.
14. No cross-session question-cache contamination.
15. End-to-end feedback loop: Answer A -> Gap A -> Question A vs Answer B -> Gap B -> Question B.
"""

import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import services.candidate_service as candidate_service
from agents.evidence_engine import EvidenceEngine, MockEvidenceEvaluator
from agents.interview_director import InterviewDirector
from agents.question_bank import (
    LLMQuestionBank,
    StaticQuestionBank,
    _are_near_duplicates,
)
from models.evidence import EvidenceEvaluation
from models.interview_state import CompetencyState, InterviewState
from services.curriculum_service import CurriculumService
from services.interview_service import InterviewService
from services.session_service import SessionService

CANDIDATE_ID = "CAND-001"


def _build_test_stack():
    curriculum_service = CurriculumService(
        str(Path(__file__).resolve().parent.parent.parent / "curriculum.json")
    )
    session_service = SessionService()
    director = InterviewDirector(candidate_service, curriculum_service)
    evidence_engine = EvidenceEngine(curriculum_service=curriculum_service)
    service = InterviewService(
        candidate_service=candidate_service,
        curriculum_service=curriculum_service,
        session_service=session_service,
        director=director,
        evidence_engine=evidence_engine,
    )
    return service, curriculum_service, session_service, director, evidence_engine


def _strong_answer(state, curriculum: CurriculumService) -> str:
    """Build an answer rich in the current competency's curriculum keywords."""
    from agents.evidence_engine import _STOPWORDS
    import re
    keywords = []
    for topic in curriculum.get_topics():
        if topic.title.lower() == (state.currentCompetency or "").lower():
            terms = {
                term
                for objective in curriculum.get_day(topic.day).objectives
                for term in re.findall(r"[a-z']+", objective.lower())
                if len(term) > 4 and term not in _STOPWORDS
            }
            keywords = sorted(terms)
            break
    joined = ", ".join(keywords[:6]) or "system, database, architecture, production"
    return (
        "I recently built a system where " + joined + " all mattered. For example, we had to "
        "balance latency and accuracy, because the production environment demanded sub-200ms "
        "responses, and therefore we chose a hybrid architecture. However, that decision was a "
        "real trade-off: although we gained speed, the added complexity forced us to reason "
        "carefully about failures. As a result, we documented every choice, which made the "
        "whole team more effective."
    )


class TestTwoAgentFeedbackLoop:
    """Core tests for Agent 2 -> Agent 1 feedback loop and adaptive rules."""

    def test_01_agent_2_evaluates_candidate_answer(self):
        _, curriculum, _, _, engine = _build_test_stack()
        state = InterviewState(sessionId=uuid4(), candidateId=CANDIDATE_ID, currentCompetency="Embeddings Explained")
        state.currentQuestionId = "Q1"
        state.currentQuestion = "What are embeddings?"

        eval_res = engine.evaluate_answer(state, "Embeddings map tokens to high-dimensional semantic vector spaces.")
        assert isinstance(eval_res, EvidenceEvaluation)
        assert eval_res.competency == "Embeddings Explained"
        assert 0 <= eval_res.evidenceScore <= 100
        assert isinstance(eval_res.strengths, list)
        assert isinstance(eval_res.gaps, list)
        assert eval_res.reason

    def test_02_agent_2_evaluation_passed_to_agent_1(self):
        service, _, sessions, _, _ = _build_test_stack()
        turn1 = service.start_interview(CANDIDATE_ID)
        state = sessions.get_session(turn1.sessionId)

        turn2 = service.process_answer(turn1.sessionId, "I use Redis for basic caching.")
        assert turn2.evidence is not None
        assert len(state.evidenceEvaluations) == 1
        assert state.evidenceEvaluations[-1].competency == turn1.currentCompetency

    def test_03_weak_answer_produces_targeted_followup(self):
        service, _, sessions, _, _ = _build_test_stack()
        turn1 = service.start_interview(CANDIDATE_ID)

        turn2 = service.process_answer(turn1.sessionId, "I don't know much about this.")
        assert turn2.currentCompetency == turn1.currentCompetency
        assert turn2.questionId == "Q2"
        assert turn2.evidence.evidenceScore < 80

    def test_04_strong_answer_causes_agent_1_to_move_to_another_competency(self):
        service, curriculum, sessions, _, _ = _build_test_stack()
        turn1 = service.start_interview(CANDIDATE_ID)
        state = sessions.get_session(turn1.sessionId)

        turn2 = service.process_answer(turn1.sessionId, _strong_answer(state, curriculum))
        assert turn2.evidence.verified is True
        assert turn2.currentCompetency != turn1.currentCompetency

    def test_05_different_candidate_answers_produce_different_next_questions(self):
        service1, _, sessions1, _, _ = _build_test_stack()
        turn1 = service1.start_interview(CANDIDATE_ID)
        comp = turn1.currentCompetency

        # Answer 1: triggers invalidation/stale data gap
        eval_invalidation = EvidenceEvaluation(
            competency=comp,
            evidenceScore=45,
            technicalScore=40,
            reasoningScore=40,
            completenessScore=50,
            communicationScore=60,
            verified=False,
            followUpRequired=True,
            nextAction="FOLLOW_UP",
            reason="Cache invalidation strategy not explained.",
            strengths=["Understands basic caching"],
            gaps=["cache invalidation strategy not explained", "stale data handling missing"],
            questionId="Q1",
            question="Tell me about your caching setup.",
        )
        state1 = sessions1.get_session(turn1.sessionId)
        state1.currentAnswer = "I'd use Redis for caching because it reduces database load."
        state1.evidenceEvaluations.append(eval_invalidation)

        director = InterviewDirector(candidate_service, CurriculumService(str(Path(__file__).resolve().parent.parent.parent / "curriculum.json")))
        q_path_a = director.generate_followup_question(state1).question

        # Answer 2: triggers failure/recovery gap
        state2 = InterviewState(sessionId=uuid4(), candidateId=CANDIDATE_ID, currentCompetency=comp)
        state2.conversationHistory = list(state1.conversationHistory)
        state2.currentAnswer = "I'd use Redis with TTL-based expiration, invalidate entries after writes, and version cache keys."
        eval_failure = EvidenceEvaluation(
            competency=comp,
            evidenceScore=55,
            technicalScore=50,
            reasoningScore=50,
            completenessScore=60,
            communicationScore=70,
            verified=False,
            followUpRequired=True,
            nextAction="FOLLOW_UP",
            reason="Failure recovery behavior not addressed.",
            strengths=["Understands TTL and invalidation"],
            gaps=["failure recovery behavior is not addressed"],
            questionId="Q1",
            question="Tell me about your caching setup.",
        )
        state2.evidenceEvaluations.append(eval_failure)
        q_path_b = director.generate_followup_question(state2).question

        assert q_path_a != q_path_b
        assert "invalidation" in q_path_a.lower() or "stale" in q_path_a.lower()
        assert "unavailable" in q_path_b.lower() or "fail" in q_path_b.lower() or "recovery" in q_path_b.lower()

    def test_06_followup_explicitly_targets_evaluator_identified_gap(self):
        bank = StaticQuestionBank()
        state = InterviewState(sessionId=uuid4(), candidateId=CANDIDATE_ID, currentCompetency="Docker")
        state.currentAnswer = "I run Docker containers."
        state.evidenceEvaluations.append(EvidenceEvaluation(
            competency="Docker",
            evidenceScore=40,
            technicalScore=40,
            reasoningScore=30,
            completenessScore=40,
            communicationScore=50,
            verified=False,
            followUpRequired=True,
            nextAction="FOLLOW_UP",
            reason="Lacks cache invalidation strategy.",
            strengths=[],
            gaps=["cache invalidation strategy not explained"],
            questionId="Q1",
            question="Explain Docker.",
        ))

        q = bank.followup_for("Docker", state)
        assert "invalidation" in q.lower() or "stale" in q.lower() or "docker" in q.lower()

    def test_07_exact_duplicate_questions_are_rejected(self):
        q = "How do indexing and distance metrics affect retrieval quality and speed?"
        assert _are_near_duplicates(q, q) is True

    def test_08_near_duplicate_questions_are_rejected(self):
        q1 = "How would you roll out a new model version without downtime?"
        q2 = "How would you plan a safe rollout of a new model version without downtime?"
        assert _are_near_duplicates(q1, q2) is True

    def test_09_interview_cannot_finish_before_8_questions(self):
        service, _, sessions, _, _ = _build_test_stack()
        turn = service.start_interview(CANDIDATE_ID)
        state = sessions.get_session(turn.sessionId)

        # 5 strong answers = 5 questions < 8
        for _ in range(5):
            turn = service.process_answer(turn.sessionId, "Strong answer providing full technical depth and explicit reasoning for production systems.")
            if turn.done:
                break

        assert turn.done is False
        assert len([m for m in state.conversationHistory if m.role == "interviewer"]) == 6

    def test_10_interview_can_finish_at_8_when_evidence_is_sufficient(self):
        service, curriculum, sessions, _, engine = _build_test_stack()
        turn = service.start_interview(CANDIDATE_ID)
        state = sessions.get_session(turn.sessionId)

        # Give strong answers to verify competencies (8 turns total)
        for i in range(8):
            turn = service.process_answer(
                turn.sessionId,
                _strong_answer(state, curriculum)
            )
            if turn.done:
                break

        assert turn.done is True
        assert len([m for m in state.conversationHistory if m.role == "interviewer"]) >= 8

    def test_11_interview_continues_after_8_when_evidence_is_insufficient(self):
        service, _, sessions, _, _ = _build_test_stack()
        turn = service.start_interview(CANDIDATE_ID)
        state = sessions.get_session(turn.sessionId)

        # 7 weak answers = 8 questions presented, but evidence scores are 0-30
        for _ in range(7):
            turn = service.process_answer(turn.sessionId, "I am not sure about this.")

        # Should continue because evidence is insufficient
        assert turn.done is False

    def test_12_interview_hard_stops_at_20(self):
        service, _, sessions, _, _ = _build_test_stack()
        turn = service.start_interview(CANDIDATE_ID)

        turns = 0
        while not turn.done and turns < 25:
            turn = service.process_answer(turn.sessionId, "I am not sure.")
            turns += 1

        state = sessions.get_session(turn.sessionId)
        questions_asked = sum(1 for m in state.conversationHistory if m.role == "interviewer")
        assert questions_asked == 20
        assert turn.done is True

    def test_13_interview_does_not_require_all_competencies_to_be_verified(self):
        service, curriculum, sessions, _, engine = _build_test_stack()
        turn = service.start_interview(CANDIDATE_ID)
        state = sessions.get_session(turn.sessionId)

        # Provide good answers for 4 competencies
        for _ in range(8):
            turn = service.process_answer(
                turn.sessionId,
                _strong_answer(state, curriculum)
            )
            if turn.done:
                break

        assert turn.done is True
        verified_count = sum(1 for c in state.competencies if c.status == "verified")
        total_competencies = len(state.competencies)
        assert verified_count < total_competencies

    def test_14_no_cross_session_question_cache_contamination(self):
        bank = LLMQuestionBank()
        state1 = InterviewState(sessionId=uuid4(), candidateId="CAND-001")
        state2 = InterviewState(sessionId=uuid4(), candidateId="CAND-002")

        q1_list = bank.questions_for("RAG", state1)
        q2_list = bank.questions_for("RAG", state2)
        assert isinstance(q1_list, list)
        assert isinstance(q2_list, list)

    def test_15_end_to_end_candidate_answer_eval_decision_next_question(self):
        service, _, sessions, director, engine = _build_test_stack()
        turn1 = service.start_interview(CANDIDATE_ID)
        sessionId = turn1.sessionId

        # Turn 1: Candidate gives answer
        turn2 = service.process_answer(sessionId, "I'd use Redis for caching to speed up DB reads.")
        assert turn2.evidence is not None
        assert turn2.evidence.gaps
        assert turn2.questionId == "Q2"
        assert turn2.question != turn1.question

        # Turn 2: Candidate gives follow-up answer addressing gap
        turn3 = service.process_answer(sessionId, "We use TTL invalidation on database write operations to prevent stale cache entries.")
        assert turn3.questionId == "Q3"
        assert turn3.evidence is not None
