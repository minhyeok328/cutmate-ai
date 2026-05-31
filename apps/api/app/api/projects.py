from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.analysis.draft import DraftMedia, build_draft_analysis
from app.core.config import ANALYSIS_MODES, MAX_UPLOAD_BYTES, get_settings
from app.core.paths import resolve_workspace_path
from app.db.connection import connect
from app.db.repositories import (
    DEFAULT_LOCAL_USER_ID,
    AnalysisJob,
    AnalysisJobCreate,
    AnalysisJobRepository,
    AnalysisJobUpdate,
    AnalysisResult,
    AnalysisResultRepository,
    ExportJob,
    ExportJobCreate,
    ExportJobRepository,
    Subtitle,
    SubtitleCreate,
    ThumbnailCandidate,
    ThumbnailCandidateCreate,
    ThumbnailCandidateRepository,
    VideoProject,
    VideoProjectCreate,
    VideoProjectRepository,
    VideoSegment,
    VideoSegmentCreate,
    utc_now,
)
from app.db.schema import initialize_schema
from app.media.probe import (
    MediaProbeError,
    MediaProbeToolUnavailableError,
    VideoMetadata,
    probe_video_metadata,
)
from app.media.storage import (
    LocalMediaStorage,
    StoredSourceUpload,
    UnsupportedMediaExtensionError,
    UploadTooLargeError,
)
from app.thumbnails.draft import build_thumbnail_candidates

router = APIRouter(prefix="/projects", tags=["projects"])

CONTENT_PURPOSES = frozenset({"short_form", "vlog", "lecture", "interview", "promotional_video"})
OUTPUT_GOALS = frozenset(
    {"source_summary", "highlight_extraction", "subtitle_generation", "short_form_conversion"}
)
SAFE_DISPLAY_NAME_RE = re.compile(r"[\x00-\x1f\x7f]")


class SubtitleUpdateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)


class SegmentUpdateRequest(BaseModel):
    status: Literal["pending", "accepted", "rejected", "modified"]


class ThumbnailUpdateRequest(BaseModel):
    status: Literal["pending", "selected", "rejected"]


class DirectFrameRequest(BaseModel):
    timestamp_ms: int = Field(ge=0)


class ExportCreateRequest(BaseModel):
    aspect_ratio: Literal["original", "9:16", "1:1"]
    resolution: str = Field(min_length=3, max_length=24)
    include_subtitles: bool = False
    include_thumbnail: bool = False
    crop_mode: Literal["center", "manual"] = "center"


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    file: Annotated[UploadFile, File()],
    purpose: Annotated[str, Form()],
    output_goal: Annotated[str, Form()],
    title: Annotated[str | None, Form()] = None,
    analysis_mode: Annotated[str, Form()] = "standard",
) -> dict[str, object]:
    _validate_form_choice("purpose", purpose, CONTENT_PURPOSES)
    _validate_form_choice("output_goal", output_goal, OUTPUT_GOALS)
    _validate_form_choice("analysis_mode", analysis_mode, ANALYSIS_MODES)

    settings = get_settings()
    project_id = _new_id("project")
    job_id = _new_id("analysis_job")
    source_file_name = _safe_display_filename(file.filename)
    project_title = _project_title(title, source_file_name)

    try:
        saved_upload = _save_upload(project_id, source_file_name, file, settings.max_upload_bytes)
        try:
            metadata = probe_video_metadata(saved_upload.path)
            _validate_duration(metadata.duration_ms, settings.max_duration_seconds)
        except (HTTPException, MediaProbeError):
            _discard_saved_upload(saved_upload)
            raise
        project, job = _persist_project_and_job(
            project_id=project_id,
            job_id=job_id,
            title=project_title,
            purpose=purpose,
            output_goal=output_goal,
            analysis_mode=analysis_mode,
            saved_upload=saved_upload,
            source_file_name=source_file_name,
            source_mime_type=file.content_type,
            metadata=metadata,
        )
    except UnsupportedMediaExtensionError as exc:
        raise _api_error(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "UNSUPPORTED_MEDIA_TYPE",
            "Upload must be an mp4, mov, or m4v video.",
        ) from exc
    except UploadTooLargeError as exc:
        raise _api_error(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "UPLOAD_TOO_LARGE",
            f"Upload exceeds the {MAX_UPLOAD_BYTES} byte limit.",
        ) from exc
    except MediaProbeToolUnavailableError as exc:
        raise _api_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "LOCAL_TOOL_UNAVAILABLE",
            "Required local media tooling is unavailable.",
        ) from exc
    except MediaProbeError as exc:
        raise _api_error(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "UNSUPPORTED_MEDIA_TYPE",
            "Uploaded media could not be parsed.",
        ) from exc

    return {
        "project": _project_dto(project),
        "analysis_job": _analysis_job_dto(job),
    }


@router.post("/{project_id}/analysis/run")
def run_project_analysis(project_id: str) -> dict[str, object]:
    db_path = resolve_workspace_path(get_settings().sqlite_path)
    with connect(db_path) as connection:
        initialize_schema(connection)
        projects = VideoProjectRepository(connection)
        jobs = AnalysisJobRepository(connection)
        results = AnalysisResultRepository(connection)

        project = projects.get(project_id)
        if project is None:
            raise _api_error(404, "PROJECT_NOT_FOUND", "Project was not found.")

        job = jobs.get_latest_for_project(project_id)
        if job is None:
            raise _api_error(
                404,
                "ANALYSIS_JOB_NOT_FOUND",
                "Analysis job was not found for this project.",
            )

        draft = build_draft_analysis(
            DraftMedia(
                duration_ms=project.duration_ms,
                has_audio=project.has_audio,
                purpose=project.purpose,
                output_goal=project.output_goal,
            )
        )
        analysis_status = "completed_with_warnings" if draft.warnings else "completed"
        analysis = results.replace_for_project(
            result_id=_new_id("analysis_result"),
            owner_id=project.owner_id,
            project_id=project.id,
            job_id=job.id,
            status=analysis_status,
            warnings=draft.warnings,
            subtitles=tuple(
                SubtitleCreate(
                    id=subtitle.id,
                    start_ms=subtitle.start_ms,
                    end_ms=subtitle.end_ms,
                    text=subtitle.text,
                )
                for subtitle in draft.subtitles
            ),
            segments=tuple(
                VideoSegmentCreate(
                    id=segment.id,
                    segment_type=segment.segment_type,
                    start_ms=segment.start_ms,
                    end_ms=segment.end_ms,
                    transcript=segment.transcript,
                    reason=segment.reason,
                )
                for segment in (*draft.cut_candidates, *draft.highlight_candidates)
            ),
        )
        completed_job = jobs.update(
            job.id,
            AnalysisJobUpdate(
                status=analysis_status,
                progress_percent=100,
                current_step="draft_generation",
                completed_at=utc_now(),
            ),
        )
        projects.update_status(project.id, "draft_ready")

    if completed_job is None:
        raise _api_error(500, "ANALYSIS_JOB_UPDATE_FAILED", "Analysis job update failed.")
    return {"analysis_job": _analysis_job_dto(completed_job), "analysis": _analysis_dto(analysis)}


@router.get("/{project_id}/analysis")
def get_project_analysis(project_id: str) -> dict[str, object]:
    db_path = resolve_workspace_path(get_settings().sqlite_path)
    with connect(db_path) as connection:
        initialize_schema(connection)
        project = VideoProjectRepository(connection).get(project_id)
        if project is None:
            raise _api_error(404, "PROJECT_NOT_FOUND", "Project was not found.")
        analysis = AnalysisResultRepository(connection).get_by_project(project_id)
        if analysis is None:
            raise _api_error(
                404,
                "ANALYSIS_NOT_FOUND",
                "Analysis result was not found for this project.",
            )
    return {"analysis": _analysis_dto(analysis)}


@router.patch("/{project_id}/subtitles/{subtitle_id}")
def update_project_subtitle(
    project_id: str,
    subtitle_id: str,
    request: SubtitleUpdateRequest,
) -> dict[str, object]:
    if request.end_ms <= request.start_ms:
        raise _api_error(400, "VALIDATION_FAILED", "Subtitle end time must be after start time.")

    db_path = resolve_workspace_path(get_settings().sqlite_path)
    with connect(db_path) as connection:
        initialize_schema(connection)
        project = VideoProjectRepository(connection).get(project_id)
        if project is None:
            raise _api_error(404, "PROJECT_NOT_FOUND", "Project was not found.")
        if request.end_ms > project.duration_ms:
            raise _api_error(400, "VALIDATION_FAILED", "Subtitle timing exceeds video duration.")

        subtitle = AnalysisResultRepository(connection).update_subtitle(
            project_id=project_id,
            subtitle_id=subtitle_id,
            edited_text=request.text.strip(),
            start_ms=request.start_ms,
            end_ms=request.end_ms,
        )
        if subtitle is None:
            raise _api_error(404, "SUBTITLE_NOT_FOUND", "Subtitle was not found.")
    return {"subtitle": _subtitle_dto(subtitle)}


@router.patch("/{project_id}/segments/{segment_id}")
def update_project_segment(
    project_id: str,
    segment_id: str,
    request: SegmentUpdateRequest,
) -> dict[str, object]:
    db_path = resolve_workspace_path(get_settings().sqlite_path)
    with connect(db_path) as connection:
        initialize_schema(connection)
        project = VideoProjectRepository(connection).get(project_id)
        if project is None:
            raise _api_error(404, "PROJECT_NOT_FOUND", "Project was not found.")

        segment = AnalysisResultRepository(connection).update_segment_status(
            project_id=project_id,
            segment_id=segment_id,
            status=request.status,
        )
        if segment is None:
            raise _api_error(404, "SEGMENT_NOT_FOUND", "Segment was not found.")
    return {"segment": _segment_dto(segment)}


@router.post("/{project_id}/thumbnails/generate")
def generate_project_thumbnails(project_id: str) -> dict[str, object]:
    db_path = resolve_workspace_path(get_settings().sqlite_path)
    with connect(db_path) as connection:
        initialize_schema(connection)
        project = VideoProjectRepository(connection).get(project_id)
        if project is None:
            raise _api_error(404, "PROJECT_NOT_FOUND", "Project was not found.")

        draft_candidates = build_thumbnail_candidates(project.duration_ms, count=3)
        thumbnails = ThumbnailCandidateRepository(connection).replace_generated_candidates(
            owner_id=project.owner_id,
            project_id=project.id,
            candidates=tuple(
                ThumbnailCandidateCreate(
                    id=candidate.id,
                    image_asset_id=candidate.image_asset_id,
                    timestamp_ms=candidate.timestamp_ms,
                    reason=candidate.reason,
                    tags=candidate.tags,
                    internal_score=candidate.internal_score,
                )
                for candidate in draft_candidates
            ),
        )
    return {"thumbnail_candidates": [_thumbnail_dto(thumbnail) for thumbnail in thumbnails]}


@router.patch("/{project_id}/thumbnails/{thumbnail_id}")
def update_project_thumbnail(
    project_id: str,
    thumbnail_id: str,
    request: ThumbnailUpdateRequest,
) -> dict[str, object]:
    db_path = resolve_workspace_path(get_settings().sqlite_path)
    with connect(db_path) as connection:
        initialize_schema(connection)
        project = VideoProjectRepository(connection).get(project_id)
        if project is None:
            raise _api_error(404, "PROJECT_NOT_FOUND", "Project was not found.")

        thumbnail = ThumbnailCandidateRepository(connection).update_status(
            project_id=project_id,
            thumbnail_id=thumbnail_id,
            status=request.status,
        )
        if thumbnail is None:
            raise _api_error(
                404,
                "THUMBNAIL_NOT_FOUND",
                "Thumbnail candidate was not found.",
            )
    return {"thumbnail": _thumbnail_dto(thumbnail)}


@router.post("/{project_id}/thumbnails/direct-frame")
def create_direct_frame_thumbnail(
    project_id: str,
    request: DirectFrameRequest,
) -> dict[str, object]:
    db_path = resolve_workspace_path(get_settings().sqlite_path)
    with connect(db_path) as connection:
        initialize_schema(connection)
        project = VideoProjectRepository(connection).get(project_id)
        if project is None:
            raise _api_error(404, "PROJECT_NOT_FOUND", "Project was not found.")
        if request.timestamp_ms > project.duration_ms:
            raise _api_error(400, "VALIDATION_FAILED", "Timestamp exceeds video duration.")

        thumbnail = ThumbnailCandidateRepository(connection).create_direct_frame(
            owner_id=project.owner_id,
            project_id=project.id,
            candidate=ThumbnailCandidateCreate(
                id=_new_id("thumbnail"),
                image_asset_id=_new_id("asset"),
                timestamp_ms=request.timestamp_ms,
                reason="Direct frame selected by the user.",
                tags=("direct_frame",),
                internal_score=1.0,
                status="custom_selected",
            ),
        )
    return {"thumbnail": _thumbnail_dto(thumbnail)}


@router.post("/{project_id}/exports")
def create_project_export(
    project_id: str,
    request: ExportCreateRequest,
) -> dict[str, object]:
    db_path = resolve_workspace_path(get_settings().sqlite_path)
    with connect(db_path) as connection:
        initialize_schema(connection)
        project = VideoProjectRepository(connection).get(project_id)
        if project is None:
            raise _api_error(404, "PROJECT_NOT_FOUND", "Project was not found.")

        export_job = ExportJobRepository(connection).create_completed(
            ExportJobCreate(
                id=_new_id("export"),
                owner_id=project.owner_id,
                project_id=project.id,
                aspect_ratio=request.aspect_ratio,
                resolution=request.resolution,
                include_subtitles=request.include_subtitles,
                include_thumbnail=request.include_thumbnail,
                crop_mode=request.crop_mode,
                output_asset_id=_new_id("asset"),
                thumbnail_asset_id=_new_id("asset") if request.include_thumbnail else None,
            )
        )
    return {"export_job": _export_job_dto(export_job)}


@router.get("/{project_id}/exports/{export_id}")
def get_project_export(project_id: str, export_id: str) -> dict[str, object]:
    db_path = resolve_workspace_path(get_settings().sqlite_path)
    with connect(db_path) as connection:
        initialize_schema(connection)
        project = VideoProjectRepository(connection).get(project_id)
        if project is None:
            raise _api_error(404, "PROJECT_NOT_FOUND", "Project was not found.")
        export_job = ExportJobRepository(connection).get(project_id, export_id)
        if export_job is None:
            raise _api_error(404, "EXPORT_NOT_FOUND", "Export job was not found.")
    return {"export_job": _export_job_dto(export_job)}


def _save_upload(
    project_id: str,
    source_file_name: str,
    file: UploadFile,
    max_upload_bytes: int,
) -> StoredSourceUpload:
    storage_root = resolve_workspace_path(get_settings().storage_dir)
    storage = LocalMediaStorage(storage_root)
    return storage.save_source_upload(
        video_id=project_id,
        upload_filename=source_file_name,
        source=file.file,
        max_bytes=max_upload_bytes,
    )


def _discard_saved_upload(saved_upload: StoredSourceUpload) -> None:
    with suppress(FileNotFoundError):
        saved_upload.path.unlink()
    with suppress(OSError):
        saved_upload.path.parent.rmdir()


def _persist_project_and_job(
    *,
    project_id: str,
    job_id: str,
    title: str,
    purpose: str,
    output_goal: str,
    analysis_mode: str,
    saved_upload: StoredSourceUpload,
    source_file_name: str,
    source_mime_type: str | None,
    metadata: VideoMetadata,
    connector: Callable[[Path], Any] = connect,
) -> tuple[VideoProject, AnalysisJob]:
    db_path = resolve_workspace_path(get_settings().sqlite_path)
    with connector(db_path) as connection:
        initialize_schema(connection)
        projects = VideoProjectRepository(connection)
        jobs = AnalysisJobRepository(connection)
        project = projects.create(
            VideoProjectCreate(
                id=project_id,
                owner_id=DEFAULT_LOCAL_USER_ID,
                title=title,
                purpose=purpose,
                output_goal=output_goal,
                duration_ms=metadata.duration_ms,
                width=metadata.width,
                height=metadata.height,
                fps=metadata.fps,
                aspect_ratio=metadata.aspect_ratio,
                has_audio=metadata.has_audio,
                source_file_name=source_file_name,
                source_extension=saved_upload.extension,
                source_mime_type=source_mime_type,
                source_size_bytes=saved_upload.size_bytes,
            )
        )
        job = jobs.create(
            AnalysisJobCreate(
                id=job_id,
                owner_id=DEFAULT_LOCAL_USER_ID,
                project_id=project_id,
                mode=analysis_mode,
            )
        )
    return project, job


def _validate_duration(duration_ms: int, max_duration_seconds: int) -> None:
    if duration_ms > max_duration_seconds * 1000:
        raise _api_error(
            422,
            "VIDEO_DURATION_EXCEEDED",
            "Only videos up to 20 minutes can be analyzed.",
        )


def _validate_form_choice(
    field_name: str,
    value: str,
    allowed_values: tuple[str, ...] | frozenset[str],
) -> None:
    if value not in allowed_values:
        raise _api_error(
            status.HTTP_400_BAD_REQUEST,
            "VALIDATION_FAILED",
            f"Unsupported {field_name}.",
        )


def _safe_display_filename(filename: str | None) -> str:
    if filename is None:
        return "upload.mp4"
    name = filename.replace("\\", "/").rsplit("/", maxsplit=1)[-1].strip()
    name = SAFE_DISPLAY_NAME_RE.sub("", name)
    if name == "":
        return "upload.mp4"
    return name[:255]


def _project_title(title: str | None, source_file_name: str) -> str:
    clean_title = SAFE_DISPLAY_NAME_RE.sub("", (title or "").strip())
    if clean_title:
        return clean_title[:120]
    stem = source_file_name.rsplit(".", maxsplit=1)[0].strip()
    return (stem or "Untitled video")[:120]


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(16)}"


def _project_dto(project: VideoProject) -> dict[str, object]:
    return {
        "project_id": project.id,
        "owner_id": project.owner_id,
        "title": project.title,
        "purpose": project.purpose,
        "output_goal": project.output_goal,
        "status": project.status,
        "metadata": {
            "duration_ms": project.duration_ms,
            "width": project.width,
            "height": project.height,
            "fps": project.fps,
            "aspect_ratio": project.aspect_ratio,
            "has_audio": project.has_audio,
            "source_file_name": project.source_file_name,
            "source_extension": project.source_extension,
            "source_mime_type": project.source_mime_type,
            "source_size_bytes": project.source_size_bytes,
        },
        "selected_thumbnail_id": None,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "deleted_at": None,
    }


def _analysis_job_dto(job: AnalysisJob) -> dict[str, object]:
    return {
        "job_id": job.id,
        "project_id": job.project_id,
        "owner_id": job.owner_id,
        "status": job.status,
        "mode": job.mode,
        "progress_percent": job.progress_percent,
        "current_step": job.current_step,
        "failed_step": job.failed_step,
        "warnings": [],
        "error": None,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "updated_at": job.updated_at,
    }


def _subtitle_dto(subtitle: Subtitle) -> dict[str, object]:
    return {
        "subtitle_id": subtitle.id,
        "start_ms": subtitle.start_ms,
        "end_ms": subtitle.end_ms,
        "text": subtitle.text,
        "edited_text": subtitle.edited_text,
        "status": subtitle.status,
    }


def _analysis_dto(analysis: AnalysisResult) -> dict[str, object]:
    return {
        "project_id": analysis.project_id,
        "job_id": analysis.job_id,
        "status": analysis.status,
        "warnings": list(analysis.warnings),
        "subtitles": [_subtitle_dto(subtitle) for subtitle in analysis.subtitles],
        "cut_candidates": [_segment_dto(segment) for segment in analysis.cut_candidates],
        "highlight_candidates": [
            _segment_dto(segment) for segment in analysis.highlight_candidates
        ],
    }


def _segment_dto(segment: VideoSegment) -> dict[str, object]:
    return {
        "segment_id": segment.id,
        "type": segment.segment_type,
        "start_ms": segment.start_ms,
        "end_ms": segment.end_ms,
        "transcript": segment.transcript,
        "reason": segment.reason,
        "status": segment.status,
    }


def _thumbnail_dto(thumbnail: ThumbnailCandidate) -> dict[str, object]:
    return {
        "thumbnail_id": thumbnail.id,
        "timestamp_ms": thumbnail.timestamp_ms,
        "image_url": f"/api/v1/media/{thumbnail.image_asset_id}",
        "reason": thumbnail.reason,
        "tags": list(thumbnail.tags),
        "status": thumbnail.status,
    }


def _export_job_dto(export_job: ExportJob) -> dict[str, object]:
    return {
        "export_id": export_job.id,
        "project_id": export_job.project_id,
        "status": export_job.status,
        "aspect_ratio": export_job.aspect_ratio,
        "resolution": export_job.resolution,
        "include_subtitles": export_job.include_subtitles,
        "include_thumbnail": export_job.include_thumbnail,
        "crop_mode": export_job.crop_mode,
        "download_url": f"/api/v1/downloads/{export_job.output_asset_id}",
        "thumbnail_download_url": (
            f"/api/v1/downloads/{export_job.thumbnail_asset_id}"
            if export_job.thumbnail_asset_id is not None
            else None
        ),
        "error": None,
        "created_at": export_job.created_at,
        "completed_at": export_job.completed_at,
    }


def _api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": code,
                "message": message,
                "retryable": False,
                "details": {},
            }
        },
    )
