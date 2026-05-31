import os

import pytest

from app import desktop_sidecar


def test_desktop_sidecar_sets_local_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(app: str, **kwargs: object) -> None:
        calls.append({"app": app, **kwargs})

    monkeypatch.delenv("CUTMATE_APP_URL", raising=False)
    monkeypatch.delenv("CUTMATE_STORAGE_DIR", raising=False)
    monkeypatch.delenv("CUTMATE_SQLITE_PATH", raising=False)

    desktop_sidecar.main(run_server=fake_run)

    assert calls == [
        {
            "app": "app.main:app",
            "host": "127.0.0.1",
            "port": 8000,
            "log_level": "info",
        }
    ]
    assert os.environ["CUTMATE_APP_URL"] == "tauri://localhost"
    assert os.environ["CUTMATE_STORAGE_DIR"] == ".cutmate/storage"
    assert os.environ["CUTMATE_SQLITE_PATH"] == ".cutmate/cutmate.db"
