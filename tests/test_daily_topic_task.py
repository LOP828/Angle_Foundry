from __future__ import annotations

import logging

from app.generator.validator import validate_topic_result
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

    def fake_prompt_builder(request, recent_titles=None):
        return request.topic

    def fake_text_generator(prompt, **kwargs):
        if prompt == "AI使用":
            raise RuntimeError("mock ai failure")
        return '{"topic":"理财","items_by_direction":{"坑":["a","b"],"盲区":["c","d"],"痛点":["e","f"],"疑问":["g","h"],"跨界话题":["理财 × 综艺：a","从短视频看消费：b"]}}'

    def fake_parser(raw_text):
        return make_result("理财")

    def fake_validator(result, expected_count, recent_titles=None):
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
        history_loader=lambda days=1: [],
        history_appender=lambda **kwargs: None,
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

    def fake_prompt_builder(request, recent_titles=None):
        return request.topic

    def fake_text_generator(prompt, **kwargs):
        return "raw"

    def fake_parser(raw_text):
        return make_result("理财")

    def fake_validator(result, expected_count, recent_titles=None):
        return result.model_copy(update={"is_valid": False, "errors": ["bad result"]})

    summary = run_daily_topic_task(
        config,
        logger=logging.getLogger("test_daily_topic_task_invalid"),
        text_generator=fake_text_generator,
        prompt_builder=fake_prompt_builder,
        result_parser=fake_parser,
        result_validator=fake_validator,
        history_loader=lambda days=1: [],
        history_appender=lambda **kwargs: None,
        message_formatter=lambda result, *, provider: None,
        feishu_notifier=lambda message, *, webhook, timeout_seconds: None,
    )

    assert summary["success_count"] == 0
    assert summary["failure_count"] == 1
    assert summary["failed_topics"][0]["error"] == "bad result"


def test_run_daily_topic_task_retries_once_after_parser_failure_then_succeeds() -> None:
    config = make_config().model_copy(update={"topics": ["理财"]})
    parser_calls = 0
    formatted_topics: list[str] = []
    sent_topics: list[str] = []

    def fake_prompt_builder(request, recent_titles=None):
        return request.topic

    def fake_text_generator(prompt, **kwargs):
        return f"raw-{prompt}"

    def fake_parser(raw_text):
        nonlocal parser_calls
        parser_calls += 1
        if parser_calls == 1:
            raise ValueError("bad json")
        return make_result("理财")

    def fake_validator(result, expected_count, recent_titles=None):
        return result.model_copy(update={"is_valid": True, "errors": []})

    def fake_formatter(result, *, provider):
        formatted_topics.append(result.topic)
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
        logger=logging.getLogger("test_daily_topic_task_retry_success"),
        text_generator=fake_text_generator,
        prompt_builder=fake_prompt_builder,
        result_parser=fake_parser,
        result_validator=fake_validator,
        history_loader=lambda days=1: [],
        history_appender=lambda **kwargs: None,
        message_formatter=fake_formatter,
        feishu_notifier=fake_notify,
    )

    assert parser_calls == 2
    assert summary["success_count"] == 1
    assert summary["failure_count"] == 0
    assert summary["succeeded_topics"] == ["理财"]
    assert summary["failed_topics"] == []
    assert formatted_topics == ["理财"]
    assert sent_topics == ["理财"]


def test_run_daily_topic_task_returns_failure_after_retrying_invalid_result() -> None:
    config = make_config().model_copy(update={"topics": ["理财"]})
    validator_calls = 0

    def fake_prompt_builder(request, recent_titles=None):
        return request.topic

    def fake_text_generator(prompt, **kwargs):
        return "raw"

    def fake_parser(raw_text):
        return make_result("理财")

    def fake_validator(result, expected_count, recent_titles=None):
        nonlocal validator_calls
        validator_calls += 1
        return result.model_copy(
            update={"is_valid": False, "errors": [f"bad result {validator_calls}"]}
        )

    summary = run_daily_topic_task(
        config,
        logger=logging.getLogger("test_daily_topic_task_retry_failure"),
        text_generator=fake_text_generator,
        prompt_builder=fake_prompt_builder,
        result_parser=fake_parser,
        result_validator=fake_validator,
        history_loader=lambda days=1: [],
        history_appender=lambda **kwargs: None,
        message_formatter=lambda result, *, provider: None,
        feishu_notifier=lambda message, *, webhook, timeout_seconds: None,
    )

    assert validator_calls == 2
    assert summary["success_count"] == 0
    assert summary["failure_count"] == 1
    assert summary["failed_topics"][0]["topic"] == "理财"
    assert summary["failed_topics"][0]["error"] == "bad result 2"


def test_run_daily_topic_task_retries_once_after_history_duplicate_then_succeeds() -> None:
    config = make_config().model_copy(update={"topics": ["理财"]})
    prompt_recent_titles: list[list[str]] = []
    validator_recent_titles: list[list[str]] = []
    text_calls = 0
    history_records: list[dict[str, object]] = []

    def fake_prompt_builder(request, recent_titles=None):
        prompt_recent_titles.append(list(recent_titles or []))
        return request.topic

    def fake_text_generator(prompt, **kwargs):
        nonlocal text_calls
        text_calls += 1
        return f"raw-{text_calls}"

    def fake_parser(raw_text):
        return make_result("理财")

    def fake_validator(result, expected_count, recent_titles=None):
        validator_recent_titles.append(list(recent_titles or []))
        if len(validator_recent_titles) == 1:
            return result.model_copy(
                update={
                    "is_valid": False,
                    "errors": ["盲区[1] duplicates a recently sent title."],
                }
            )
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

    summary = run_daily_topic_task(
        config,
        logger=logging.getLogger("test_daily_topic_task_history_retry_success"),
        text_generator=fake_text_generator,
        prompt_builder=fake_prompt_builder,
        result_parser=fake_parser,
        result_validator=fake_validator,
        history_loader=lambda days=1: ["昨天的重复标题"],
        history_appender=lambda **kwargs: history_records.append(kwargs),
        message_formatter=fake_formatter,
        feishu_notifier=lambda message, *, webhook, timeout_seconds: None,
    )

    assert prompt_recent_titles == [["昨天的重复标题"]]
    assert validator_recent_titles == [["昨天的重复标题"], ["昨天的重复标题"]]
    assert text_calls == 2
    assert summary["success_count"] == 1
    assert summary["failure_count"] == 0
    assert len(history_records) == 10
    assert history_records[0]["topic"] == "理财"


def test_run_daily_topic_task_returns_failure_after_retrying_history_duplicate() -> None:
    config = make_config().model_copy(update={"topics": ["理财"]})
    validator_calls = 0
    history_records: list[dict[str, object]] = []

    def fake_prompt_builder(request, recent_titles=None):
        return request.topic

    def fake_text_generator(prompt, **kwargs):
        return "raw"

    def fake_parser(raw_text):
        return make_result("理财")

    def fake_validator(result, expected_count, recent_titles=None):
        nonlocal validator_calls
        validator_calls += 1
        return result.model_copy(
            update={
                "is_valid": False,
                "errors": ["盲区[1] duplicates a recently sent title."],
            }
        )

    summary = run_daily_topic_task(
        config,
        logger=logging.getLogger("test_daily_topic_task_history_retry_failure"),
        text_generator=fake_text_generator,
        prompt_builder=fake_prompt_builder,
        result_parser=fake_parser,
        result_validator=fake_validator,
        history_loader=lambda days=1: ["昨天的重复标题"],
        history_appender=lambda **kwargs: history_records.append(kwargs),
        message_formatter=lambda result, *, provider: None,
        feishu_notifier=lambda message, *, webhook, timeout_seconds: None,
    )

    assert validator_calls == 2
    assert summary["success_count"] == 0
    assert summary["failure_count"] == 1
    assert summary["failed_topics"][0]["error"] == "盲区[1] duplicates a recently sent title."
    assert history_records == []


def test_run_daily_topic_task_completes_history_dedup_retry_chain() -> None:
    config = make_config().model_copy(update={"topics": ["理财"]})
    prompt_recent_titles: list[list[str]] = []
    history_records: list[dict[str, object]] = []
    parser_calls = 0

    def fake_prompt_builder(request, recent_titles=None):
        prompt_recent_titles.append(list(recent_titles or []))
        return request.topic

    def fake_text_generator(prompt, **kwargs):
        return f"raw-{prompt}"

    def fake_parser(raw_text):
        nonlocal parser_calls
        parser_calls += 1
        if parser_calls == 1:
            return TopicResult(
                topic="理财",
                items_by_direction={
                    "坑": ["普通人理财最容易踩的坑是什么", "为什么跟风买基金容易亏"],
                    "盲区": ["很多人忽略的现金流盲区", "记账为什么不等于会理财"],
                    "痛点": ["工资不低却总存不下钱怎么办", "为什么越省钱越焦虑"],
                    "疑问": ["普通人该先存钱还是先投资", "年轻人要不要太早配置保险"],
                    "跨界话题": ["理财 × 短视频：为什么越刷越想买", "从奶茶联名看年轻人的消费决策"],
                },
                raw_response="duplicate",
            )

        return TopicResult(
            topic="理财",
            items_by_direction={
                "坑": ["普通人为什么越攒钱越没安全感", "基金定投最容易忽略的止损边界"],
                "盲区": ["存款稳定的人为什么也会现金流紧张", "记账很久却看不出消费结构问题"],
                "痛点": ["收入上涨后为什么还是留不住钱", "做了预算却总被临时消费打乱怎么办"],
                "疑问": ["普通人什么时候才算适合开始投资", "保险和应急金到底该先配哪一个"],
                "跨界话题": ["理财 × 外卖满减：为什么省了几块却更容易超支", "从演唱会抢票看年轻人的冲动消费逻辑"],
            },
            raw_response="unique",
        )

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

    summary = run_daily_topic_task(
        config,
        logger=logging.getLogger("test_daily_topic_task_history_dedup_chain"),
        text_generator=fake_text_generator,
        prompt_builder=fake_prompt_builder,
        result_parser=fake_parser,
        result_validator=validate_topic_result,
        history_loader=lambda days=1: ["很多人忽略的现金流盲区"],
        history_appender=lambda **kwargs: history_records.append(kwargs),
        message_formatter=fake_formatter,
        feishu_notifier=lambda message, *, webhook, timeout_seconds: None,
    )

    assert prompt_recent_titles == [["很多人忽略的现金流盲区"]]
    assert parser_calls == 2
    assert summary["success_count"] == 1
    assert summary["failure_count"] == 0
    assert summary["succeeded_topics"] == ["理财"]
    assert len(history_records) == 10
    assert history_records[0]["title"] == "普通人为什么越攒钱越没安全感"
    assert all(record["title"] != "很多人忽略的现金流盲区" for record in history_records)
