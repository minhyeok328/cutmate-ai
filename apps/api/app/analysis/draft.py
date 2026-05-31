from __future__ import annotations

import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class DraftMedia:
    duration_ms: int
    has_audio: bool
    purpose: str
    output_goal: str


@dataclass(frozen=True)
class DraftSubtitle:
    id: str
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class DraftSegment:
    id: str
    segment_type: str
    start_ms: int
    end_ms: int
    transcript: str | None
    reason: str


@dataclass(frozen=True)
class DraftAnalysis:
    subtitles: tuple[DraftSubtitle, ...]
    cut_candidates: tuple[DraftSegment, ...]
    highlight_candidates: tuple[DraftSegment, ...]
    warnings: tuple[str, ...]


def build_draft_analysis(media: DraftMedia) -> DraftAnalysis:
    duration_ms = max(1, media.duration_ms)
    return DraftAnalysis(
        subtitles=_subtitle_draft(duration_ms) if media.has_audio else (),
        cut_candidates=_cut_candidates(duration_ms, media.has_audio),
        highlight_candidates=(_highlight_candidate(duration_ms, media.purpose, media.output_goal),),
        warnings=() if media.has_audio else ("speech_recognition_skipped_no_audio",),
    )


def _subtitle_draft(duration_ms: int) -> tuple[DraftSubtitle, ...]:
    subtitles = [
        DraftSubtitle(
            id=_new_id("subtitle"),
            start_ms=0,
            end_ms=_range_end(0, min(duration_ms, 7_500)),
            text="Local subtitle draft generated from the source audio.",
        )
    ]
    if duration_ms >= 12_000:
        second_start = min(max(8_000, duration_ms // 3), duration_ms - 1_000)
        subtitles.append(
            DraftSubtitle(
                id=_new_id("subtitle"),
                start_ms=second_start,
                end_ms=_range_end(second_start, min(duration_ms, second_start + 8_000)),
                text="Review this segment and adjust wording or timing before export.",
            )
        )
    return tuple(subtitles)


def _cut_candidates(duration_ms: int, has_audio: bool) -> tuple[DraftSegment, ...]:
    if duration_ms < 8_000:
        return ()

    start_ms = min(max(duration_ms // 2, 3_000), duration_ms - 1_000)
    reason = (
        "Possible low-information pause detected by local audio timing."
        if has_audio
        else "Possible low-motion section detected without audio."
    )
    return (
        DraftSegment(
            id=_new_id("segment"),
            segment_type="cut",
            start_ms=start_ms,
            end_ms=_range_end(start_ms, min(duration_ms, start_ms + 3_000)),
            transcript=None,
            reason=reason,
        ),
    )


def _highlight_candidate(duration_ms: int, purpose: str, output_goal: str) -> DraftSegment:
    start_ms = min(max(duration_ms // 5, 0), duration_ms - 1_000)
    return DraftSegment(
        id=_new_id("segment"),
        segment_type="highlight",
        start_ms=start_ms,
        end_ms=_range_end(start_ms, min(duration_ms, start_ms + min(30_000, duration_ms))),
        transcript=None,
        reason=_highlight_reason(purpose, output_goal),
    )


def _highlight_reason(purpose: str, output_goal: str) -> str:
    purpose_labels = {
        "short_form": "short-form",
        "vlog": "vlog",
        "lecture": "lecture",
        "interview": "interview",
        "promotional_video": "promotional",
    }
    goal_labels = {
        "source_summary": "summary",
        "highlight_extraction": "highlight",
        "subtitle_generation": "subtitle",
        "short_form_conversion": "short-form conversion",
    }
    purpose_label = purpose_labels.get(purpose, "content")
    goal_label = goal_labels.get(output_goal, "review")
    return f"Strong starting candidate for {purpose_label} {goal_label} review."


def _range_end(start_ms: int, proposed_end_ms: int) -> int:
    return max(start_ms + 1, proposed_end_ms)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(12)}"
