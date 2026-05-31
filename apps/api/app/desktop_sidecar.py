from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

UvicornRunner = Callable[..., Any]


def main(run_server: UvicornRunner | None = None) -> None:
    os.environ.setdefault("CUTMATE_APP_URL", "tauri://localhost")
    os.environ.setdefault("CUTMATE_STORAGE_DIR", ".cutmate/storage")
    os.environ.setdefault("CUTMATE_SQLITE_PATH", ".cutmate/cutmate.db")

    if run_server is None:
        from uvicorn import run as run_server

    run_server("app.main:app", host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
