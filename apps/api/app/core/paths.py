from __future__ import annotations

from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]


def resolve_workspace_path(relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        raise ValueError("Workspace paths must be relative.")

    resolved = (WORKSPACE_ROOT / path).resolve(strict=False)
    try:
        resolved.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError("Workspace path escapes the app workspace.") from exc
    return resolved
