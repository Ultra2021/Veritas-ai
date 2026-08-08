"""Service for loading and querying candidate data from candidates.json.

Provides validated candidate data to future modules (interview logic,
evidence engine, etc.). No interview or AI logic lives here.
"""

import json
from pathlib import Path

from pydantic import ValidationError

from models.candidate import CandidateProfile, CandidateSummary, InterviewTopic, Mission

DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "candidates.json"


class CandidateDataError(Exception):
    """Raised when candidate data cannot be loaded or validated."""


class CandidateNotFoundError(ValueError):
    """Raised when a candidate_id does not exist in the dataset."""


_candidates: list[CandidateProfile] | None = None


def _read_candidates(file_path: Path) -> list[CandidateProfile]:
    try:
        with open(file_path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError as exc:
        raise CandidateDataError(f"Candidate data file not found: {file_path}") from exc
    except json.JSONDecodeError as exc:
        raise CandidateDataError(
            f"Candidate data file is not valid JSON: {exc}"
        ) from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), list):
        raise CandidateDataError("Candidate data file must contain a 'candidates' list.")

    validated: list[CandidateProfile] = []
    for index, record in enumerate(payload["candidates"]):
        try:
            validated.append(CandidateProfile.model_validate(record))
        except ValidationError as exc:
            raise CandidateDataError(
                f"Invalid candidate record at index {index}: {exc}"
            ) from exc
    return validated


def _get_candidates() -> list[CandidateProfile]:
    if _candidates is None:
        return _read_candidates(DEFAULT_DATA_PATH)
    return _candidates


def _get_candidate(candidate_id: str) -> CandidateProfile:
    for candidate in _get_candidates():
        if candidate.member.id == candidate_id:
            return candidate
    raise CandidateNotFoundError(f"Candidate not found: {candidate_id}")


def load_candidates(file_path: str | Path | None = None) -> list[CandidateProfile]:
    """Load and validate candidates from disk.

    Replaces the in-memory cache with a fresh copy. Uses the default
    dataset path unless ``file_path`` is provided.
    """
    global _candidates
    path = Path(file_path) if file_path else DEFAULT_DATA_PATH
    _candidates = _read_candidates(path)
    return _candidates


def get_candidate(candidate_id: str) -> CandidateProfile:
    """Return the validated profile for a single candidate."""
    return _get_candidate(candidate_id)


def _to_interview_topic(mission: Mission) -> InterviewTopic:
    """Normalize a dataset mission into an interview topic."""
    if mission.skipped:
        status: str = "skipped"
        attempts: int = 0
    elif mission.passed:
        status = "passed"
        attempts = mission.attempts or 0
    else:
        status = "failed"
        attempts = mission.attempts or 0
    return InterviewTopic(day=mission.day, title=mission.title, status=status, attempts=attempts)


def get_interview_topics(candidate_id: str) -> list[InterviewTopic]:
    """Transform a candidate's curriculum into interview-ready topics.

    Returns every mission as ``(day, title, status, attempts)`` sorted by
    day, where ``status`` is ``passed``, ``failed``, or ``skipped`` and
    ``attempts`` is 0 for skipped missions. Consumed by the Interview
    Director in the next module; this is data transformation only.
    """
    candidate = _get_candidate(candidate_id)
    topics = [_to_interview_topic(mission) for mission in candidate.missions]
    return sorted(topics, key=lambda topic: topic.day)


def get_completed_missions(candidate_id: str) -> list[Mission]:
    """Return missions the candidate passed."""
    candidate = _get_candidate(candidate_id)
    return [mission for mission in candidate.missions if mission.passed]


def get_failed_missions(candidate_id: str) -> list[Mission]:
    """Return missions the candidate attempted but did not pass."""
    candidate = _get_candidate(candidate_id)
    return [mission for mission in candidate.missions if mission.passed is False]


def get_skipped_missions(candidate_id: str) -> list[Mission]:
    """Return missions the candidate skipped."""
    candidate = _get_candidate(candidate_id)
    return [mission for mission in candidate.missions if mission.skipped]


def get_candidate_summary(candidate_id: str) -> CandidateSummary:
    """Return a normalized, interview-ready profile for a candidate.

    Builds a ``CandidateSummary`` from the dataset's member and signals
    fields so the Candidate Selection page can render directly. The
    first-attempt success rate is derived as ``missionsFirstTry`` over
    ``missionsCompleted`` (0.0 when no missions are completed). Future
    modules never need to parse the raw candidate JSON.
    """
    candidate = _get_candidate(candidate_id)
    signals = candidate.signals
    topics = get_interview_topics(candidate_id)

    if signals.missionsCompleted:
        first_attempt_rate = round(
            signals.missionsFirstTry / signals.missionsCompleted, 2
        )
    else:
        first_attempt_rate = 0.0

    return CandidateSummary(
        name=candidate.member.name,
        jobRole=candidate.member.jobRole,
        yearsExperience=candidate.member.yearsExperience,
        education=candidate.member.education,
        status=candidate.member.status,
        missionsCompleted=signals.missionsCompleted,
        firstAttemptSuccessRate=first_attempt_rate,
        commitDays=signals.commitDays,
        completedTopics=[topic for topic in topics if topic.status == "passed"],
        failedTopics=[topic for topic in topics if topic.status == "failed"],
        skippedTopics=[topic for topic in topics if topic.status == "skipped"],
    )
