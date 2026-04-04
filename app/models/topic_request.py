from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TopicRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    topic: str = Field(min_length=1)
    directions: list[str]
    count_per_direction: int = Field(gt=0)
    style_rules: list[str] = Field(default_factory=list)

    @field_validator("directions")
    @classmethod
    def validate_directions(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("directions must be a non-empty list.")
        return cleaned
