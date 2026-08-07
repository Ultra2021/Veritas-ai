"""Pydantic models for interview session state management.

``InterviewState`` is the single source of truth shared by the Interview
Director, the Evidence Engine, the API layer, and the Next.js frontend.
No agent maintains its own memory; all interview data flows through this
model.
"""

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ConversationRole = Literal["system", "interviewer", "candidate", "evaluator"]
CompetencyStatus = Literal["pending", "in_progress", "verified", "needs_followup"]
InterviewStage = Literal["initialized", "interviewing", "evaluating", "completed"]


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class ConversationMessage(BaseModel):
    """A single message exchanged during a live interview."""

    model_config = ConfigDict(extra="forbid")

    role: ConversationRole
    message: str
    timestamp: datetime = Field(default_factory=utc_now)


class CompetencyState(BaseModel):
    """Live tracking state for a single competency.

    The single competency ledger entry shared by the Interview Director,
    Evidence Engine, Hiring Report, and frontend Evidence Sidebar.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    competency: str
    status: CompetencyStatus = "pending"
    evidenceScore: int = Field(default=0, ge=0, le=100)
    attempts: int = Field(default=0, ge=0)
    notes: str = ""


class InterviewDNA(BaseModel):
    """Five-dimension skill profile for a candidate, scored 0-100."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    technicalKnowledge: int = Field(default=0, ge=0, le=100)
    communication: int = Field(default=0, ge=0, le=100)
    problemSolving: int = Field(default=0, ge=0, le=100)
    leadership: int = Field(default=0, ge=0, le=100)
    learningAbility: int = Field(default=0, ge=0, le=100)


class InterviewMetadata(BaseModel):
    """Operational metadata powering analytics, dashboards, and replay."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    startedAt: datetime = Field(default_factory=utc_now)
    lastInteractionAt: datetime = Field(default_factory=utc_now)
    totalQuestionsAsked: int = Field(default=0, ge=0)
    totalFollowUps: int = Field(default=0, ge=0)
    interviewDurationSeconds: int = Field(default=0, ge=0)


class InterviewState(BaseModel):
    """Shared memory for a single live interview session.

    Read and written exclusively through ``SessionService``. Holds the
    current question, live transcript, competency ledger, hiring
    confidence, interview DNA, and stage so the frontend can render the
    interview and future modules can coordinate its lifecycle without
    maintaining their own state.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    sessionId: UUID
    candidateId: str
    currentCompetency: str | None = None
    currentQuestionId: str = ""
    currentQuestion: str = ""
    currentAnswer: str | None = None
    conversationHistory: list[ConversationMessage] = Field(default_factory=list)
    competencies: list[CompetencyState] = Field(default_factory=list)
    hiringConfidence: int | None = Field(default=None, ge=0, le=100)
    interviewDNA: InterviewDNA = Field(default_factory=InterviewDNA)
    interviewStage: InterviewStage = "initialized"
    metadata: InterviewMetadata = Field(default_factory=InterviewMetadata)
    completed: bool = False
    createdAt: datetime = Field(default_factory=utc_now)
    updatedAt: datetime = Field(default_factory=utc_now)
