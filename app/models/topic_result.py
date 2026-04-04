from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TopicResult(BaseModel):
    model_config = ConfigDict()

    topic: str = Field(min_length=1)
    items_by_direction: dict[str, list[str]] = Field(default_factory=dict)
    raw_response: str = ""
    is_valid: bool = False
    errors: list[str] = Field(default_factory=list)
