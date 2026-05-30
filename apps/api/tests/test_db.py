import sqlite3
from pathlib import Path

import pytest

from app.db.connection import connect
from app.db.repositories import (
    AnalysisJobCreate,
    AnalysisJobRepository,
    AnalysisJobUpdate,
    VideoProjectCreate,
    VideoProjectRepository,
)
from app.db.schema import initialize_schema


def test_initialize_schema_creates_required_tables_and_indexes(tmp_path: Path) -> None:
    db_path = tmp_path / "cutmate.sqlite3"

    with connect(db_path) as conn:
        initialize_schema(conn)

        table_names = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        index_names = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }

        assert {"users", "video_projects", "media_assets", "analysis_jobs"} <= table_names
        assert {
            "idx_projects_owner_deleted_created",
            "idx_projects_owner_status",
            "idx_analysis_jobs_project_created",
            "idx_analysis_jobs_owner_status",
            "ux_analysis_one_active_per_project",
        } <= index_names
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1


def test_create_and_fetch_video_project(tmp_path: Path) -> None:
    db_path = tmp_path / "cutmate.sqlite3"

    with connect(db_path) as conn:
        initialize_schema(conn)
        videos = VideoProjectRepository(conn)

        created = videos.create(
            VideoProjectCreate(
                id="project_1",
                owner_id="local_user",
                title="Launch edit",
                purpose="promotional_video",
                output_goal="highlight_extraction",
                duration_ms=305_000,
                width=1920,
                height=1080,
                fps=29.97,
                aspect_ratio="16:9",
                has_audio=True,
                source_file_name="launch.mov",
                source_extension="mov",
                source_mime_type="video/quicktime",
                source_size_bytes=2_147_483_648,
            )
        )

        fetched = videos.get("project_1")

    assert fetched == created
    assert created.status == "uploaded"
    assert created.owner_id == "local_user"
    assert created.has_audio is True
    assert created.source_size_bytes == 2_147_483_648
    assert created.created_at.endswith("Z")
    assert created.updated_at == created.created_at


def test_create_update_and_fetch_analysis_job(tmp_path: Path) -> None:
    db_path = tmp_path / "cutmate.sqlite3"

    with connect(db_path) as conn:
        initialize_schema(conn)
        videos = VideoProjectRepository(conn)
        jobs = AnalysisJobRepository(conn)
        videos.create(
            VideoProjectCreate(
                id="project_1",
                owner_id="local_user",
                title="Interview edit",
                purpose="interview",
                output_goal="subtitle_generation",
                duration_ms=120_000,
                width=1280,
                height=720,
                fps=None,
                aspect_ratio="16:9",
                has_audio=True,
                source_file_name="interview.mp4",
                source_extension="mp4",
                source_mime_type="video/mp4",
                source_size_bytes=42_000_000,
            )
        )

        created = jobs.create(
            AnalysisJobCreate(
                id="job_1",
                owner_id="local_user",
                project_id="project_1",
                mode="standard",
            )
        )
        updated = jobs.update(
            "job_1",
            AnalysisJobUpdate(
                status="processing",
                progress_percent=35,
                current_step="speech_recognition",
                started_at="2026-05-31T01:00:00Z",
            ),
        )
        fetched = jobs.get("job_1")

    assert created.status == "queued"
    assert created.progress_percent == 0
    assert updated is not None
    assert updated == fetched
    assert fetched is not None
    assert fetched.status == "processing"
    assert fetched.progress_percent == 35
    assert fetched.current_step == "speech_recognition"
    assert fetched.started_at == "2026-05-31T01:00:00Z"
    assert fetched.updated_at != created.updated_at


def test_database_persists_video_and_job_across_connections(tmp_path: Path) -> None:
    db_path = tmp_path / "cutmate.sqlite3"

    with connect(db_path) as conn:
        initialize_schema(conn)
        videos = VideoProjectRepository(conn)
        jobs = AnalysisJobRepository(conn)
        videos.create(
            VideoProjectCreate(
                id="project_1",
                owner_id="local_user",
                title="Vlog edit",
                purpose="vlog",
                output_goal="short_form_conversion",
                duration_ms=600_000,
                width=3840,
                height=2160,
                fps=60.0,
                aspect_ratio="16:9",
                has_audio=False,
                source_file_name="weekend.m4v",
                source_extension="m4v",
                source_mime_type=None,
                source_size_bytes=1_000_000,
            )
        )
        jobs.create(
            AnalysisJobCreate(
                id="job_1",
                owner_id="local_user",
                project_id="project_1",
                mode="light",
            )
        )

    with connect(db_path) as conn:
        videos = VideoProjectRepository(conn)
        jobs = AnalysisJobRepository(conn)

        assert videos.get("project_1") is not None
        assert jobs.get("job_1") is not None
        assert videos.get("missing") is None
        assert jobs.get("missing") is None


def test_analysis_job_requires_existing_project(tmp_path: Path) -> None:
    db_path = tmp_path / "cutmate.sqlite3"

    with connect(db_path) as conn:
        initialize_schema(conn)
        jobs = AnalysisJobRepository(conn)

        with pytest.raises(sqlite3.IntegrityError):
            jobs.create(
                AnalysisJobCreate(
                    id="job_1",
                    owner_id="local_user",
                    project_id="missing_project",
                    mode="standard",
                )
            )
