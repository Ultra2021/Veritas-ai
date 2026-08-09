"""API tests for Module 8 (FastAPI endpoints)."""

import re
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from agents.evidence_engine import _STOPWORDS
from main import app
from services.curriculum_service import CurriculumService

client = TestClient(app)

CANDIDATE_ID = "CAND-001"

_CURRICULUM = CurriculumService(
    str(Path(__file__).resolve().parent.parent.parent / "curriculum.json")
)


def _strong_answer(competency: str) -> str:
    """Build an answer rich in the current competency's curriculum keywords."""
    keywords: list[str] = []
    for topic in _CURRICULUM.get_topics():
        if topic.title.lower() == (competency or "").lower():
            keywords = sorted(
                {
                    term
                    for objective in _CURRICULUM.get_day(topic.day).objectives
                    for term in re.findall(r"[a-z']+", objective.lower())
                    if len(term) > 4 and term not in _STOPWORDS
                }
            )
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


def _start(candidate_id: str = CANDIDATE_ID) -> dict:
    resp = client.post("/api/interview/start", json={"candidateId": candidate_id})
    assert resp.status_code == 200
    return resp.json()


def _drive_to_completion(session_id: str) -> None:
    for _ in range(30):
        state = client.get(f"/api/interview/{session_id}").json()
        answer = _strong_answer(state["currentCompetency"])
        resp = client.post(
            "/api/interview/answer", json={"sessionId": session_id, "answer": answer}
        )
        assert resp.status_code == 200
        if resp.json()["done"]:
            return
    raise AssertionError("interview did not complete within 30 turns")


# 1. Health check
def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


# 2. Start interview with a valid candidate
def test_start_interview_valid_candidate():
    data = _start()
    assert data["sessionId"]
    assert data["questionId"] == "Q1"
    assert data["question"]
    assert data["currentCompetency"]
    assert data["interviewStage"] == "interviewing"
    assert data["done"] is False


# 3. Start interview with an invalid candidate
def test_start_interview_invalid_candidate_returns_404():
    resp = client.post("/api/interview/start", json={"candidateId": "DOES-NOT-EXIST"})
    assert resp.status_code == 404


def test_start_interview_empty_candidate_returns_422():
    for bad in ("", "   "):
        resp = client.post("/api/interview/start", json={"candidateId": bad})
        assert resp.status_code == 422


# 4. Submit a valid answer
def test_submit_valid_answer_returns_next_turn():
    start = _start()
    session_id = start["sessionId"]

    resp = client.post(
        "/api/interview/answer", json={"sessionId": session_id, "answer": "I like computers."}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sessionId"] == session_id
    assert data["question"]
    assert data["evidence"] is not None
    assert data["hiringConfidence"] is not None
    assert isinstance(data["competencies"], list)
    assert "technicalKnowledge" in data["interviewDNA"] or "interviewDNA" in data
    assert data["done"] is False


# 5. Submit an empty answer
def test_submit_empty_answer_returns_422():
    start = _start()
    session_id = start["sessionId"]
    for bad in ("", "   "):
        resp = client.post(
            "/api/interview/answer", json={"sessionId": session_id, "answer": bad}
        )
        assert resp.status_code == 422


# 6. Submit an answer for an unknown session
def test_submit_answer_unknown_session_returns_404():
    resp = client.post(
        "/api/interview/answer", json={"sessionId": str(uuid4()), "answer": "Hello?"}
    )
    assert resp.status_code == 404


# 7. Submit an answer to a completed interview
def test_submit_answer_completed_interview_returns_409():
    start = _start()
    session_id = start["sessionId"]
    _drive_to_completion(session_id)

    resp = client.post(
        "/api/interview/answer", json={"sessionId": session_id, "answer": "hello"}
    )
    assert resp.status_code == 409


# 8. Get an existing interview state
def test_get_existing_state_returns_200():
    start = _start()
    session_id = start["sessionId"]

    resp = client.get(f"/api/interview/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sessionId"] == session_id
    assert data["currentQuestion"] == start["question"]
    assert isinstance(data["conversationHistory"], list)
    assert isinstance(data["competencies"], list)


# 9. Get an unknown interview state
def test_get_unknown_state_returns_404():
    resp = client.get(f"/api/interview/{uuid4()}")
    assert resp.status_code == 404


# 10. Response JSON serialization
def test_responses_are_json_serializable():
    start = _start()
    session_id = start["sessionId"]

    for resp in (
        client.get("/health"),
        client.get(f"/api/interview/{session_id}"),
        client.post(
            "/api/interview/answer", json={"sessionId": session_id, "answer": "I like computers."}
        ),
    ):
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        assert isinstance(resp.json(), dict)


# Extra: frontend contract and CORS
def test_start_response_exposes_stable_contract():
    data = _start()
    expected = {
        "sessionId",
        "questionId",
        "question",
        "currentCompetency",
        "interviewStage",
        "evidence",
        "competencies",
        "hiringConfidence",
        "interviewDNA",
        "done",
    }
    assert expected <= set(data)
    assert "conversationHistory" not in data
    assert "currentAnswer" not in data


def test_cors_allows_configured_frontend_origin():
    resp = client.options(
        "/api/interview/start",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_end_interview_early_returns_200():
    start_resp = client.post("/api/interview/start", json={"candidateId": "CAND-001"})
    assert start_resp.status_code == 200
    session_id = start_resp.json()["sessionId"]

    end_resp = client.post("/api/interview/end", json={"sessionId": session_id})
    assert end_resp.status_code == 200
    body = end_resp.json()
    assert body["done"] is True
    assert body["interviewStage"] == "completed"

