from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.core.config import get_settings
from app.core.paths import resolve_workspace_path
from app.db.connection import connect
from app.db.repositories import (
    AnalysisJobCreate,
    AnalysisJobRepository,
    VideoProjectCreate,
    VideoProjectRepository,
)
from app.db.schema import initialize_schema
from app.main import create_app


def teardown_function() -> None:
    get_settings.cache_clear()


def test_generate_thumbnail_candidates_hides_internal_scores(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_id = _seed_project(monkeypatch, tmp_path)
    client = TestClient(create_app())

    response: Response = client.post(f"/api/v1/projects/{project_id}/thumbnails/generate")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["thumbnail_candidates"]) == 3
    assert "internal_score" not in str(payload)
    assert ".cutmate" not in str(payload)
    assert payload["thumbnail_candidates"][0]["status"] == "pending"
    assert payload["thumbnail_candidates"][0]["image_url"].startswith("/api/v1/media/")


def test_select_candidate_and_direct_frame_thumbnail(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_id = _seed_project(monkeypatch, tmp_path)
    client = TestClient(create_app())
    candidates = client.post(
        f"/api/v1/projects/{project_id}/thumbnails/generate"
    ).json()["thumbnail_candidates"]
    candidate_id = candidates[0]["thumbnail_id"]

    select_response: Response = client.patch(
        f"/api/v1/projects/{project_id}/thumbnails/{candidate_id}",
        json={"status": "selected"},
    )
    direct_response: Response = client.post(
        f"/api/v1/projects/{project_id}/thumbnails/direct-frame",
        json={"timestamp_ms": 12_000},
    )

    assert select_response.status_code == 200
    assert select_response.json()["thumbnail"]["status"] == "selected"
    assert direct_response.status_code == 200
    assert direct_response.json()["thumbnail"]["status"] == "custom_selected"
    assert direct_response.json()["thumbnail"]["timestamp_ms"] == 12_000


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
                title="Thumbnail project",
                purpose="promotional_video",
                output_goal="highlight_extraction",
                duration_ms=60_000,
                width=1920,
                height=1080,
                fps=30.0,
                aspect_ratio="16:9",
                has_audio=True,
                source_file_name="thumbnail.mp4",
                source_extension="mp4",
                source_mime_type="video/mp4",
                source_size_bytes=100,
            )
        )
        AnalysisJobRepository(connection).create(
            AnalysisJobCreate(
                id=f"analysis_job_{token}",
                owner_id="local_user",
                project_id=project_id,
                mode="standard",
            )
        )
    return project_id
