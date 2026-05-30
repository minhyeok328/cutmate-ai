from fastapi.testclient import TestClient
from httpx import Response

from app.main import create_app


def test_health_check_reports_local_first_runtime() -> None:
    client = TestClient(create_app())

    response: Response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_name": "CutMate AI",
        "local_worker": "available",
        "local_first": True,
        "external_api_mode": "disabled",
    }


def test_runtime_config_exposes_safe_local_quality_mode() -> None:
    client = TestClient(create_app())

    response: Response = client.get("/api/v1/config/runtime")

    assert response.status_code == 200
    payload = response.json()
    assert payload["quality_mode"]["model"] == "openai/gpt-oss-20b"
    assert payload["quality_mode"]["api_key_required"] is False
    assert payload["external_api_enabled"] is False
