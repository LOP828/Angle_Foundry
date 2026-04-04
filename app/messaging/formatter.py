from __future__ import annotations

from app.models import AppConfig
from app.models import PushMessage, TopicResult


def format_push_message(
    result: TopicResult,
    *,
    provider: str = "feishu",
    title: str | None = None,
) -> PushMessage:
    lines = [f"领域：{result.topic}", ""]

    for direction in AppConfig.allowed_directions:
        lines.append(direction)
        for index, item in enumerate(result.items_by_direction.get(direction, []), start=1):
            lines.append(f"{index}. {item}")
        lines.append("")

    body = "\n".join(lines).rstrip()

    return PushMessage(
        title=title or f"{result.topic}每日选题",
        body=body,
        provider=provider,
        topic=result.topic,
    )
