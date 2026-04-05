from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
import tomllib
from typing import Any

from app.models import AppConfig

DEFAULT_CONFIG_PATH = Path("config/config.toml")
ENV_OVERRIDE_FIELDS = {
    "ANGLE_FOUNDRY_AI_MODEL": "ai_model",
    "ANGLE_FOUNDRY_AI_BASE_URL": "ai_base_url",
    "ANGLE_FOUNDRY_AI_TIMEOUT_SECONDS": "ai_timeout_seconds",
    "ANGLE_FOUNDRY_AI_MAX_RETRIES": "ai_max_retries",
    "FEISHU_WEBHOOK": "push_webhook",
    "ANGLE_FOUNDRY_API_KEY": "ai_api_key",
}
INT_OVERRIDE_FIELDS = {"ai_timeout_seconds", "ai_max_retries"}


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def _flatten_config(data: dict[str, Any]) -> dict[str, Any]:
    schedule = data.get("schedule", {})
    generator = data.get("generator", {})
    push = data.get("push", {})
    ai = data.get("ai", {})

    return {
        "schedule_enabled": schedule.get("enabled"),
        "schedule_cron": schedule.get("cron"),
        "topics": generator.get("topics"),
        "directions": generator.get("directions"),
        "count_per_direction": generator.get("count_per_direction"),
        "push_provider": push.get("provider"),
        "push_webhook": push.get("webhook"),
        "ai_model": ai.get("model"),
        "ai_base_url": ai.get("base_url"),
        "ai_timeout_seconds": ai.get("timeout_seconds"),
        "ai_max_retries": ai.get("max_retries"),
        "ai_api_key": ai.get("api_key"),
    }


def _apply_env_overrides(flat_config: dict[str, Any]) -> dict[str, Any]:
    overrides = dict(flat_config)
    for env_name, field_name in ENV_OVERRIDE_FIELDS.items():
        env_value = os.getenv(env_name)
        if env_value is None or env_value == "":
            continue

        if field_name in INT_OVERRIDE_FIELDS:
            overrides[field_name] = int(env_value)
        else:
            overrides[field_name] = env_value

    return overrides


def load_config(config_path: str | Path | None = None) -> AppConfig:
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    data = _read_toml(path)
    flat_config = _flatten_config(data)
    resolved_config = _apply_env_overrides(flat_config)
    return AppConfig.model_validate(resolved_config)


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return load_config()
