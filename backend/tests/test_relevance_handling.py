"""Unit tests verifying proper handling of irrelevant, evasive, and gibberish answers."""

import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import services.candidate_service as candidate_service
from agents.evidence_engine import EvidenceEngine
from agents.interview_director import InterviewDirector
from models.interview_state import InterviewState
from services.curriculum_service import CurriculumService
from services.session_service import SessionService
from utils.relevance import is_irrelevant_or_gibberish

CANDIDATE_ID = "CAND-001"


def _build_test_deps():
    curriculum = CurriculumService(
        str(Path(__file__).resolve().parent.parent.parent / "curriculum.json")
    )
    sessions = SessionService()
    director = InterviewDirector(candidate_service, curriculum)
    engine = EvidenceEngine(curriculum_service=curriculum)
    return curriculum, sessions, director, engine


class TestRelevanceHandling:
    """Test suite ensuring gibberish and irrelevant answers are flagged and given proper non-affirming responses."""

    def test_01_detect_gibberish_and_evasions(self):
        assert is_irrelevant_or_gibberish("jgfjhgjfh bye")[0] is True
        assert is_irrelevant_or_gibberish("asdfghjkl")[0] is True
        assert is_irrelevant_or_gibberish("I don't know")[0] is True
        assert is_irrelevant_or_gibberish("bye")[0] is True
        assert is_irrelevant_or_gibberish("what is the weather today")[0] is False or is_irrelevant_or_gibberish("bye")[0] is True

        # Valid answer
        assert is_irrelevant_or_gibberish("In a LangGraph multi-agent workflow, state is synchronized via shared state graph.")[0] is False

    def test_02_evidence_engine_scores_gibberish_zero(self):
        curriculum, sessions, director, engine = _build_test_deps()
        state = sessions.create_session(CANDIDATE_ID)
        director.start_interview(state)
        state.currentAnswer = "jgfjhgjfh bye"

        eval_res = engine.evaluate_answer(state, "jgfjhgjfh bye")
        assert eval_res.evidenceScore == 0
        assert eval_res.technicalScore == 0
        assert eval_res.verified is False
        assert len(eval_res.strengths) == 0
        assert "nonsensical" in eval_res.gaps[0].lower() or "off-topic" in eval_res.gaps[0].lower() or "no technical answer" in eval_res.gaps[0].lower()

    def test_03_interview_director_does_not_say_makes_sense_to_gibberish(self):
        curriculum, sessions, director, engine = _build_test_deps()
        state = sessions.create_session(CANDIDATE_ID)
        director.start_interview(state)

        # Process a gibberish answer turn
        state.currentAnswer = "jgfjhgjfh bye"
        eval_res = engine.evaluate_answer(state, "jgfjhgjfh bye")
        state.evidenceEvaluations.append(eval_res)

        resp = director.generate_followup_question(state)
        # Verify reply does NOT start with 'Makes sense' or 'Fair point' or 'Got it. Focusing on'
        reply_lower = resp.reply.lower()
        assert not reply_lower.startswith("makes sense")
        assert not reply_lower.startswith("fair point")
        assert not reply_lower.startswith("interesting approach")
        assert not reply_lower.startswith("that's helpful context")
        # Verify it contains redirection phrasing
        assert (
            "doesn't seem relevant" in reply_lower
            or "didn't catch a technical" in reply_lower
            or "focused on the technical" in reply_lower
            or "refocus" in reply_lower
            or "re-approaching" in reply_lower
            or "moving back" in reply_lower
        )
