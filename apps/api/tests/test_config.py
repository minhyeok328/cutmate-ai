from typing import cast

import pytest

from app.core.config import get_public_runtime_config, get_settings


def teardown_function() -> None:
    get_settings.cache_clear()


def test_default_settings_are_local_first() -> None:
    settings = get_settings()

    assert settings.default_llm == "Qwen/Qwen3-8B"
    assert settings.quality_llm == "openai/gpt-oss-20b"
    assert settings.external_api_mode == "disabled"
    assert settings.max_duration_seconds == 1200
    assert settings.max_upload_bytes == 2_147_483_648


def test_settings_include_tauri_desktop_origins() -> None:
    settings = get_settings()
    assert "tauri://localhost" in settings.cors_origins
    assert settings.app_url in settings.cors_origins


def test_public_runtime_config_does_not_require_openai_api_key() -> None:
    config = get_public_runtime_config()

    assert config["quality_mode"] == {
        "model": "openai/gpt-oss-20b",
        "execution": "self-hosted local inference",
        "api_key_required": False,
    }
    assert "OPENAI_API_KEY" not in str(config)


def test_invalid_model_and_external_api_env_values_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CUTMATE_DEFAULT_LLM", "untrusted/model")
    monkeypatch.setenv("CUTMATE_QUALITY_LLM", "remote-api-model")
    monkeypatch.setenv("CUTMATE_LLM_RUNTIME", "remote-runtime")
    monkeypatch.setenv("CUTMATE_EXTERNAL_API_MODE", "enabled")
    get_settings.cache_clear()

    settings = get_settings()
    config = get_public_runtime_config()

    assert settings.default_llm == "Qwen/Qwen3-8B"
    assert settings.quality_llm == "openai/gpt-oss-20b"
    assert settings.llm_runtime == "ollama"
    assert settings.external_api_mode == "disabled"
    assert config["external_api_enabled"] is False
    quality_mode = cast(dict[str, object], config["quality_mode"])
    assert quality_mode["api_key_required"] is False


def test_local_paths_reject_absolute_and_traversal_env_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CUTMATE_STORAGE_DIR", "C:/Users/MIN/Videos")
    monkeypatch.setenv("CUTMATE_SQLITE_PATH", "../cutmate.db")
    monkeypatch.setenv("CUTMATE_MODEL_DIR", "~/models")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.storage_dir == ".cutmate/storage"
    assert settings.sqlite_path == ".cutmate/cutmate.db"
    assert settings.model_dir == ".cutmate/models"


def test_upload_limit_env_value_must_match_fixed_mvp_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CUTMATE_MAX_UPLOAD_BYTES", "5")
    get_settings.cache_clear()

    assert get_settings().max_upload_bytes == 2_147_483_648
