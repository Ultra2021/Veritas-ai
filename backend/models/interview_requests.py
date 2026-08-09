"""Pydantic request models for the Module 8 API layer.

API-layer validation only; no interview business logic lives here.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StartInterviewRequest(BaseModel):
    """Request body for ``POST /api/interview/start``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    candidateId: str = Field(
        min_length=1,
        description="Identifier of the candidate to interview.",
    )


class AnswerRequest(BaseModel):
    """Request body for ``POST /api/interview/answer``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    sessionId: UUID | str = Field(
        description="Identifier of the active interview session.",
    )
    answer: str = Field(
        min_length=1,
        description="The candidate's answer to the current question.",
    )


class EndInterviewRequest(BaseModel):
    """Request body for ``POST /api/interview/end``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    sessionId: UUID | str = Field(
        description="Identifier of the active interview session to terminate early.",
    )


class SpecInterviewRequest(BaseModel):
    """Unified request body for ``POST /api/interview`` per technical-spec.md."""

    model_config = ConfigDict(str_strip_whitespace=True)

    sessionId: UUID | str = Field(
        description="Session identifier (UUID or arbitrary string like 'abc-123').",
    )
    candidate: dict | str | None = Field(
        default=None,
        description="Candidate object or candidate ID for session initialization.",
    )
    candidateId: str | None = Field(
        default=None,
        description="Candidate identifier string.",
    )
    message: str | None = Field(
        default=None,
        description="Candidate answer message per technical spec.",
    )
    answer: str | None = Field(
        default=None,
        description="Candidate answer text.",
    )


