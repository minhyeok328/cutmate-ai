from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.core.config import get_settings
from app.core.paths import resolve_workspace_path
from app.db.connection import connect
from app.db.repositories import VideoProjectCreate, VideoProjectRepository
from app.db.schema import initialize_schema
from app.main import create_app


def teardown_function() -> None:
    get_settings.cache_clear()


def test_create_and_fetch_export_job_without_exposing_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_id = _seed_project(monkeypatch, tmp_path)
    client = TestClient(create_app())

    create_response: Response = client.post(
        f"/api/v1/projects/{project_id}/exports",
        json={
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "include_subtitles": True,
            "include_thumbnail": True,
            "crop_mode": "center",
        },
    )

    assert create_response.status_code == 200
    payload = create_response.json()
    assert payload["export_job"]["status"] == "completed"
    assert payload["export_job"]["aspect_ratio"] == "9:16"
    assert payload["export_job"]["download_url"].startswith("/api/v1/downloads/")
    assert ".cutmate" not in str(payload)

    export_id = payload["export_job"]["export_id"]
    fetch_response: Response = client.get(f"/api/v1/projects/{project_id}/exports/{export_id}")

    assert fetch_response.status_code == 200
    assert fetch_response.json()["export_job"] == payload["export_job"]


def test_record_metric_event_and_run_cleanup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _seed_project(monkeypatch, tmp_path)
    client = TestClient(create_app())

    metric_response: Response = client.post(
        "/api/v1/metrics/events",
        json={"event_name": "export_completed", "metadata": {"surface": "workspace"}},
    )
    cleanup_response: Response = client.post("/api/v1/maintenance/cleanup")

    assert metric_response.status_code == 200
    assert metric_response.json()["metric_event"]["event_name"] == "export_completed"
    assert cleanup_response.status_code == 200
    assert cleanup_response.json()["cleanup"]["status"] == "completed"

    invalid_response: Response = client.post(
        "/api/v1/metrics/events",
        json={"event_name": "Invalid Event", "metadata": {}},
    )

    assert invalid_response.status_code == 400
    assert invalid_response.json()["detail"]["error"]["code"] == "VALIDATION_FAILED"


def _seed_project(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> str:
    workspace_root = resolve_workspace_path(".")
    relative_tmp_path = tmp_path.relative_to(workspace_root).as_posix()
    token = tmp_path.name
    monkeypatch.setenv("CUTMATE_SQLITE_PATH", f"{relative_tmp_path}/cutmate.db")
    monkeypatch.setenv("CUTMATE_STORAGE_DIR", f"{relative_tmp_path}/storage")
    get_settings.cache_clear()

    project_id = f"project_{token}"
    db_path = resolve_workspace_path(f"{relative_tmp_path}/cutmate.db")
    with connect(db_path) as connection:
        initialize_schema(connection)
        VideoProjectRepository(connection).create(
            VideoProjectCreate(
                id=project_id,
                owner_id="local_user",
                title="Export project",
                purpose="promotional_video",
                output_goal="short_form_conversion",
                duration_ms=60_000,
                width=1920,
                height=1080,
                fps=30.0,
                aspect_ratio="16:9",
                has_audio=True,
                source_file_name="export.mp4",
                source_extension="mp4",
                source_mime_type="video/mp4",
                source_size_bytes=100,
            )
        )
    return project_id
