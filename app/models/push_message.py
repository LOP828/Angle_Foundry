from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PushMessage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    provider: Literal["feishu", "wecom"]
    topic: str = Field(min_length=1)
