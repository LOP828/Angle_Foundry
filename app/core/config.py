from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
import tomllib
from typing import Any

from app.models import AppConfig

DEFAULT_CONFIG_PATH = Path("config/config.toml")


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def _flatten_config(data: dict[str, Any], api_key: str) -> dict[str, Any]:
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
        "ai_api_key": api_key,
    }


def load_config(config_path: str | Path | None = None) -> AppConfig:
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    api_key = os.getenv("ANGLE_FOUNDRY_API_KEY")
    if not api_key:
        raise ValueError("Environment variable ANGLE_FOUNDRY_API_KEY is required.")

    data = _read_toml(path)
    return AppConfig.model_validate(_flatten_config(data, api_key=api_key))


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return load_config()
