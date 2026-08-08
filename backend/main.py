"""Veritas AI Backend entry point.

Evidence-Driven AI Interview Platform Backend.

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import FRONTEND_ORIGIN
from routes import health, interview
from services.candidate_service import CandidateNotFoundError
from services.interview_service import (
    EmptyAnswerError,
    InterviewCompletedError,
    InterviewServiceError,
    MissingCurrentQuestionError,
)
from services.session_service import SessionNotFoundError

app = FastAPI(
    title="Veritas AI Backend",
    version="1.0.0",
    description="Evidence-Driven AI Interview Platform Backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error(status_code: int, message: str) -> JSONResponse:
    """Build a JSON error response without leaking internal details."""
    return JSONResponse(status_code=status_code, content={"detail": message})


@app.exception_handler(CandidateNotFoundError)
async def candidate_not_found_handler(
    request: Request, exc: CandidateNotFoundError
) -> JSONResponse:
    return _error(404, str(exc))


@app.exception_handler(SessionNotFoundError)
async def session_not_found_handler(
    request: Request, exc: SessionNotFoundError
) -> JSONResponse:
    return _error(404, str(exc))


@app.exception_handler(InterviewCompletedError)
async def interview_completed_handler(
    request: Request, exc: InterviewCompletedError
) -> JSONResponse:
    return _error(409, str(exc))


@app.exception_handler(EmptyAnswerError)
async def empty_answer_handler(
    request: Request, exc: EmptyAnswerError
) -> JSONResponse:
    return _error(422, str(exc))


@app.exception_handler(MissingCurrentQuestionError)
async def missing_current_question_handler(
    request: Request, exc: MissingCurrentQuestionError
) -> JSONResponse:
    return _error(400, str(exc))


@app.exception_handler(InterviewServiceError)
async def interview_service_error_handler(
    request: Request, exc: InterviewServiceError
) -> JSONResponse:
    return _error(500, "Internal server error.")


app.include_router(health.router)
app.include_router(interview.router)
