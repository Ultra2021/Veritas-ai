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

    sessionId: UUID = Field(
        description="Identifier of the active interview session.",
    )
    answer: str = Field(
        min_length=1,
        description="The candidate's answer to the current question.",
    )
