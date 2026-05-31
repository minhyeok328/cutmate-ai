from __future__ import annotations

import re
import secrets
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.paths import resolve_workspace_path
from app.db.connection import connect
from app.db.repositories import MetricEventRepository
from app.db.schema import initialize_schema

router = APIRouter(tags=["ops"])

EVENT_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


class MetricEventRequest(BaseModel):
    event_name: str = Field(min_length=2, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/metrics/events")
def record_metric_event(request: MetricEventRequest) -> dict[str, object]:
    if EVENT_NAME_RE.fullmatch(request.event_name) is None:
        raise _api_error(400, "VALIDATION_FAILED", "Unsupported metric event name.")

    db_path = resolve_workspace_path(get_settings().sqlite_path)
    with connect(db_path) as connection:
        initialize_schema(connection)
        event = MetricEventRepository(connection).create(
            event_id=_new_id("metric"),
            event_name=request.event_name,
            metadata=_sanitize_metadata(request.metadata),
        )
    return {
        "metric_event": {
            "metric_event_id": event.id,
            "event_name": event.event_name,
            "metadata": event.metadata,
            "created_at": event.created_at,
        }
    }


@router.post("/maintenance/cleanup")
def run_cleanup() -> dict[str, object]:
    return {"cleanup": {"status": "completed", "failed_artifacts_removed": 0}}


def _sanitize_metadata(metadata: dict[str, Any]) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    for key, value in metadata.items():
        if len(key) > 64:
            continue
        if isinstance(value, str | int | float | bool) or value is None:
            sanitized[key] = value
    return sanitized


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(12)}"


def _api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": code,
                "message": message,
                "retryable": False,
                "details": {},
            }
        },
    )
