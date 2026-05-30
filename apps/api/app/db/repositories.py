from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

DEFAULT_LOCAL_USER_ID = "local_user"


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class VideoProjectCreate:
    id: str
    owner_id: str
    title: str
    purpose: str
    output_goal: str
    duration_ms: int
    width: int
    height: int
    fps: float | None
    aspect_ratio: str
    has_audio: bool
    source_file_name: str
    source_extension: str
    source_mime_type: str | None
    source_size_bytes: int


@dataclass(frozen=True)
class VideoProject:
    id: str
    owner_id: str
    title: str
    purpose: str
    output_goal: str
    status: str
    duration_ms: int
    width: int
    height: int
    fps: float | None
    aspect_ratio: str
    has_audio: bool
    source_file_name: str
    source_extension: str
    source_mime_type: str | None
    source_size_bytes: int
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class AnalysisJobCreate:
    id: str
    owner_id: str
    project_id: str
    mode: str


@dataclass(frozen=True)
class AnalysisJobUpdate:
    status: str | None = None
    progress_percent: int | None = None
    current_step: str | None = None
    failed_step: str | None = None
    error_code: str | None = None
    error_summary: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


@dataclass(frozen=True)
class AnalysisJob:
    id: str
    owner_id: str
    project_id: str
    status: str
    mode: str
    progress_percent: int
    current_step: str | None
    failed_step: str | None
    error_code: str | None
    error_summary: str | None
    retry_of_job_id: str | None
    local_runtime: str | None
    model_profile_json: str | None
    tool_versions_json: str | None
    created_at: str
    started_at: str | None
    completed_at: str | None
    updated_at: str


class VideoProjectRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, data: VideoProjectCreate) -> VideoProject:
        timestamp = utc_now()
        ensure_local_user(self.connection, data.owner_id, timestamp)
        self.connection.execute(
            """
            INSERT INTO video_projects (
                id,
                owner_id,
                title,
                purpose,
                output_goal,
                status,
                duration_ms,
                width,
                height,
                fps,
                aspect_ratio,
                has_audio,
                source_file_name,
                source_extension,
                source_mime_type,
                source_size_bytes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, 'uploaded', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.id,
                data.owner_id,
                data.title,
                data.purpose,
                data.output_goal,
                data.duration_ms,
                data.width,
                data.height,
                data.fps,
                data.aspect_ratio,
                1 if data.has_audio else 0,
                data.source_file_name,
                data.source_extension,
                data.source_mime_type,
                data.source_size_bytes,
                timestamp,
                timestamp,
            ),
        )
        self.connection.commit()
        created = self.get(data.id)
        if created is None:
            raise RuntimeError("Failed to fetch created video project.")
        return created

    def get(self, project_id: str) -> VideoProject | None:
        row = self.connection.execute(
            """
            SELECT
                id,
                owner_id,
                title,
                purpose,
                output_goal,
                status,
                duration_ms,
                width,
                height,
                fps,
                aspect_ratio,
                has_audio,
                source_file_name,
                source_extension,
                source_mime_type,
                source_size_bytes,
                created_at,
                updated_at
            FROM video_projects
            WHERE id = ?
            """,
            (project_id,),
        ).fetchone()
        if row is None:
            return None
        return _video_from_row(row)


class AnalysisJobRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, data: AnalysisJobCreate) -> AnalysisJob:
        timestamp = utc_now()
        self.connection.execute(
            """
            INSERT INTO analysis_jobs (
                id,
                owner_id,
                project_id,
                status,
                mode,
                progress_percent,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, 'queued', ?, 0, ?, ?)
            """,
            (data.id, data.owner_id, data.project_id, data.mode, timestamp, timestamp),
        )
        self.connection.commit()
        created = self.get(data.id)
        if created is None:
            raise RuntimeError("Failed to fetch created analysis job.")
        return created

    def update(self, job_id: str, data: AnalysisJobUpdate) -> AnalysisJob | None:
        existing = self.get(job_id)
        if existing is None:
            return None

        timestamp = utc_now()
        self.connection.execute(
            """
            UPDATE analysis_jobs
            SET
                status = COALESCE(?, status),
                progress_percent = COALESCE(?, progress_percent),
                current_step = COALESCE(?, current_step),
                failed_step = COALESCE(?, failed_step),
                error_code = COALESCE(?, error_code),
                error_summary = COALESCE(?, error_summary),
                started_at = COALESCE(?, started_at),
                completed_at = COALESCE(?, completed_at),
                updated_at = ?
            WHERE id = ?
            """,
            (
                data.status,
                data.progress_percent,
                data.current_step,
                data.failed_step,
                data.error_code,
                data.error_summary,
                data.started_at,
                data.completed_at,
                timestamp,
                job_id,
            ),
        )
        self.connection.commit()
        return self.get(job_id)

    def get(self, job_id: str) -> AnalysisJob | None:
        row = self.connection.execute(
            """
            SELECT
                id,
                owner_id,
                project_id,
                status,
                mode,
                progress_percent,
                current_step,
                failed_step,
                error_code,
                error_summary,
                retry_of_job_id,
                local_runtime,
                model_profile_json,
                tool_versions_json,
                created_at,
                started_at,
                completed_at,
                updated_at
            FROM analysis_jobs
            WHERE id = ?
            """,
            (job_id,),
        ).fetchone()
        if row is None:
            return None
        return _job_from_row(row)


def ensure_local_user(
    connection: sqlite3.Connection,
    user_id: str,
    timestamp: str | None = None,
) -> None:
    created_at = timestamp or utc_now()
    connection.execute(
        """
        INSERT INTO users (id, local_user, created_at, updated_at)
        VALUES (?, 1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET updated_at = excluded.updated_at
        """,
        (user_id, created_at, created_at),
    )


def _video_from_row(row: sqlite3.Row) -> VideoProject:
    return VideoProject(
        id=row["id"],
        owner_id=row["owner_id"],
        title=row["title"],
        purpose=row["purpose"],
        output_goal=row["output_goal"],
        status=row["status"],
        duration_ms=row["duration_ms"],
        width=row["width"],
        height=row["height"],
        fps=row["fps"],
        aspect_ratio=row["aspect_ratio"],
        has_audio=bool(row["has_audio"]),
        source_file_name=row["source_file_name"],
        source_extension=row["source_extension"],
        source_mime_type=row["source_mime_type"],
        source_size_bytes=row["source_size_bytes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _job_from_row(row: sqlite3.Row) -> AnalysisJob:
    return AnalysisJob(
        id=row["id"],
        owner_id=row["owner_id"],
        project_id=row["project_id"],
        status=row["status"],
        mode=row["mode"],
        progress_percent=row["progress_percent"],
        current_step=row["current_step"],
        failed_step=row["failed_step"],
        error_code=row["error_code"],
        error_summary=row["error_summary"],
        retry_of_job_id=row["retry_of_job_id"],
        local_runtime=row["local_runtime"],
        model_profile_json=row["model_profile_json"],
        tool_versions_json=row["tool_versions_json"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        updated_at=row["updated_at"],
    )
