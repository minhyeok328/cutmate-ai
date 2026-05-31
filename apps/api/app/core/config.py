import os
from dataclasses import dataclass
from functools import lru_cache

SUPPORTED_FORMATS = ("mp4", "mov", "m4v")
ANALYSIS_MODES = ("light", "standard", "quality")
DEFAULT_LLM = "Qwen/Qwen3-8B"
QUALITY_LLM = "openai/gpt-oss-20b"
LLM_RUNTIME = "ollama"
EXTERNAL_API_MODE = "disabled"
MAX_UPLOAD_BYTES = 2_147_483_648


@dataclass(frozen=True)
class Settings:
    app_name: str = "CutMate AI"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    storage_dir: str = ".cutmate/storage"
    sqlite_path: str = ".cutmate/cutmate.db"
    model_dir: str = ".cutmate/models"
    default_llm: str = DEFAULT_LLM
    quality_llm: str = QUALITY_LLM
    llm_runtime: str = LLM_RUNTIME
    external_api_mode: str = EXTERNAL_API_MODE
    max_duration_seconds: int = 20 * 60
    max_upload_bytes: int = MAX_UPLOAD_BYTES
    desktop_app_origins: tuple[str, ...] = ("tauri://localhost", "http://tauri.localhost")

    @property
    def cors_origins(self) -> list[str]:
        return [self.app_url, *self.desktop_app_origins]


def _read_env(name: str, fallback: str) -> str:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return fallback
    return value.strip()


def _read_allowlisted_env(name: str, allowed_value: str) -> str:
    value = _read_env(name, allowed_value)
    if value != allowed_value:
        return allowed_value
    return value


def _read_allowlisted_int_env(name: str, allowed_value: int) -> int:
    value = _read_env(name, str(allowed_value))
    try:
        parsed = int(value)
    except ValueError:
        return allowed_value
    if parsed != allowed_value:
        return allowed_value
    return parsed


def _is_safe_relative_path(value: str) -> bool:
    normalized = value.replace("\\", "/").strip()
    if normalized in {"", ".", ".."}:
        return False
    if normalized.startswith(("/", "~")):
        return False
    if ":" in normalized.split("/", maxsplit=1)[0]:
        return False
    return ".." not in normalized.split("/")


def _read_relative_path_env(name: str, fallback: str) -> str:
    value = _read_env(name, fallback)
    if not _is_safe_relative_path(value):
        return fallback
    return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_url=_read_env("CUTMATE_APP_URL", Settings.app_url),
        api_url=_read_env("CUTMATE_API_URL", Settings.api_url),
        storage_dir=_read_relative_path_env("CUTMATE_STORAGE_DIR", Settings.storage_dir),
        sqlite_path=_read_relative_path_env("CUTMATE_SQLITE_PATH", Settings.sqlite_path),
        model_dir=_read_relative_path_env("CUTMATE_MODEL_DIR", Settings.model_dir),
        default_llm=_read_allowlisted_env("CUTMATE_DEFAULT_LLM", DEFAULT_LLM),
        quality_llm=_read_allowlisted_env("CUTMATE_QUALITY_LLM", QUALITY_LLM),
        llm_runtime=_read_allowlisted_env("CUTMATE_LLM_RUNTIME", LLM_RUNTIME),
        external_api_mode=_read_allowlisted_env("CUTMATE_EXTERNAL_API_MODE", EXTERNAL_API_MODE),
        max_upload_bytes=_read_allowlisted_int_env("CUTMATE_MAX_UPLOAD_BYTES", MAX_UPLOAD_BYTES),
    )


def get_public_runtime_config() -> dict[str, object]:
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "app_url": settings.app_url,
        "api_url": settings.api_url,
        "max_duration_seconds": settings.max_duration_seconds,
        "max_upload_bytes": settings.max_upload_bytes,
        "supported_formats": SUPPORTED_FORMATS,
        "analysis_modes": ANALYSIS_MODES,
        "default_llm": settings.default_llm,
        "llm_runtime": settings.llm_runtime,
        "quality_mode": {
            "model": settings.quality_llm,
            "execution": "self-hosted local inference",
            "api_key_required": False,
        },
        "external_api_mode": settings.external_api_mode,
        "external_api_enabled": settings.external_api_mode == "enabled",
    }
