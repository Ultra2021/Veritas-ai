"""Service for loading and querying curriculum data from curriculum.json.

Provides validated curriculum data to future modules (Interview
Director, Evidence Engine, frontend). No interview or AI logic lives
here; this is a data access layer only.
"""

import json
from pathlib import Path

from pydantic import ValidationError

from models.curriculum import (
    Curriculum,
    CurriculumDay,
    CurriculumModule,
    CurriculumSummary,
    CurriculumTopic,
)


class CurriculumDataError(Exception):
    """Raised when curriculum data cannot be loaded or validated."""


class CurriculumModuleNotFoundError(ValueError):
    """Raised when a module id does not exist in the curriculum."""


class CurriculumDayNotFoundError(ValueError):
    """Raised when a day number does not exist in the curriculum."""


class CurriculumService:
    """Provides validated access to the curriculum.json dataset.

    Loads the dataset lazily on first use and caches it in memory, so
    callers can query modules, days, objectives, tools, and topics
    without re-reading the file.
    """

    def __init__(self, data_path: str) -> None:
        self._data_path = Path(data_path)
        self._curriculum: Curriculum | None = None

    def load_curriculum(self) -> Curriculum:
        """Load and validate curriculum.json, returning the root model.

        Replaces the in-memory cache with a fresh copy.
        """
        try:
            with open(self._data_path, encoding="utf-8") as handle:
                payload = json.load(handle)
        except FileNotFoundError as exc:
            raise CurriculumDataError(
                f"Curriculum data file not found: {self._data_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise CurriculumDataError(
                f"Curriculum data file is not valid JSON: {exc}"
            ) from exc

        try:
            self._curriculum = Curriculum.model_validate(payload)
        except ValidationError as exc:
            raise CurriculumDataError(f"Invalid curriculum data: {exc}") from exc
        return self._curriculum

    def _get_curriculum(self) -> Curriculum:
        if self._curriculum is None:
            self.load_curriculum()
        return self._curriculum

    def get_all_modules(self) -> list[CurriculumModule]:
        """Return all curriculum modules."""
        return self._get_curriculum().modules

    def get_module(self, module_id: int) -> CurriculumModule:
        """Return a single module by its number.

        Raises ``CurriculumModuleNotFoundError`` if the module does not
        exist.
        """
        for module in self._get_curriculum().modules:
            if module.n == module_id:
                return module
        raise CurriculumModuleNotFoundError(f"Module not found: {module_id}")

    def _get_day(self, day_number: int) -> CurriculumDay:
        for day in self._get_curriculum().days:
            if day.day == day_number:
                return day
        raise CurriculumDayNotFoundError(f"Curriculum day not found: {day_number}")

    def get_day(self, day_number: int) -> CurriculumDay:
        """Return the curriculum entry for a specific day."""
        return self._get_day(day_number)

    def get_learning_objectives(self, day_number: int) -> list[str]:
        """Return all learning objectives for a day."""
        return self._get_day(day_number).objectives

    def get_tools(self, day_number: int) -> list[str]:
        """Return the tools or technologies introduced on a day."""
        return self._get_day(day_number).tools

    def _module_for_day(self, day_number: int) -> CurriculumModule | None:
        for module in self._get_curriculum().modules:
            start, end = module.days[0], module.days[-1]
            if start <= day_number <= end:
                return module
        return None

    def get_topics(self) -> list[CurriculumTopic]:
        """Return a simplified list of interviewable topics.

        Each topic is ``(day, title, module)`` using only curriculum
        fields, ready for the Interview Director.
        """
        curriculum = self._get_curriculum()
        topics: list[CurriculumTopic] = []
        for day in sorted(curriculum.days, key=lambda entry: entry.day):
            module = self._module_for_day(day.day)
            topics.append(
                CurriculumTopic(
                    day=day.day,
                    title=day.title,
                    module=module.title if module else "",
                )
            )
        return topics

    def get_topic_by_day(self, day_number: int) -> CurriculumTopic:
        """Return the interview topic associated with a curriculum day."""
        day = self._get_day(day_number)
        module = self._module_for_day(day_number)
        return CurriculumTopic(
            day=day.day,
            title=day.title,
            module=module.title if module else "",
        )

    def get_curriculum_summary(self) -> CurriculumSummary:
        """Return a lightweight curriculum summary suitable for AI prompts."""
        curriculum = self._get_curriculum()
        return CurriculumSummary(
            totalModules=len(curriculum.modules),
            totalDays=len(curriculum.days),
            topics=self.get_topics(),
        )
