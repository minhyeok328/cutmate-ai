from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from math import gcd
from pathlib import Path
from typing import cast


class MediaProbeError(RuntimeError):
    """Raised when local metadata extraction fails with a user-safe reason."""


class MediaProbeToolUnavailableError(MediaProbeError):
    """Raised when ffprobe is unavailable in the active environment."""


@dataclass(frozen=True)
class VideoMetadata:
    duration_ms: int
    width: int
    height: int
    fps: float | None
    aspect_ratio: str
    has_audio: bool


def probe_video_metadata(path: Path, *, timeout_seconds: int = 20) -> VideoMetadata:
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path is None:
        raise MediaProbeToolUnavailableError("Required local media probe tool is unavailable.")

    try:
        result = subprocess.run(  # noqa: S603 - fixed executable path, shell disabled.
            [
                ffprobe_path,
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(path),
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        raise MediaProbeToolUnavailableError(
            "Required local media probe tool is unavailable."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise MediaProbeError("Media metadata extraction timed out.") from exc

    if result.returncode != 0:
        raise MediaProbeError("Uploaded media could not be parsed.")

    try:
        payload = cast(dict[str, object], json.loads(result.stdout))
    except json.JSONDecodeError as exc:
        raise MediaProbeError("Uploaded media metadata could not be parsed.") from exc

    streams_value = payload.get("streams")
    if not isinstance(streams_value, list):
        raise MediaProbeError("Uploaded media does not contain readable streams.")
    streams = cast(list[object], streams_value)

    video_stream = _first_stream(streams, "video")
    if video_stream is None:
        raise MediaProbeError("Uploaded media does not contain a readable video stream.")

    width = _positive_int(video_stream.get("width"))
    height = _positive_int(video_stream.get("height"))
    if width is None or height is None:
        raise MediaProbeError("Uploaded media video dimensions are missing.")

    duration_ms = _duration_ms(video_stream.get("duration"))
    if duration_ms is None:
        media_format_value = payload.get("format")
        if isinstance(media_format_value, dict):
            media_format = cast(dict[str, object], media_format_value)
            duration_ms = _duration_ms(media_format.get("duration"))
    if duration_ms is None:
        raise MediaProbeError("Uploaded media duration is missing.")

    return VideoMetadata(
        duration_ms=duration_ms,
        width=width,
        height=height,
        fps=_fps(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate")),
        aspect_ratio=_aspect_ratio(width, height),
        has_audio=_first_stream(streams, "audio") is not None,
    )


def _first_stream(streams: list[object], codec_type: str) -> dict[str, object] | None:
    for stream in streams:
        if isinstance(stream, dict):
            stream_data = cast(dict[str, object], stream)
            if stream_data.get("codec_type") == codec_type:
                return stream_data
    return None


def _positive_int(value: object) -> int | None:
    if isinstance(value, int) and value > 0:
        return value
    return None


def _duration_ms(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    try:
        seconds = float(value)
    except ValueError:
        return None
    if seconds < 0:
        return None
    return round(seconds * 1000)


def _fps(value: object) -> float | None:
    if not isinstance(value, str) or value in {"", "0/0"}:
        return None
    numerator_text, separator, denominator_text = value.partition("/")
    if separator == "":
        try:
            fps = float(value)
        except ValueError:
            return None
        return fps if fps > 0 else None
    try:
        numerator = float(numerator_text)
        denominator = float(denominator_text)
    except ValueError:
        return None
    if denominator <= 0:
        return None
    fps = numerator / denominator
    return fps if fps > 0 else None


def _aspect_ratio(width: int, height: int) -> str:
    divisor = gcd(width, height)
    return f"{width // divisor}:{height // divisor}"
