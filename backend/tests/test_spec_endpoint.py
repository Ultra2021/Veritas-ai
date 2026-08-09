"""Tests validating the POST /api/interview spec endpoint per technical-spec.md."""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_spec_start_interview_with_string_session_id():
    """Verify POST /api/interview start flow with string sessionId and candidate object."""
    payload = {
        "sessionId": "abc-123",
        "candidate": {
            "member": {
                "id": "CAND-001",
                "name": "Sarah Johnson",
                "jobRole": "Senior Data Engineer",
            }
        },
    }
    resp = client.post("/api/interview", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sessionId"] == "abc-123"
    assert data["done"] is False
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0


def test_spec_conversation_turn_with_message():
    """Verify POST /api/interview turn flow with candidate message."""
    start_payload = {
        "sessionId": "abc-456",
        "candidateId": "CAND-001",
    }
    start_resp = client.post("/api/interview", json=start_payload)
    assert start_resp.status_code == 200

    turn_payload = {
        "sessionId": "abc-456",
        "message": (
            "I implemented HNSW vector indexing with cosine distance for dense retrieval, "
            "handling 10k queries/sec with sub-50ms latency."
        ),
    }
    turn_resp = client.post("/api/interview", json=turn_payload)
    assert turn_resp.status_code == 200
    data = turn_resp.json()
    assert data["done"] is False
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0


def test_spec_end_interview_returns_structured_feedback():
    """Verify feedback structure upon interview completion per technical-spec.md."""
    start_resp = client.post("/api/interview/start", json={"candidateId": "CAND-001"})
    session_id = start_resp.json()["sessionId"]

    end_resp = client.post("/api/interview/end", json={"sessionId": session_id})
    assert end_resp.status_code == 200
    data = end_resp.json()
    assert data["done"] is True
    assert "feedback" in data
    feedback = data["feedback"]
    assert isinstance(feedback["summary"], str)
    assert isinstance(feedback["strengths"], list)
    assert isinstance(feedback["gaps"], list)
    assert isinstance(feedback["next"], list)
