from __future__ import annotations

import httpx
import pytest

from app.messaging.feishu_notifier import FeishuNotifierError, notify
from app.messaging.formatter import format_push_message
from app.models import TopicResult


def make_message_text():
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
    return format_push_message(result, provider="feishu")


def test_notify_sends_feishu_text_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://example.com/feishu")
        payload = request.read().decode("utf-8")
        assert '"msg_type":"text"' in payload
        assert "理财每日选题" in payload
        assert "领域：理财" in payload
        return httpx.Response(200, json={"code": 0, "msg": "success"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    notify(
        make_message_text(),
        webhook="https://example.com/feishu",
        timeout_seconds=10,
        client=client,
    )


def test_notify_raises_clear_error_on_http_status_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="server error")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(FeishuNotifierError, match="HTTP 500"):
        notify(
            make_message_text(),
            webhook="https://example.com/feishu",
            timeout_seconds=10,
            client=client,
        )


def test_notify_raises_clear_error_on_feishu_code_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"code": 19024, "msg": "invalid webhook"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(FeishuNotifierError, match="code 19024: invalid webhook"):
        notify(
            make_message_text(),
            webhook="https://example.com/feishu",
            timeout_seconds=10,
            client=client,
        )


def test_minimal_formatter_and_notifier_integration_with_mock_transport() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.read().decode("utf-8")
        return httpx.Response(200, json={"code": 0, "msg": "success"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    message = make_message_text()

    notify(
        message,
        webhook="https://example.com/feishu",
        timeout_seconds=10,
        client=client,
    )

    assert "理财每日选题" in captured["body"]
    assert "跨界话题" in captured["body"]
