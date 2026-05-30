from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.config import ANALYSIS_MODES, MAX_UPLOAD_BYTES, get_settings
from app.core.paths import resolve_workspace_path
from app.db.connection import connect
from app.db.repositories import (
    DEFAULT_LOCAL_USER_ID,
    AnalysisJob,
    AnalysisJobCreate,
    AnalysisJobRepository,
    VideoProject,
    VideoProjectCreate,
    VideoProjectRepository,
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

router = APIRouter(prefix="/projects", tags=["projects"])

CONTENT_PURPOSES = frozenset({"short_form", "vlog", "lecture", "interview", "promotional_video"})
OUTPUT_GOALS = frozenset(
    {"source_summary", "highlight_extraction", "subtitle_generation", "short_form_conversion"}
)
SAFE_DISPLAY_NAME_RE = re.compile(r"[\x00-\x1f\x7f]")


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
