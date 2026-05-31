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


def test_run_analysis_generates_draft_results(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_id = _seed_project(monkeypatch, tmp_path, has_audio=True)
    client = TestClient(create_app())

    response: Response = client.post(f"/api/v1/projects/{project_id}/analysis/run")

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_job"]["status"] == "completed"
    assert payload["analysis_job"]["progress_percent"] == 100
    assert payload["analysis"]["status"] == "completed"
    assert len(payload["analysis"]["subtitles"]) == 2
    assert len(payload["analysis"]["cut_candidates"]) == 1
    assert len(payload["analysis"]["highlight_candidates"]) == 1
    assert "internal_score" not in str(payload)
    assert ".cutmate" not in str(payload)

    get_response: Response = client.get(f"/api/v1/projects/{project_id}/analysis")

    assert get_response.status_code == 200
    assert get_response.json()["analysis"] == payload["analysis"]


def test_run_analysis_without_audio_skips_subtitles_but_keeps_candidates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_id = _seed_project(monkeypatch, tmp_path, has_audio=False)
    client = TestClient(create_app())

    response: Response = client.post(f"/api/v1/projects/{project_id}/analysis/run")

    assert response.status_code == 200
    analysis = response.json()["analysis"]
    assert analysis["subtitles"] == []
    assert analysis["warnings"] == ["speech_recognition_skipped_no_audio"]
    assert len(analysis["cut_candidates"]) == 1
    assert len(analysis["highlight_candidates"]) == 1


def test_update_subtitle_and_segment_review_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_id = _seed_project(monkeypatch, tmp_path, has_audio=True)
    client = TestClient(create_app())
    analysis = client.post(f"/api/v1/projects/{project_id}/analysis/run").json()["analysis"]
    subtitle_id = analysis["subtitles"][0]["subtitle_id"]
    segment_id = analysis["cut_candidates"][0]["segment_id"]

    subtitle_response: Response = client.patch(
        f"/api/v1/projects/{project_id}/subtitles/{subtitle_id}",
        json={"text": "Edited subtitle text.", "start_ms": 100, "end_ms": 2_500},
    )
    segment_response: Response = client.patch(
        f"/api/v1/projects/{project_id}/segments/{segment_id}",
        json={"status": "accepted"},
    )

    assert subtitle_response.status_code == 200
    assert subtitle_response.json()["subtitle"] == {
        "subtitle_id": subtitle_id,
        "start_ms": 100,
        "end_ms": 2_500,
        "text": "Local subtitle draft generated from the source audio.",
        "edited_text": "Edited subtitle text.",
        "status": "edited",
    }
    assert segment_response.status_code == 200
    assert segment_response.json()["segment"]["segment_id"] == segment_id
    assert segment_response.json()["segment"]["status"] == "accepted"

    refreshed = client.get(f"/api/v1/projects/{project_id}/analysis").json()["analysis"]
    assert refreshed["subtitles"][0]["edited_text"] == "Edited subtitle text."
    assert refreshed["cut_candidates"][0]["status"] == "accepted"


def _seed_project(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, has_audio: bool) -> str:
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
                title="Analysis project",
                purpose="promotional_video",
                output_goal="highlight_extraction",
                duration_ms=60_000,
                width=1920,
                height=1080,
                fps=30.0,
                aspect_ratio="16:9",
                has_audio=has_audio,
                source_file_name="analysis.mp4",
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
