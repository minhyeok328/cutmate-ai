from __future__ import annotations

import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class DraftThumbnailCandidate:
    id: str
    image_asset_id: str
    timestamp_ms: int
    reason: str
    tags: tuple[str, ...]
    internal_score: float


def build_thumbnail_candidates(
    duration_ms: int,
    *,
    count: int = 3,
) -> tuple[DraftThumbnailCandidate, ...]:
    safe_duration = max(1, duration_ms)
    candidate_count = max(1, count)
    timestamps = _candidate_timestamps(safe_duration, candidate_count)
    return tuple(
        DraftThumbnailCandidate(
            id=_new_id("thumbnail"),
            image_asset_id=_new_id("asset"),
            timestamp_ms=timestamp_ms,
            reason=_reason_for_index(index),
            tags=_tags_for_index(index),
            internal_score=max(0.1, 0.92 - index * 0.08),
        )
        for index, timestamp_ms in enumerate(timestamps)
    )


def _candidate_timestamps(duration_ms: int, count: int) -> tuple[int, ...]:
    if count == 1:
        return (min(duration_ms - 1, duration_ms // 2),)
    return tuple(
        min(duration_ms - 1, max(0, round(duration_ms * (index + 1) / (count + 1))))
        for index in range(count)
    )


def _reason_for_index(index: int) -> str:
    reasons = (
        "Sharp representative frame near a likely highlight.",
        "Balanced frame with stable composition.",
        "Bright frame suitable for platform thumbnail preview.",
    )
    return reasons[index % len(reasons)]


def _tags_for_index(index: int) -> tuple[str, ...]:
    tags = (
        ("highlight_related", "sharp_frame"),
        ("stable_composition", "subject_centered"),
        ("bright_scene", "crop_safe"),
    )
    return tags[index % len(tags)]


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(12)}"
