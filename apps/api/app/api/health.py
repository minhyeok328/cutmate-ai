from typing import Any

from fastapi import APIRouter

from app.core.config import get_public_runtime_config, get_settings

router = APIRouter(tags=["runtime"])


@router.get("/health")
def health_check() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "local_worker": "available",
        "local_first": True,
        "external_api_mode": settings.external_api_mode,
    }


@router.get("/config/runtime")
def runtime_config() -> dict[str, Any]:
    return get_public_runtime_config()
