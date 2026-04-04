from __future__ import annotations

import logging

from app.models import AppConfig
from app.models import TopicResult
from app.tasks.daily_topic_task import run_daily_topic_task


def make_config() -> AppConfig:
    return AppConfig(
        schedule_enabled=True,
        schedule_cron="30 8 * * *",
        topics=["理财", "AI使用"],
        directions=["坑", "盲区", "痛点", "疑问", "跨界话题"],
        count_per_direction=2,
        push_provider="feishu",
        push_webhook="https://example.com/webhook",
        ai_model="test-model",
        ai_base_url="https://example.com/v1",
        ai_timeout_seconds=30,
        ai_max_retries=1,
        ai_api_key="secret",
    )


def make_result(topic: str) -> TopicResult:
    return TopicResult(
        topic=topic,
        items_by_direction={
            "坑": ["a", "b"],
            "盲区": ["c", "d"],
            "痛点": ["e", "f"],
            "疑问": ["g", "h"],
            "跨界话题": ["理财 × 综艺：a", "从短视频看消费：b"],
        },
        raw_response="mock",
    )


def test_run_daily_topic_task_continues_after_single_topic_failure() -> None:
    config = make_config()
    logger = logging.getLogger("test_daily_topic_task")
    sent_topics: list[str] = []

    def fake_prompt_builder(request):
        return request.topic

    def fake_text_generator(prompt, **kwargs):
        if prompt == "AI使用":
            raise RuntimeError("mock ai failure")
        return '{"topic":"理财","items_by_direction":{"坑":["a","b"],"盲区":["c","d"],"痛点":["e","f"],"疑问":["g","h"],"跨界话题":["理财 × 综艺：a","从短视频看消费：b"]}}'

    def fake_parser(raw_text):
        return make_result("理财")

    def fake_validator(result, expected_count):
        assert expected_count == 2
        return result.model_copy(update={"is_valid": True, "errors": []})

    def fake_formatter(result, *, provider):
        return type(
            "Message",
            (),
            {
                "topic": result.topic,
                "title": f"{result.topic}每日选题",
                "body": "body",
                "provider": provider,
            },
        )()

    def fake_notify(message, *, webhook, timeout_seconds):
        sent_topics.append(message.topic)

    summary = run_daily_topic_task(
        config,
        logger=logger,
        text_generator=fake_text_generator,
        prompt_builder=fake_prompt_builder,
        result_parser=fake_parser,
        result_validator=fake_validator,
        message_formatter=fake_formatter,
        feishu_notifier=fake_notify,
    )

    assert summary["total_topics"] == 2
    assert summary["success_count"] == 1
    assert summary["failure_count"] == 1
    assert summary["succeeded_topics"] == ["理财"]
    assert sent_topics == ["理财"]
    assert summary["failed_topics"][0]["topic"] == "AI使用"


def test_run_daily_topic_task_returns_failure_for_invalid_result() -> None:
    config = make_config().model_copy(update={"topics": ["理财"]})

    def fake_prompt_builder(request):
        return request.topic

    def fake_text_generator(prompt, **kwargs):
        return "raw"

    def fake_parser(raw_text):
        return make_result("理财")

    def fake_validator(result, expected_count):
        return result.model_copy(update={"is_valid": False, "errors": ["bad result"]})

    summary = run_daily_topic_task(
        config,
        logger=logging.getLogger("test_daily_topic_task_invalid"),
        text_generator=fake_text_generator,
        prompt_builder=fake_prompt_builder,
        result_parser=fake_parser,
        result_validator=fake_validator,
        message_formatter=lambda result, *, provider: None,
        feishu_notifier=lambda message, *, webhook, timeout_seconds: None,
    )

    assert summary["success_count"] == 0
    assert summary["failure_count"] == 1
    assert summary["failed_topics"][0]["error"] == "bad result"
