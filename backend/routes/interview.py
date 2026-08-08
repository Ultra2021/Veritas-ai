"""Module 8: FastAPI routes exposing the existing InterviewService.

The API layer contains NO interview business logic. Handlers validate the
HTTP request via Pydantic request models, delegate to the shared
``InterviewService`` (or ``SessionService`` for state recovery), and
serialize the existing Pydantic response models.

Composition root: the shared ``InterviewService`` and ``SessionService``
are built once at import time and handed out through FastAPI dependencies
so every request talks to the same in-memory session store.
"""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends

import config
import services.candidate_service as candidate_service
from agents.evidence_engine import (
    EvidenceEngine,
    GeminiEvidenceEvaluator,
    LLMEvidenceEvaluator,
)
from agents.interview_director import InterviewDirector
from agents.question_bank import GeminiQuestionBank, LLMQuestionBank
from models.interview_requests import AnswerRequest, StartInterviewRequest
from models.interview_response import InterviewTurnResponse
from models.interview_state import InterviewState
from services.curriculum_service import CurriculumService
from services.interview_service import InterviewService
from services.llm_provider import GroqProvider, LLMProvider
from services.session_service import SessionService

router = APIRouter(prefix="/api/interview", tags=["Interview"])

_CURRICULUM_PATH = Path(__file__).resolve().parent.parent.parent / "curriculum.json"


def _build_provider() -> LLMProvider | None:
    """Build the active LLM provider from configuration, if any.

    A single provider instance is shared by both the question bank and
    the evidence evaluator so the Groq client is created exactly once.
    ``LLM_PROVIDER=gemini`` keeps the existing Gemini strategy, and any
    other value falls back to the deterministic agents.
    """
    if config.LLM_PROVIDER == "groq":
        return GroqProvider(api_key=config.GROQ_API_KEY, model_name=config.GROQ_MODEL)
    return None


def _build_question_bank(
    curriculum_service: CurriculumService,
    provider: LLMProvider | None,
):
    """Compose the QuestionBank strategy for the configured provider."""
    if provider is not None:
        return LLMQuestionBank(
            provider=provider,
            curriculum_service=curriculum_service,
        )
    if config.GEMINI_API_KEY:
        return GeminiQuestionBank(api_key=config.GEMINI_API_KEY)
    return None


def _build_evaluator(provider: LLMProvider | None):
    """Compose the EvidenceEvaluator strategy for the configured provider."""
    if provider is not None:
        return LLMEvidenceEvaluator(provider=provider)
    if config.GEMINI_API_KEY:
        return GeminiEvidenceEvaluator(api_key=config.GEMINI_API_KEY)
    return None


def _build_service(session_service: SessionService) -> InterviewService:
    """Compose the InterviewService with its existing collaborators."""
    curriculum_service = CurriculumService(str(_CURRICULUM_PATH))
    provider = _build_provider()
    director = InterviewDirector(
        candidate_service,
        curriculum_service,
        question_bank=_build_question_bank(curriculum_service, provider),
    )
    evidence_engine = EvidenceEngine(
        curriculum_service=curriculum_service,
        evaluator=_build_evaluator(provider),
    )
    return InterviewService(
        candidate_service=candidate_service,
        curriculum_service=curriculum_service,
        session_service=session_service,
        director=director,
        evidence_engine=evidence_engine,
    )


_session_service = SessionService()
interview_service = _build_service(_session_service)


def get_interview_service() -> InterviewService:
    """FastAPI dependency returning the shared InterviewService."""
    return interview_service


def get_session_service() -> SessionService:
    """FastAPI dependency returning the shared SessionService."""
    return _session_service


@router.post(
    "/start",
    response_model=InterviewTurnResponse,
    summary="Start an interview",
    description=(
        "Validates the candidate and begins a new interview session. Returns the "
        "new session id and the first interview question so the frontend can "
        "render immediately."
    ),
    responses={404: {"description": "Candidate not found"}},
)
def start_interview(
    payload: StartInterviewRequest,
    service: InterviewService = Depends(get_interview_service),
) -> InterviewTurnResponse:
    """Start a new interview for the given candidate."""
    return service.start_interview(payload.candidateId)


@router.post(
    "/answer",
    response_model=InterviewTurnResponse,
    summary="Process a candidate answer",
    description=(
        "Evaluates the candidate's answer and advances the interview: a follow-up "
        "question, the next competency's question, or a completion response."
    ),
    responses={
        400: {"description": "Interview in an invalid state"},
        404: {"description": "Session not found"},
        409: {"description": "Interview already completed"},
        422: {"description": "Empty answer"},
    },
)
def process_answer(
    payload: AnswerRequest,
    service: InterviewService = Depends(get_interview_service),
) -> InterviewTurnResponse:
    """Evaluate the candidate's answer and return the next turn."""
    return service.process_answer(payload.sessionId, payload.answer)


@router.get(
    "/{session_id}",
    response_model=InterviewState,
    summary="Get interview state",
    description=(
        "Returns the current InterviewState for a session. Useful for reconnecting "
        "to an interview, refreshing the browser, debugging, and frontend state "
        "recovery."
    ),
    responses={404: {"description": "Session not found"}},
)
def get_interview_state(
    session_id: UUID,
    session_service: SessionService = Depends(get_session_service),
) -> InterviewState:
    """Return the stored InterviewState for a session."""
    return session_service.get_session(session_id)
