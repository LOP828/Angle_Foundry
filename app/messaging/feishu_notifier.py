from __future__ import annotations

import json

import httpx

from app.models import PushMessage


class FeishuNotifierError(RuntimeError):
    """Raised when a Feishu text message cannot be delivered."""


def notify(
    message: PushMessage,
    *,
    webhook: str,
    timeout_seconds: int = 10,
    client: httpx.Client | None = None,
) -> None:
    own_client = client is None
    http_client = client or httpx.Client(timeout=timeout_seconds)
    payload = {
        "msg_type": "text",
        "content": {"text": f"{message.title}\n\n{message.body}"},
    }

    try:
        try:
            response = http_client.post(webhook, json=payload)
        except httpx.RequestError as exc:
            raise FeishuNotifierError(f"Feishu request failed: {exc}") from exc

        if response.status_code >= 400:
            raise FeishuNotifierError(
                f"Feishu webhook returned HTTP {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise FeishuNotifierError("Feishu response is not valid JSON.") from exc

        code = data.get("code")
        if code != 0:
            msg = data.get("msg") or "unknown error"
            raise FeishuNotifierError(f"Feishu send failed with code {code}: {msg}")
    finally:
        if own_client:
            http_client.close()
