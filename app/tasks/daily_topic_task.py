from __future__ import annotations

import logging

from app.generator.ai_client import generate_text
from app.generator.parser import parse_topic_result
from app.generator.prompt_builder import build_prompt
from app.generator.validator import validate_topic_result
from app.messaging.feishu_notifier import notify as feishu_notify
from app.messaging.formatter import format_push_message
from app.models import AppConfig
from app.models import TopicRequest


def run_daily_topic_task(
    config: AppConfig,
    *,
    logger: logging.Logger | None = None,
    text_generator=generate_text,
    prompt_builder=build_prompt,
    result_parser=parse_topic_result,
    result_validator=validate_topic_result,
    message_formatter=format_push_message,
    feishu_notifier=feishu_notify,
) -> dict[str, object]:
    task_logger = logger or logging.getLogger("angle_foundry")
    summary: dict[str, object] = {
        "total_topics": len(config.topics),
        "success_count": 0,
        "failure_count": 0,
        "succeeded_topics": [],
        "failed_topics": [],
    }

    task_logger.info("Daily topic task started for %s topics.", len(config.topics))

    for topic in config.topics:
        task_logger.info("Processing topic '%s'.", topic)
        try:
            request = TopicRequest(
                topic=topic,
                directions=config.directions,
                count_per_direction=config.count_per_direction,
                style_rules=[],
            )
            prompt = prompt_builder(request)
            raw_text = text_generator(
                prompt,
                model=config.ai_model,
                base_url=config.ai_base_url,
                api_key=config.ai_api_key,
                timeout_seconds=config.ai_timeout_seconds,
                max_retries=config.ai_max_retries,
            )
            parsed_result = result_parser(raw_text)
            validated_result = result_validator(
                parsed_result,
                expected_count=config.count_per_direction,
            )
            if not validated_result.is_valid:
                raise RuntimeError("; ".join(validated_result.errors))

            message = message_formatter(
                validated_result,
                provider=config.push_provider,
            )
            if config.push_provider != "feishu":
                raise RuntimeError(
                    f"Push provider '{config.push_provider}' is not implemented yet."
                )

            feishu_notifier(
                message,
                webhook=config.push_webhook,
                timeout_seconds=min(config.ai_timeout_seconds, 10),
            )
            summary["success_count"] = int(summary["success_count"]) + 1
            succeeded_topics = list(summary["succeeded_topics"])
            succeeded_topics.append(topic)
            summary["succeeded_topics"] = succeeded_topics
            task_logger.info("Topic '%s' processed successfully.", topic)
        except Exception as exc:  # noqa: BLE001
            summary["failure_count"] = int(summary["failure_count"]) + 1
            failed_topics = list(summary["failed_topics"])
            failed_topics.append({"topic": topic, "error": str(exc)})
            summary["failed_topics"] = failed_topics
            task_logger.exception("Topic '%s' failed: %s", topic, exc)

    task_logger.info(
        "Daily topic task finished. total=%s success=%s failure=%s",
        summary["total_topics"],
        summary["success_count"],
        summary["failure_count"],
    )
    return summary
