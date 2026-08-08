"""Pydantic models for evidence evaluation output (Evidence Engine)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

NextAction = Literal["FOLLOW_UP", "VERIFY", "NEXT_COMPETENCY"]


class EvidenceEvaluation(BaseModel):
    """Structured outcome of evaluating a single candidate answer.

    Frontend contract for the Evidence Sidebar and future Interview
    Replay. Carries the question it evaluated (``questionId``/``question``)
    so each evaluation can be traced back to the exact question asked.
    """

    model_config = ConfigDict(extra="forbid")

    competency: str
    evidenceScore: int = Field(ge=0, le=100)
    technicalScore: int = Field(ge=0, le=100)
    reasoningScore: int = Field(ge=0, le=100)
    completenessScore: int = Field(ge=0, le=100)
    communicationScore: int = Field(ge=0, le=100)
    verified: bool = False
    followUpRequired: bool = False
    nextAction: NextAction = "FOLLOW_UP"
    reason: str = ""
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    questionId: str = ""
    question: str = ""
