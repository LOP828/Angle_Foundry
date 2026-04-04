from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AppConfig(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    allowed_directions: ClassVar[tuple[str, ...]] = (
        "坑",
        "盲区",
        "痛点",
        "疑问",
        "跨界话题",
    )

    schedule_enabled: bool
    schedule_cron: str = Field(min_length=1)
    topics: list[str]
    directions: list[str]
    count_per_direction: int = Field(gt=0)
    push_provider: Literal["feishu", "wecom"]
    push_webhook: str = Field(min_length=1)
    ai_model: str = Field(min_length=1)
    ai_base_url: str = Field(min_length=1)
    ai_timeout_seconds: int = Field(gt=0)
    ai_max_retries: int = Field(ge=0)
    ai_api_key: str = Field(min_length=1)

    @field_validator("topics")
    @classmethod
    def validate_topics(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("topics must be a non-empty list.")
        return cleaned

    @field_validator("directions")
    @classmethod
    def validate_directions(cls, value: list[str]) -> list[str]:
        if value != list(cls.allowed_directions):
            allowed = " / ".join(cls.allowed_directions)
            raise ValueError(f"directions must be exactly: {allowed}")
        return value
