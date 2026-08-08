"""Unit tests for the InterviewService orchestration (Module 7)."""

import json
import re
import sys
from pathlib import Path
from uuid import UUID, uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import services.candidate_service as candidate_service
from agents.evidence_engine import EvidenceEngine, _STOPWORDS
from agents.interview_director import (
    InterviewDirector,
    MAX_FOLLOWUPS_PER_COMPETENCY,
    MAX_QUESTIONS_TO_COMPLETE,
    MIN_DISTINCT_CURRICULUM_DAYS,
    MIN_QUESTIONS_TO_COMPLETE,
)
from agents.question_bank import LLMQuestionBank, StaticQuestionBank
from models.evidence import EvidenceEvaluation
from models.interview_state import (
    CompetencyState,
    ConversationMessage,
    InterviewState,
)
from services.curriculum_service import CurriculumService
from services.interview_service import (
    EmptyAnswerError,
    InsufficientQuestionError,
    InterviewCompletedError,
    InterviewService,
    MissingCurrentQuestionError,
)
from services.session_service import SessionNotFoundError, SessionService

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


def _trim_competencies(state: InterviewState, count: int) -> None:
    """Keep the current competency plus ``count - 1`` more.

    The director always starts on a seeded curriculum competency (the
    first one rotates deterministically by session id), so the ledger
    must retain ``currentCompetency``; otherwise follow-ups are generated
    against a competency missing from the ledger and the interview would
    quietly exceed the intended size.
    """
    current = next(
        entry
        for entry in state.competencies
        if entry.competency == state.currentCompetency
    )
    others = [
        entry
        for entry in state.competencies
        if entry.competency != current.competency
    ]
    state.competencies = [current, *others[: count - 1]]


class _FakeQuestionProvider:
    """A provider returning a fixed scenario-question list on demand."""

    def __init__(self, questions):
        self.questions = list(questions)
        self.calls = 0

    def questions_for(self, *, competency, curriculum_context="", conversation_context=""):
        self.calls += 1
        return list(self.questions)

    def followup_for(self, *, competency, curriculum_context="", conversation_context=""):
        return None


class _RejectFollowupBank(StaticQuestionBank):
    """A bank whose follow-up is always an already-asked question.

    Forces the Interview Director to reject the follow-up (duplicate
    prevention), so the orchestration layer must move on without counting
    the rejected question.
    """

    def followup_for(self, competency: str, state: InterviewState | None = None) -> str:
        asked = self._asked_questions(state)
        return next(iter(asked), "") if asked else ""


def _build_service_with_bank(bank) -> tuple[InterviewService, CurriculumService, SessionService]:
    curriculum_service = CurriculumService(
        str(Path(__file__).resolve().parent.parent.parent / "curriculum.json")
    )
    session_service = SessionService()
    director = InterviewDirector(
        candidate_service, curriculum_service, question_bank=bank
    )
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


class TestFollowUpCap:
    """Follow-ups must stop after MAX_FOLLOWUPS_PER_COMPETENCY attempts and
    never loop forever on a plateauing candidate."""

    def _start(self, service: InterviewService):
        return service.start_interview(CANDIDATE_ID)

    def test_followup_capped_per_competency(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        first = resp.currentCompetency

        weak = "I don't know."
        service.process_answer(resp.sessionId, weak)
        service.process_answer(resp.sessionId, weak)
        resp = service.process_answer(resp.sessionId, weak)

        state = sessions.get_session(resp.sessionId)
        entry = next(c for c in state.competencies if c.competency == first)
        assert entry.attempts == MAX_FOLLOWUPS_PER_COMPETENCY + 1
        assert entry.status == "needs_followup"
        assert resp.currentCompetency != first

    def test_followup_exhaustion_moves_to_next_competency(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        first = resp.currentCompetency

        for _ in range(MAX_FOLLOWUPS_PER_COMPETENCY + 1):
            resp = service.process_answer(resp.sessionId, "I don't know.")

        assert resp.currentCompetency != first
        entry = next(
            c
            for c in sessions.get_session(resp.sessionId).competencies
            if c.competency == first
        )
        assert entry.status == "needs_followup"
        assert entry.attempts == MAX_FOLLOWUPS_PER_COMPETENCY + 1

    def test_exhausted_single_competency_below_minimum_raises(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        state.competencies = [
            c for c in state.competencies if c.competency == resp.currentCompetency
        ]

        with pytest.raises(InsufficientQuestionError):
            for _ in range(MAX_FOLLOWUPS_PER_COMPETENCY + 1):
                service.process_answer(resp.sessionId, "I don't know.")

        final = sessions.get_session(resp.sessionId)
        assert final.completed is False
        assert (
            service._questions_presented(final)
            == MAX_FOLLOWUPS_PER_COMPETENCY + 1
            < MIN_QUESTIONS_TO_COMPLETE
        )

    def test_select_next_competency_skips_exhausted(self):
        _, curriculum, _ = _build_service()
        director = InterviewDirector(candidate_service, curriculum)
        exhausted = CompetencyState(
            competency="Exhausted",
            status="needs_followup",
            attempts=MAX_FOLLOWUPS_PER_COMPETENCY + 1,
        )
        pending = CompetencyState(competency="Pending", status="pending")
        state = InterviewState(sessionId=uuid4(), candidateId=CANDIDATE_ID)
        state.competencies = [exhausted, pending]

        assert director.select_next_competency(state) is pending
        state.currentCompetency = "Exhausted"
        assert director._resolve_competency(state) == "Pending"

        state.competencies = [exhausted]
        assert director.select_next_competency(state) is None
        assert director._resolve_competency(state) is None

    def test_total_followups_incremented_only_while_followup_asked(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        first = resp.currentCompetency
        state = sessions.get_session(resp.sessionId)
        assert state.metadata.totalFollowUps == 0

        service.process_answer(resp.sessionId, "I don't know.")
        assert state.metadata.totalFollowUps == 1
        service.process_answer(resp.sessionId, "I don't know.")
        assert state.metadata.totalFollowUps == 2

        resp = service.process_answer(resp.sessionId, "I don't know.")
        assert state.metadata.totalFollowUps == 2
        assert resp.currentCompetency != first

    def test_followup_never_repeats_within_session(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)

        turns = 0
        while not resp.done and turns < 100:
            resp = service.process_answer(resp.sessionId, "I don't know.")
            turns += 1

        assert resp.done is True
        asked = [m.message for m in state.conversationHistory if m.role == "interviewer"]
        assert len(asked) == len(set(asked))

    def test_interview_terminates_on_plateau(self):
        service, _, _ = _build_service()
        resp = self._start(service)
        turns = 0
        while not resp.done and turns < 100:
            resp = service.process_answer(resp.sessionId, "I don't know.")
            turns += 1

        assert resp.done is True
        assert turns <= 10 * (MAX_FOLLOWUPS_PER_COMPETENCY + 1)


class TestMinimumQuestionGate:
    """The interview must not complete before 8 questions are presented."""

    def _start(self, service: InterviewService):
        return service.start_interview(CANDIDATE_ID)

    def test_interview_cannot_complete_before_minimum_questions(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        # Two competencies supply at most 3 questions each -> 6 < 8.
        _trim_competencies(state, 2)

        with pytest.raises(InsufficientQuestionError):
            for _ in range(20):
                service.process_answer(resp.sessionId, "I don't know.")

        final = sessions.get_session(resp.sessionId)
        assert final.completed is False
        assert final.interviewStage != "completed"
        assert service._questions_presented(final) == 6
        assert service._questions_presented(final) < MIN_QUESTIONS_TO_COMPLETE

    def test_followup_questions_count_toward_minimum(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        # Four competencies supply 3 questions each -> 12 total, reaching the
        # minimum question count while covering four distinct curriculum days.
        _trim_competencies(state, 4)
        session_id = resp.sessionId

        resp = None
        for _ in range(12):
            resp = service.process_answer(session_id, "I don't know.")

        assert resp.done is True
        final = sessions.get_session(resp.sessionId)
        assert final.completed is True
        assert service._questions_presented(final) >= MIN_QUESTIONS_TO_COMPLETE

    def test_rejected_followup_does_not_count_toward_minimum(self):
        service, _, sessions = _build_service_with_bank(_RejectFollowupBank())
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        assert service._questions_presented(state) == 1

        next_resp = service.process_answer(resp.sessionId, "I don't know.")

        assert service._questions_presented(state) == 2
        assert next_resp.questionId == "Q2"
        asked = [m.message for m in state.conversationHistory if m.role == "interviewer"]
        assert len(asked) == len(set(asked))

    def test_followup_cap_preserved_under_minimum_gate(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 4)
        session_id = resp.sessionId

        resp = None
        for _ in range(12):
            resp = service.process_answer(session_id, "I don't know.")

        assert resp.done is True
        final = sessions.get_session(resp.sessionId)
        assert final.metadata.totalFollowUps == 4 * MAX_FOLLOWUPS_PER_COMPETENCY
        for entry in final.competencies:
            assert entry.attempts == MAX_FOLLOWUPS_PER_COMPETENCY + 1

    def test_duplicate_protection_preserved_under_minimum_gate(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 4)

        for _ in range(12):
            service.process_answer(resp.sessionId, "I don't know.")

        asked = [
            m.message
            for m in sessions.get_session(resp.sessionId).conversationHistory
            if m.role == "interviewer"
        ]
        assert len(asked) == 12
        assert len(set(asked)) == 12

    def test_naturally_long_interview_still_completes(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)

        turns = 0
        while not resp.done and turns < 100:
            resp = service.process_answer(resp.sessionId, "I don't know.")
            turns += 1

        assert resp.done is True
        assert sessions.get_session(resp.sessionId).completed is True
        assert service._questions_presented(state) == MAX_QUESTIONS_TO_COMPLETE
        assert turns == MAX_QUESTIONS_TO_COMPLETE


class TestCurriculumDayCoverage:
    """The interview must not complete before 8 questions across at least
    4 distinct curriculum days have been explored."""

    def _start(self, service: InterviewService):
        return service.start_interview(CANDIDATE_ID)

    def test_interview_cannot_complete_with_only_three_curriculum_days(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        # Three competencies supply 9 questions but only 3 distinct days.
        _trim_competencies(state, 3)
        session_id = resp.sessionId

        with pytest.raises(InsufficientQuestionError):
            for _ in range(12):
                service.process_answer(session_id, "I don't know.")

        final = sessions.get_session(session_id)
        assert final.completed is False
        assert final.interviewStage != "completed"
        assert service._questions_presented(final) == 9
        assert len(service._director.covered_curriculum_days(final)) == 3

    def test_followup_does_not_count_as_new_curriculum_day(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 2)
        session_id = resp.sessionId
        first_competency = resp.currentCompetency

        assert service._director.covered_curriculum_days(state) == set()

        for _ in range(3):
            service.process_answer(session_id, "I don't know.")

        final = sessions.get_session(session_id)
        first_day = next(
            entry.day
            for entry in final.competencies
            if entry.competency == first_competency
        )
        assert first_day is not None
        assert service._director.covered_curriculum_days(final) == {first_day}

    def test_uncovered_curriculum_day_is_prioritized(self):
        _, curriculum, _ = _build_service()
        director = InterviewDirector(candidate_service, curriculum)

        covered = CompetencyState(
            competency="Alpha", day=1, status="pending", attempts=1
        )
        uncovered = CompetencyState(
            competency="Zulu", day=2, status="pending", attempts=0
        )
        state = InterviewState(sessionId=uuid4(), candidateId=CANDIDATE_ID)
        state.competencies = [covered, uncovered]

        # Coverage threshold not met: the uncovered day wins over alphabetic order.
        assert director.select_next_competency(state) is uncovered

        # Once four distinct days are covered, normal alphabetic ordering resumes.
        state.competencies = [
            covered,
            CompetencyState(
                competency="Bravo", day=2, status="pending", attempts=1
            ),
            CompetencyState(
                competency="Charlie", day=3, status="pending", attempts=1
            ),
            CompetencyState(competency="Delta", day=4, status="pending", attempts=1),
            CompetencyState(competency="Zulu", day=5, status="pending", attempts=0),
        ]
        selected = director.select_next_competency(state)
        assert selected is not None
        assert selected.competency == "Alpha"

    def test_interview_completes_with_8_questions_and_4_days(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 4)
        session_id = resp.sessionId

        resp = None
        for _ in range(12):
            resp = service.process_answer(session_id, "I don't know.")

        assert resp.done is True
        final = sessions.get_session(session_id)
        assert final.completed is True
        assert service._questions_presented(final) >= MIN_QUESTIONS_TO_COMPLETE
        assert len(service._director.covered_curriculum_days(final)) == 4

    def test_33_competencies_are_not_required(self):
        service, curriculum, sessions = _build_service()
        resp = self._start(service)

        while not resp.done:
            resp = service.process_answer(resp.sessionId, "I don't know.")

        final = sessions.get_session(resp.sessionId)
        assert final.completed is True
        covered = service._director.covered_curriculum_days(final)
        assert len(covered) >= MIN_DISTINCT_CURRICULUM_DAYS
        assert len(covered) < len(curriculum.get_topics())

    def test_insufficient_curriculum_days_fails_deterministically(self):
        service, curriculum, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        # Strong answers verify each competency in one question: four
        # competencies cover four days but supply only four questions < 8.
        _trim_competencies(state, 4)
        session_id = resp.sessionId

        with pytest.raises(InsufficientQuestionError):
            for _ in range(6):
                service.process_answer(session_id, _strong_answer(state, curriculum))

        final = sessions.get_session(session_id)
        assert final.completed is False
        assert service._questions_presented(final) == 4
        assert len(service._director.covered_curriculum_days(final)) == 4

    def test_existing_8_question_gate_still_passes(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 2)
        session_id = resp.sessionId

        with pytest.raises(InsufficientQuestionError):
            for _ in range(12):
                service.process_answer(session_id, "I don't know.")

        final = sessions.get_session(session_id)
        assert final.completed is False
        assert service._questions_presented(final) == 6
        assert len(service._director.covered_curriculum_days(final)) == 2

    def test_existing_followup_cap_still_passes(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 4)
        session_id = resp.sessionId

        resp = None
        for _ in range(12):
            resp = service.process_answer(session_id, "I don't know.")

        assert resp.done is True
        final = sessions.get_session(session_id)
        assert final.metadata.totalFollowUps == 4 * MAX_FOLLOWUPS_PER_COMPETENCY
        for entry in final.competencies:
            assert entry.attempts == MAX_FOLLOWUPS_PER_COMPETENCY + 1

    def test_existing_duplicate_protection_still_passes(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 4)

        for _ in range(12):
            service.process_answer(resp.sessionId, "I don't know.")

        asked = [
            m.message
            for m in sessions.get_session(resp.sessionId).conversationHistory
            if m.role == "interviewer"
        ]
        assert len(asked) == 12
        assert len(set(asked)) == 12


class TestScenarioQuestionRotation:
    """Scenario questions rotate by a deterministic per-session offset.

    Competency selection, follow-ups, caching, and the completion gates are
    untouched: only which scenario question opens a competency changes.
    """

    def _start(self, service: InterviewService):
        return service.start_interview(CANDIDATE_ID)

    def _start_fixed(self, service, director, session_int: int) -> InterviewState:
        """Run ``start_interview`` against a session with a known id seed."""
        state = InterviewState(
            sessionId=UUID(int=session_int), candidateId=CANDIDATE_ID
        )
        service._seed_competencies(state, CANDIDATE_ID)
        director.start_interview(state)
        return state

    def test_start_interview_varies_first_question_across_sessions(self):
        service, curriculum, _ = _build_service()
        topics_by_day = {topic.day: topic.title for topic in curriculum.get_topics()}
        seeded = {
            topics_by_day.get(topic.day) or topic.title
            for topic in candidate_service.get_interview_topics(CANDIDATE_ID)
        }
        first_competencies = set()
        first_questions = set()
        for _ in range(50):
            resp = service.start_interview(CANDIDATE_ID)
            assert resp.currentCompetency in seeded
            first_competencies.add(resp.currentCompetency)
            first_questions.add(resp.question)

        assert len(first_competencies) > 1
        assert len(first_questions) > 1

    def test_start_interview_is_deterministic_for_same_seed(self):
        service, curriculum, _ = _build_service()
        director = InterviewDirector(candidate_service, curriculum)

        first = self._start_fixed(service, director, session_int=7)
        second = self._start_fixed(service, director, session_int=7)

        assert first.currentCompetency == second.currentCompetency
        assert first.currentQuestion == second.currentQuestion

        # The first question is the session-rotated scenario question for the
        # resolved competency: bank questions rotate by session offset, and
        # competencies without bank entries use the first deterministic fallback.
        questions = StaticQuestionBank().questions_for(first.currentCompetency)
        if questions:
            offset = UUID(int=7).int % len(questions)
            assert first.currentQuestion == questions[offset]
        else:
            assert first.currentQuestion == director._fallback_questions(
                first.currentCompetency
            )[0]

    def test_scenario_rotation_never_repeats_within_session(self):
        _, curriculum, _ = _build_service()
        director = InterviewDirector(candidate_service, curriculum)
        questions = StaticQuestionBank().questions_for("RAG")
        assert len(questions) == 3

        # Offset 2 exercises the wrap-around: index 2 -> 0 -> 1.
        state = InterviewState(
            sessionId=UUID(int=2), candidateId=CANDIDATE_ID
        )
        state.competencies = [
            CompetencyState(competency="RAG", day=1, status="pending")
        ]
        director.start_interview(state)

        seen = [state.currentQuestion]
        asked = {state.currentQuestion}
        assert seen[0] == questions[2]

        for _ in range(len(questions) - 1):
            question = director._next_question_for(state, "RAG")
            assert question not in asked
            asked.add(question)
            seen.append(question)
            state.conversationHistory.append(
                ConversationMessage(role="interviewer", message=question)
            )

        assert seen == questions[2:] + questions[:2]
        assert len(set(seen)) == len(seen) == 3

    def test_rotation_works_with_llm_question_bank(self):
        service, curriculum, _ = _build_service()
        provider = _FakeQuestionProvider(["L1?", "L2?", "L3?"])
        bank = LLMQuestionBank(provider=provider, curriculum_service=curriculum)
        director = InterviewDirector(candidate_service, curriculum, question_bank=bank)

        def _start_rag(session_int: int) -> InterviewState:
            state = InterviewState(
                sessionId=UUID(int=session_int), candidateId=CANDIDATE_ID
            )
            state.competencies = [
                CompetencyState(competency="RAG", day=1, status="pending")
            ]
            director.start_interview(state)
            return state

        first = _start_rag(0)
        second = _start_rag(1)
        third = _start_rag(2)

        assert first.currentCompetency == "RAG"
        assert first.currentQuestion == "L1?"
        assert second.currentQuestion == "L2?"
        assert third.currentQuestion == "L3?"
        assert provider.calls == 1

    def test_rotation_does_not_break_4_day_coverage(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 4)
        session_id = resp.sessionId

        resp = None
        for _ in range(12):
            resp = service.process_answer(session_id, "I don't know.")

        assert resp.done is True
        final = sessions.get_session(session_id)
        assert final.completed is True
        assert service._questions_presented(final) >= MIN_QUESTIONS_TO_COMPLETE
        assert len(service._director.covered_curriculum_days(final)) == 4


class TestFirstCompetencyVariation:
    """Session-seeded variation of the FIRST competency only.

    The very first competency rotates deterministically by session id
    across the candidate's seeded eligible competencies. All post-Q1
    selection (uncovered curriculum-day prioritization, alphabetical
    ordering) is unchanged.
    """

    def _build(self) -> tuple[InterviewService, CurriculumService, SessionService]:
        return _build_service()

    @staticmethod
    def _seeded_competencies(curriculum: CurriculumService) -> set[str]:
        topics_by_day = {topic.day: topic.title for topic in curriculum.get_topics()}
        return {
            topics_by_day.get(topic.day) or topic.title
            for topic in candidate_service.get_interview_topics(CANDIDATE_ID)
        }

    @staticmethod
    def _start_fixed(
        service: InterviewService, director: InterviewDirector, session_int: int
    ) -> InterviewState:
        state = InterviewState(
            sessionId=UUID(int=session_int), candidateId=CANDIDATE_ID
        )
        service._seed_competencies(state, CANDIDATE_ID)
        director.start_interview(state)
        return state

    def test_first_competency_varies_across_sessions(self):
        service, curriculum, _ = self._build()
        director = InterviewDirector(candidate_service, curriculum)
        first_competencies = set()
        for session_int in range(10):
            state = self._start_fixed(service, director, session_int)
            first_competencies.add(state.currentCompetency)
        assert len(first_competencies) > 1

    def test_first_competency_is_deterministic_for_same_session(self):
        service, curriculum, _ = self._build()
        director = InterviewDirector(candidate_service, curriculum)
        first = self._start_fixed(service, director, session_int=11)
        second = self._start_fixed(service, director, session_int=11)
        assert first.currentCompetency == second.currentCompetency
        assert first.currentQuestion == second.currentQuestion

    def test_first_competency_belongs_to_candidate(self):
        service, curriculum, _ = self._build()
        director = InterviewDirector(candidate_service, curriculum)
        seeded = self._seeded_competencies(curriculum)
        for session_int in range(20):
            state = self._start_fixed(service, director, session_int)
            assert state.currentCompetency in seeded

    def test_uncovered_curriculum_day_prioritization_after_first_question(self):
        _, curriculum, _ = self._build()
        director = InterviewDirector(candidate_service, curriculum)

        covered = CompetencyState(
            competency="Alpha", day=1, status="pending", attempts=1
        )
        uncovered = CompetencyState(
            competency="Zulu", day=2, status="pending", attempts=0
        )
        state = InterviewState(sessionId=UUID(int=9), candidateId=CANDIDATE_ID)
        state.competencies = [covered, uncovered]

        # Not the first selection (a day is already covered): the rotation
        # must not apply and the uncovered day wins over alphabetical order.
        assert director.select_next_competency(state) is uncovered

        # Once four distinct days are covered, alphabetical ordering resumes.
        state.competencies = [
            covered,
            CompetencyState(competency="Bravo", day=2, status="pending", attempts=1),
            CompetencyState(
                competency="Charlie", day=3, status="pending", attempts=1
            ),
            CompetencyState(competency="Delta", day=4, status="pending", attempts=1),
            CompetencyState(competency="Zulu", day=5, status="pending", attempts=0),
        ]
        selected = director.select_next_competency(state)
        assert selected is not None
        assert selected.competency == "Alpha"

    def test_single_competency_candidate(self):
        service, curriculum, _ = self._build()
        director = InterviewDirector(candidate_service, curriculum)
        state = InterviewState(sessionId=UUID(int=4), candidateId=CANDIDATE_ID)
        state.competencies = [
            CompetencyState(competency="Solo", day=1, status="pending")
        ]
        director.start_interview(state)
        assert state.currentCompetency == "Solo"
        selected = director.select_next_competency(state)
        assert selected is not None
        assert selected.competency == "Solo"


class TestNaturalCompletionBoundary:
    """The interview concludes at the first natural boundary (no follow-up
    required) once 8 questions across 4 curriculum days are covered, instead
    of continuing through every remaining eligible competency."""

    def _start(self, service: InterviewService):
        return service.start_interview(CANDIDATE_ID)

    def test_interview_concludes_at_natural_boundary_after_minimum(self):
        service, curriculum, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 8)

        for _ in range(8):
            resp = service.process_answer(resp.sessionId, _strong_answer(state, curriculum))

        assert resp.done is True
        final = sessions.get_session(resp.sessionId)
        assert final.completed is True
        assert final.interviewStage == "completed"
        assert service._questions_presented(final) == 8
        assert len(service._director.covered_curriculum_days(final)) == 8

    def test_eighth_answer_with_required_followup_does_not_complete(self):
        service, curriculum, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 8)

        for _ in range(7):
            resp = service.process_answer(resp.sessionId, _strong_answer(state, curriculum))

        # The 8th answer requires a follow-up, so the interview must not end.
        resp = service.process_answer(resp.sessionId, "I don't know.")

        final = sessions.get_session(resp.sessionId)
        assert resp.done is False
        assert final.completed is False
        assert resp.question
        assert resp.questionId == "Q9"
        # The 8th question plus the follow-up just presented.
        assert service._questions_presented(final) == 9
        assert len(service._director.covered_curriculum_days(final)) == 8

    def test_interview_completes_after_required_followup(self):
        service, curriculum, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 8)

        for _ in range(7):
            resp = service.process_answer(resp.sessionId, _strong_answer(state, curriculum))
        resp = service.process_answer(resp.sessionId, "I don't know.")
        assert resp.done is False

        # The follow-up is answered with no further follow-up required.
        resp = service.process_answer(resp.sessionId, _strong_answer(state, curriculum))

        assert resp.done is True
        final = sessions.get_session(resp.sessionId)
        assert final.completed is True
        assert service._questions_presented(final) == 9

    def test_interview_never_completes_before_8_questions(self):
        service, curriculum, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        # Four days are covered, but only four questions exist.
        _trim_competencies(state, 4)

        with pytest.raises(InsufficientQuestionError):
            for _ in range(6):
                service.process_answer(resp.sessionId, _strong_answer(state, curriculum))

        final = sessions.get_session(resp.sessionId)
        assert final.completed is False
        assert service._questions_presented(final) == 4
        assert len(service._director.covered_curriculum_days(final)) == 4

    def test_interview_never_completes_before_4_curriculum_days(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 3)
        for entry in state.competencies:
            entry.day = 1

        with pytest.raises(InsufficientQuestionError):
            for _ in range(12):
                service.process_answer(resp.sessionId, "I don't know.")

        final = sessions.get_session(resp.sessionId)
        assert final.completed is False
        assert service._questions_presented(final) == 9
        assert len(service._director.covered_curriculum_days(final)) == 1

    def test_existing_followup_cap_still_passes(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 4)
        session_id = resp.sessionId

        resp = None
        for _ in range(12):
            resp = service.process_answer(session_id, "I don't know.")

        assert resp.done is True
        final = sessions.get_session(session_id)
        assert final.metadata.totalFollowUps == 4 * MAX_FOLLOWUPS_PER_COMPETENCY
        for entry in final.competencies:
            assert entry.attempts == MAX_FOLLOWUPS_PER_COMPETENCY + 1

    def test_existing_duplicate_prevention_still_passes(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 4)

        for _ in range(12):
            service.process_answer(resp.sessionId, "I don't know.")

        asked = [
            m.message
            for m in sessions.get_session(resp.sessionId).conversationHistory
            if m.role == "interviewer"
        ]
        assert len(asked) == 12
        assert len(set(asked)) == 12

    def test_existing_question_rotation_still_passes(self):
        service, _, _ = _build_service()
        first_questions = {
            service.start_interview(CANDIDATE_ID).question for _ in range(20)
        }
        assert len(first_questions) > 1

    def test_existing_8_question_gate_still_passes(self):
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 2)
        session_id = resp.sessionId

        with pytest.raises(InsufficientQuestionError):
            for _ in range(12):
                service.process_answer(session_id, "I don't know.")

        final = sessions.get_session(session_id)
        assert final.completed is False
        assert service._questions_presented(final) == 6
        assert len(service._director.covered_curriculum_days(final)) == 2


class TestOptionCAdaptiveInterviewLength:
    """Option C — Adaptive Evidence-Driven Interview Length tests."""

    def _start(self, service: InterviewService):
        return service.start_interview(CANDIDATE_ID)

    def test_interview_continues_after_minimums_when_unassessed_competencies_remain(self):
        """Verify interview does not complete at 12 questions if remaining competencies need assessment."""
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 6)
        session_id = resp.sessionId

        # 11 answers after start = 12 questions presented
        for _ in range(11):
            resp = service.process_answer(session_id, "I don't know.")

        # At 12 questions, minimums are met but competencies 5 and 6 remain unassessed
        final = sessions.get_session(session_id)
        assert resp.done is False
        assert final.completed is False
        assert service._questions_presented(final) == 12

    def test_interview_completes_when_all_competencies_are_assessed(self):
        """Verify interview completes at natural boundary when all candidate competencies are assessed."""
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 4)
        session_id = resp.sessionId

        resp = None
        for _ in range(12):
            resp = service.process_answer(session_id, "I don't know.")

        # 4 competencies x 3 questions = 12 questions. All 4 competencies are exhausted.
        final = sessions.get_session(session_id)
        assert resp.done is True
        assert final.completed is True
        assert service._questions_presented(final) == 12

    def test_hard_ceiling_stops_interview_at_twenty_questions(self):
        """Verify interview stops at hard maximum of 20 questions presented."""
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)
        session_id = resp.sessionId

        resp = None
        for _ in range(20):
            if resp and resp.done:
                break
            resp = service.process_answer(session_id, "I don't know.")

        final = sessions.get_session(session_id)
        assert resp.done is True
        assert final.completed is True
        assert service._questions_presented(final) == MAX_QUESTIONS_TO_COMPLETE

    def test_strong_answers_produce_shorter_interview(self):
        """Verify a candidate with quick verified evidence completes as soon as competencies are verified."""
        class VerifyAllEngine(EvidenceEngine):
            def __init__(self, curriculum_service):
                super().__init__(curriculum_service=curriculum_service)

            def evaluate_answer(self, state, answer):
                return EvidenceEvaluation(
                    competency=state.currentCompetency or "technicalKnowledge",
                    evidenceScore=95,
                    technicalScore=95,
                    reasoningScore=95,
                    completenessScore=95,
                    communicationScore=95,
                    verified=True,
                    followUpRequired=False,
                    nextAction="VERIFY",
                    strengths=["complete mastery"],
                )

            def get_next_action(self, evaluation):
                return "NEXT_COMPETENCY"

            def update_competency(self, state, evaluation):
                for comp in state.competencies:
                    if comp.competency == evaluation.competency:
                        comp.status = "verified"
                        comp.evidenceScore = 95
                        comp.attempts += 1

            def update_interview_dna(self, state, evaluation):
                pass

            def calculate_hiring_confidence(self, state):
                pass

        service, curriculum_service, sessions = _build_service()
        service._evidence_engine = VerifyAllEngine(curriculum_service)

        resp = service.start_interview(CANDIDATE_ID)
        state = sessions.get_session(resp.sessionId)
        _trim_competencies(state, 8)
        session_id = resp.sessionId

        # 4 competencies verified on 1st question each = 4 questions < 8 minimum.
        # But minimum gate requires 8 questions / 4 days.
        # So after 4 verified, service asks remaining questions up to 8.
        # Once minimum 8 is reached, all are verified -> completes cleanly.
        resp = None
        for _ in range(8):
            if resp and resp.done:
                break
            resp = service.process_answer(session_id, "I demonstrate full mastery.")

        final = sessions.get_session(session_id)
        assert resp.done is True
        assert final.completed is True
        assert service._questions_presented(final) == 8

    def test_questions_presented_counts_only_actual_interviewer_questions(self):
        """Verify _questions_presented counts only interviewer messages in conversationHistory."""
        service, _, sessions = _build_service()
        resp = self._start(service)
        state = sessions.get_session(resp.sessionId)

        # Append fake system and candidate messages
        state.conversationHistory.append(ConversationMessage(role="candidate", message="Hello"))
        state.conversationHistory.append(ConversationMessage(role="system", message="System note"))

        assert service._questions_presented(state) == 1
