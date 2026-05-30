from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.api import projects as projects_api
from app.core.config import get_settings
from app.core.paths import resolve_workspace_path
from app.db.connection import connect
from app.db.repositories import AnalysisJobRepository, VideoProjectRepository
from app.main import create_app
from app.media.probe import VideoMetadata


def teardown_function() -> None:
    get_settings.cache_clear()


def test_create_project_upload_saves_file_and_creates_queued_job(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_test_storage(monkeypatch, tmp_path)
    monkeypatch.setattr(projects_api, "probe_video_metadata", _fake_probe)
    client = TestClient(create_app())

    response: Response = client.post(
        "/api/v1/projects",
        data={
            "title": "Launch cut",
            "purpose": "promotional_video",
            "output_goal": "highlight_extraction",
            "analysis_mode": "quality",
        },
        files={"file": ("launch.MP4", b"video-bytes", "video/mp4")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert ".pytest_tmp" not in str(payload)
    assert payload["project"]["title"] == "Launch cut"
    assert payload["project"]["metadata"]["source_extension"] == "mp4"
    assert payload["project"]["metadata"]["source_size_bytes"] == len(b"video-bytes")
    assert payload["analysis_job"]["status"] == "queued"
    assert payload["analysis_job"]["mode"] == "quality"

    project_id = payload["project"]["project_id"]
    job_id = payload["analysis_job"]["job_id"]
    source_path = _relative_path(tmp_path, "storage") / "uploads" / project_id / "source.mp4"
    assert source_path.read_bytes() == b"video-bytes"

    with connect(_relative_path(tmp_path, "cutmate.db")) as connection:
        assert VideoProjectRepository(connection).get(project_id) is not None
        assert AnalysisJobRepository(connection).get(job_id) is not None


def test_create_project_rejects_unsupported_upload_extension(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_test_storage(monkeypatch, tmp_path)
    client = TestClient(create_app())

    response: Response = client.post(
        "/api/v1/projects",
        data={
            "purpose": "vlog",
            "output_goal": "source_summary",
            "analysis_mode": "standard",
        },
        files={"file": ("clip.avi", b"video-bytes", "video/x-msvideo")},
    )

    assert response.status_code == 415
    assert response.json()["detail"]["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert not _relative_path(tmp_path, "cutmate.db").exists()


def test_create_project_rejects_over_duration_media_without_creating_job(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_test_storage(monkeypatch, tmp_path)
    monkeypatch.setattr(projects_api, "probe_video_metadata", _over_duration_probe)
    client = TestClient(create_app())

    response: Response = client.post(
        "/api/v1/projects",
        data={
            "purpose": "vlog",
            "output_goal": "source_summary",
            "analysis_mode": "standard",
        },
        files={"file": ("clip.mp4", b"video-bytes", "video/mp4")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error"]["code"] == "VIDEO_DURATION_EXCEEDED"
    assert not _relative_path(tmp_path, "cutmate.db").exists()
    storage_root = _relative_path(tmp_path, "storage")
    assert not list(storage_root.glob("uploads/*/source.mp4"))


def _configure_test_storage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    token = tmp_path.name
    monkeypatch.setenv("CUTMATE_STORAGE_DIR", f".pytest_tmp/{token}/storage")
    monkeypatch.setenv("CUTMATE_SQLITE_PATH", f".pytest_tmp/{token}/cutmate.db")
    get_settings.cache_clear()


def _relative_path(tmp_path: Path, child: str) -> Path:
    return resolve_workspace_path(f".pytest_tmp/{tmp_path.name}/{child}")


def _fake_probe(path: Path) -> VideoMetadata:
    assert path.exists()
    return VideoMetadata(
        duration_ms=42_000,
        width=1920,
        height=1080,
        fps=29.97,
        aspect_ratio="16:9",
        has_audio=True,
    )


def _over_duration_probe(path: Path) -> VideoMetadata:
    assert path.exists()
    return VideoMetadata(
        duration_ms=1_200_001,
        width=1920,
        height=1080,
        fps=30.0,
        aspect_ratio="16:9",
        has_audio=True,
    )
