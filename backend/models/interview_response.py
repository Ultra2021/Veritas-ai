"""Pydantic response models for the InterviewService frontend contract.

The existing ``agents.interview_director.InterviewResponse`` only carries
``reply``/``question``/``currentCompetency``/``interviewStage``, which
cannot satisfy the frontend contract required by Module 7. This model is
the stable, JSON-serializable contract that Module 8 will expose directly
through FastAPI; it never leaks internal agent details.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.evidence import EvidenceEvaluation
from models.interview_state import CompetencyState, InterviewDNA, InterviewStage


class FeedbackData(BaseModel):
    """Structured feedback returned upon interview completion per technical-spec.md."""

    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    next: list[str] = Field(default_factory=list)


class InterviewTurnResponse(BaseModel):
    """Frontend & Technical Spec-facing response for every interview interaction.

    Returned by ``InterviewService.start_interview``,
    ``InterviewService.process_answer``, and ``POST /api/interview``.
    Exposes reply, done state, structured feedback, alongside current question,
    competencies, hiring confidence, and interview DNA.
    """

    model_config = ConfigDict(extra="forbid")

    sessionId: UUID | str
    questionId: str = ""
    question: str = ""
    reply: str = ""
    currentCompetency: str | None = None
    interviewStage: InterviewStage = "initialized"
    evidence: EvidenceEvaluation | None = None
    competencies: list[CompetencyState] = Field(default_factory=list)
    hiringConfidence: int | None = None
    interviewDNA: InterviewDNA | None = None
    done: bool = False
    feedback: FeedbackData | None = None

