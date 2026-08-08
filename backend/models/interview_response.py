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


class InterviewTurnResponse(BaseModel):
    """Frontend-facing response for every interview interaction.

    Returned by ``InterviewService.start_interview`` and
    ``InterviewService.process_answer``. Exposes the current question,
    question id, competency, interview stage, latest evidence, competency
    ledger, hiring confidence, interview DNA, and completion state so the
    Next.js frontend can render immediately.
    """

    model_config = ConfigDict(extra="forbid")

    sessionId: UUID
    questionId: str = ""
    question: str = ""
    currentCompetency: str | None = None
    interviewStage: InterviewStage = "initialized"
    evidence: EvidenceEvaluation | None = None
    competencies: list[CompetencyState] = Field(default_factory=list)
    hiringConfidence: int | None = None
    interviewDNA: InterviewDNA | None = None
    done: bool = False
