"""Pydantic models mirroring the curriculum.json dataset exactly."""

from pydantic import BaseModel, ConfigDict


class CurriculumModule(BaseModel):
    """A curriculum module spanning a range of days."""

    model_config = ConfigDict(extra="forbid")

    n: int
    title: str
    days: list[int]


class CurriculumDay(BaseModel):
    """A single curriculum day with its objectives and tools."""

    model_config = ConfigDict(extra="forbid")

    day: int
    title: str
    type: str
    tools: list[str]
    objectives: list[str]


class Curriculum(BaseModel):
    """Root curriculum model."""

    model_config = ConfigDict(extra="forbid")

    cohort: str
    modules: list[CurriculumModule]
    days: list[CurriculumDay]


class CurriculumTopic(BaseModel):
    """An interviewable topic derived from a curriculum day."""

    model_config = ConfigDict(extra="forbid")

    day: int
    title: str
    module: str


class CurriculumSummary(BaseModel):
    """Lightweight curriculum summary suitable for AI prompts."""

    model_config = ConfigDict(extra="forbid")

    totalModules: int
    totalDays: int
    topics: list[CurriculumTopic]
