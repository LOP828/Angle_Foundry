from __future__ import annotations

import os

from app.generator.ai_client import generate_text
from app.messaging.feishu_notifier import notify
from app.messaging.formatter import format_push_message
from app.models import TopicResult


REQUIRED_ENV_VARS = (
    "ANGLE_FOUNDRY_AI_BASE_URL",
    "ANGLE_FOUNDRY_AI_MODEL",
    "ANGLE_FOUNDRY_API_KEY",
    "FEISHU_WEBHOOK",
)


def _load_required_env() -> dict[str, str]:
    values: dict[str, str] = {}
    missing: list[str] = []

    for name in REQUIRED_ENV_VARS:
        value = os.getenv(name)
        if value:
            values[name] = value
        else:
            missing.append(name)

    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            "Missing required environment variables: "
            f"{missing_text}. See .env.example for the full list."
        )

    return values


def main() -> int:
    env = _load_required_env()
    timeout_seconds = int(os.getenv("ANGLE_FOUNDRY_AI_TIMEOUT_SECONDS", "30"))
    max_retries = int(os.getenv("ANGLE_FOUNDRY_AI_MAX_RETRIES", "1"))

    ai_text = generate_text(
        "请只返回一句不超过20字的中文短句，不要 markdown，不要引号，不要解释。",
        model=env["ANGLE_FOUNDRY_AI_MODEL"],
        base_url=env["ANGLE_FOUNDRY_AI_BASE_URL"],
        api_key=env["ANGLE_FOUNDRY_API_KEY"],
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    ).strip()

    result = TopicResult(
        topic="真实联调",
        items_by_direction={
            "坑": [f"AI返回短句：{ai_text}", "联调占位：检查 AI 文本是否成功回传"],
            "盲区": ["联调占位：检查 formatter 排版", "联调占位：检查纯文本换行"],
            "痛点": ["联调占位：检查 webhook 可达性", "联调占位：检查返回码处理"],
            "疑问": ["联调占位：AI 是否成功请求一次", "联调占位：飞书是否成功外发"],
            "跨界话题": [
                "真实联调 × 飞书机器人：一次最小外发验证",
                "AI调用 × 消息推送：链路是否真正打通",
            ],
        },
        raw_response=ai_text,
        is_valid=True,
    )
    message = format_push_message(result, provider="feishu", title="Angle Foundry 真实联调")
    notify(message, webhook=env["FEISHU_WEBHOOK"], timeout_seconds=10)

    print("ai_text:", ai_text)
    print("feishu_send: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
