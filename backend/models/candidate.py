"""Pydantic models mirroring the candidates.json dataset exactly."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Member(BaseModel):
    """Profile details of a candidate's membership."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    jobRole: str
    yearsExperience: int
    education: str
    status: str


class Mission(BaseModel):
    """A single curriculum mission a candidate attempted."""

    model_config = ConfigDict(extra="forbid")

    day: int
    title: str
    passed: bool | None = None
    attempts: int | None = None
    skipped: bool | None = None


class Signals(BaseModel):
    """Aggregated engagement signals for a candidate."""

    model_config = ConfigDict(extra="forbid")

    commitDays: int
    missionsCompleted: int
    missionsFirstTry: int


class CandidateProfile(BaseModel):
    """Top-level record for one candidate in candidates.json."""

    model_config = ConfigDict(extra="forbid")

    member: Member
    missions: list[Mission]
    signals: Signals


class InterviewTopic(BaseModel):
    """A curriculum mission normalized for interview consumption.

    Derived from a ``Mission``: ``status`` maps ``passed``/``skipped``
    into a single label and ``attempts`` defaults to 0 for skipped
    missions. No fields outside the dataset are used.
    """

    model_config = ConfigDict(extra="forbid")

    day: int
    title: str
    status: Literal["passed", "failed", "skipped"]
    attempts: int


class CandidateSummary(BaseModel):
    """Frontend-ready profile for the Candidate Selection page.

    Carries only dataset-derived information: candidate identity,
    learning signals, and partitioned topic lists. Future modules
    consume this model instead of the raw candidate JSON.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    jobRole: str
    yearsExperience: int
    education: str
    status: str
    missionsCompleted: int
    firstAttemptSuccessRate: float
    commitDays: int
    completedTopics: list[InterviewTopic]
    failedTopics: list[InterviewTopic]
    skippedTopics: list[InterviewTopic]
