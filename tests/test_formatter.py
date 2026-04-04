from __future__ import annotations

from app.messaging.formatter import format_push_message
from app.models import TopicResult


def test_format_push_message_builds_plain_text_by_topic_and_directions() -> None:
    result = TopicResult(
        topic="理财",
        items_by_direction={
            "坑": ["普通人理财最容易踩的坑", "为什么跟风买基金容易亏"],
            "盲区": ["很多人忽略的现金流盲区", "记账为什么不等于会理财"],
            "痛点": ["工资不低却总存不下钱怎么办", "为什么越省钱越焦虑"],
            "疑问": ["普通人该先存钱还是先投资", "年轻人要不要太早配置保险"],
            "跨界话题": ["理财 × 短视频：为什么越刷越想买", "从奶茶联名看年轻人的消费决策"],
        },
        raw_response="mock",
        is_valid=True,
    )

    message = format_push_message(result, provider="feishu")

    assert message.title == "理财每日选题"
    assert message.provider == "feishu"
    assert message.body.startswith("领域：理财")
    assert "坑\n1. 普通人理财最容易踩的坑" in message.body
    assert "跨界话题\n1. 理财 × 短视频：为什么越刷越想买" in message.body
    assert "2. 从奶茶联名看年轻人的消费决策" in message.body
