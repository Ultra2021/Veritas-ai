"""Unit tests for the InterviewService orchestration (Module 7)."""

import json
import re
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import services.candidate_service as candidate_service
from agents.evidence_engine import EvidenceEngine, _STOPWORDS
from agents.interview_director import InterviewDirector
from services.curriculum_service import CurriculumService
from services.interview_service import (
    EmptyAnswerError,
    InterviewCompletedError,
    InterviewService,
    MissingCurrentQuestionError,
)
from services.session_service import SessionService, SessionNotFoundError

CANDIDATE_ID = "CAND-001"


def _curriculum_keywords(curriculum: CurriculumService, competency: str) -> list[str]:
    """Replicate the Evidence Engine's curriculum keyword extraction."""
    for topic in curriculum.get_topics():
        if topic.title.lower() == (competency or "").lower():
            terms = {
                term
                for objective in curriculum.get_day(topic.day).objectives
                for term in re.findall(r"[a-z']+", objective.lower())
                if len(term) > 4 and term not in _STOPWORDS
            }
            return sorted(terms)
    return []


def _strong_answer(state, curriculum: CurriculumService) -> str:
    """Build an answer rich in the current competency's curriculum keywords."""
    keywords = _curriculum_keywords(curriculum, state.currentCompetency or "")
    joined = ", ".join(keywords[:6]) or "system, database, architecture, production"
    return (
        "I recently built a system where " + joined + " all mattered. For example, we had to "
        "balance latency and accuracy, because the production environment demanded sub-200ms "
        "responses, and therefore we chose a hybrid architecture. However, that decision was a "
        "real trade-off: although we gained speed, the added complexity forced us to reason "
        "carefully about failures. As a result, we documented every choice, which made the "
        "whole team more effective."
    )


def _build_service() -> tuple[InterviewService, CurriculumService, SessionService]:
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
    return service, curriculum_service, session_service


class TestInterviewService:
    """Organized around the eight required test scenarios."""

    def _start(self, service: InterviewService):
        return service.start_interview(CANDIDATE_ID)

    # 1. Starting an interview
    def test_start_interview_creates_session_and_first_question(self):
        service, _, sessions = _build_service()
        resp = self._start(service)

        assert resp.sessionId
        assert resp.questionId == "Q1"
        assert resp.question
        assert resp.currentCompetency
        assert resp.interviewStage == "interviewing"
        assert resp.done is False
        assert resp.evidence is None

        state = sessions.get_session(resp.sessionId)
        assert state.currentQuestion == resp.question
        assert state.currentQuestionId == "Q1"
        assert state.currentCompetency == resp.currentCompetency
        assert len(state.competencies) >= 1
        roles = [message.role for message in state.conversationHistory]
        assert roles[:2] == ["system", "interviewer"]

    # 2. Processing a strong answer
    def test_strong_answer_updates_evidence_and_generates_next_question(self):
        service, curriculum, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)

        next_resp = service.process_answer(
            resp.sessionId, _strong_answer(state, curriculum)
        )

        entry = next(
            c for c in state.competencies if c.competency == resp.currentCompetency
        )
        assert entry.status == "verified"
        assert entry.evidenceScore >= 80
        assert entry.attempts == 1

        evaluation = state.evidenceEvaluations[-1]
        assert evaluation.competency == resp.currentCompetency
        assert evaluation.questionId == resp.questionId

        assert next_resp.done is False
        assert next_resp.question
        assert next_resp.questionId == "Q2"
        assert next_resp.currentCompetency != resp.currentCompetency
        assert 0 <= state.hiringConfidence <= 100
        assert 0 <= state.interviewDNA.technicalKnowledge <= 100
        assert next_resp.evidence is not None
        assert next_resp.evidence.evidenceScore >= 80

    # 3. Processing a weak answer
    def test_weak_answer_requests_followup_and_keeps_competency(self):
        service, _, sessions = _build_service()
        resp = self._start(service)

        next_resp = service.process_answer(resp.sessionId, "I don't know.")

        state = sessions.get_session(resp.sessionId)
        entry = next(
            c for c in state.competencies if c.competency == resp.currentCompetency
        )
        assert entry.status == "needs_followup"
        assert next_resp.currentCompetency == resp.currentCompetency
        assert next_resp.done is False
        assert next_resp.question
        assert next_resp.questionId == "Q2"
        assert next_resp.questionId != resp.questionId
        assert next_resp.evidence is not None
        assert next_resp.evidence.evidenceScore < 80

    # 4. Multiple turns
    def test_multiple_turns_keep_ordered_history_and_persist(self):
        service, curriculum, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)

        service.process_answer(resp.sessionId, "I don't know.")  # weak -> follow-up Q2
        resp = service.process_answer(
            resp.sessionId, _strong_answer(state, curriculum)
        )  # strong -> next competency Q3

        roles = [message.role for message in state.conversationHistory]
        assert roles == [
            "system",
            "interviewer",
            "candidate",
            "evaluator",
            "interviewer",
            "candidate",
            "evaluator",
            "interviewer",
        ]
        assert state.currentQuestionId == "Q3"
        assert len(sessions.get_session(resp.sessionId).conversationHistory) == 8

    # 5. Completed interview
    def test_completed_interview_returns_done_without_new_question(self):
        service, curriculum, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)

        for _ in range(20):
            before = len(
                [m for m in state.conversationHistory if m.role == "interviewer"]
            )
            resp = service.process_answer(
                resp.sessionId, _strong_answer(state, curriculum)
            )
            if resp.done:
                after = len(
                    [m for m in state.conversationHistory if m.role == "interviewer"]
                )
                assert after == before
                break

        assert resp.done is True
        assert resp.interviewStage == "completed"
        assert resp.question
        assert sessions.get_session(resp.sessionId).completed is True
        assert resp.hiringConfidence is not None
        assert 0 <= resp.hiringConfidence <= 100

    def test_completed_interview_rejects_new_answers(self):
        service, curriculum, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)

        for _ in range(20):
            resp = service.process_answer(
                resp.sessionId, _strong_answer(state, curriculum)
            )
            if resp.done:
                break

        assert resp.done is True
        with pytest.raises(InterviewCompletedError):
            service.process_answer(resp.sessionId, "Anything at all.")

    # 6. Invalid session
    def test_process_answer_unknown_session_raises(self):
        service, _, _ = _build_service()
        with pytest.raises(SessionNotFoundError):
            service.process_answer(uuid4(), "Hello?")

    # 7. Empty answer
    def test_empty_answer_raises_validation_error(self):
        service, _, _ = _build_service()
        resp = self._start(service)
        for bad in ("", "   ", None):
            with pytest.raises(EmptyAnswerError):
                service.process_answer(resp.sessionId, bad)

    # 8. Question/answer traceability
    def test_answer_evaluation_traceability(self):
        service, curriculum, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        answer = _strong_answer(state, curriculum)

        service.process_answer(resp.sessionId, answer)

        evaluation = state.evidenceEvaluations[-1]
        assert evaluation.questionId == resp.questionId
        assert evaluation.question == resp.question
        assert evaluation.competency == resp.currentCompetency

        history = state.conversationHistory
        candidate_idx = next(
            i
            for i, message in enumerate(history)
            if message.role == "candidate" and message.message == answer
        )
        assert history[candidate_idx + 1].role == "evaluator"
        assert history[candidate_idx + 1].message.startswith("Evidence score:")

    # Extra: error handling and frontend contract
    def test_start_interview_unknown_candidate_raises(self):
        service, _, _ = _build_service()
        with pytest.raises(candidate_service.CandidateNotFoundError):
            service.start_interview("DOES-NOT-EXIST")

    def test_missing_current_question_raises(self):
        service, _, sessions = _build_service()
        state = sessions.create_session(CANDIDATE_ID)
        with pytest.raises(MissingCurrentQuestionError):
            service.process_answer(state.sessionId, "Hello?")

    def test_responses_are_json_serializable(self):
        service, curriculum, sessions = _build_service()
        resp = self._start(service)
        json.dumps(resp.model_dump(mode="json"))

        state = sessions.get_session(resp.sessionId)
        turn = service.process_answer(resp.sessionId, _strong_answer(state, curriculum))
        payload = turn.model_dump(mode="json")
        json.dumps(payload)
        assert payload["sessionId"] == str(resp.sessionId)
        from models.interview_response import InterviewTurnResponse

        assert set(InterviewTurnResponse.model_fields) <= set(payload)
