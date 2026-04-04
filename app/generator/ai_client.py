from __future__ import annotations

import json

import httpx


class AIClientError(RuntimeError):
    """Raised when the AI client cannot return normalized text."""


def _build_endpoint(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/chat/completions"


def _extract_text(data: dict) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AIClientError("AI response missing choices.")

    message = choices[0].get("message", {})
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str) and text:
                    text_parts.append(text)
        if text_parts:
            return "".join(text_parts)

    text = choices[0].get("text")
    if isinstance(text, str) and text.strip():
        return text

    raise AIClientError("AI response does not contain text content.")


def generate_text(
    prompt: str,
    *,
    model: str,
    base_url: str,
    api_key: str,
    timeout_seconds: int,
    max_retries: int,
    client: httpx.Client | None = None,
) -> str:
    last_error: Exception | None = None
    own_client = client is None
    http_client = client or httpx.Client(timeout=timeout_seconds)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        for attempt in range(max_retries + 1):
            try:
                response = http_client.post(
                    _build_endpoint(base_url),
                    headers=headers,
                    json=payload,
                )
            except httpx.RequestError as exc:
                last_error = AIClientError(f"AI request failed: {exc}")
                if attempt == max_retries:
                    raise last_error from exc
                continue

            if response.status_code >= 500:
                last_error = AIClientError(
                    f"AI service returned HTTP {response.status_code}: {response.text}"
                )
                if attempt == max_retries:
                    raise last_error
                continue

            if response.status_code >= 400:
                raise AIClientError(
                    f"AI request returned HTTP {response.status_code}: {response.text}"
                )

            try:
                data = response.json()
            except json.JSONDecodeError as exc:
                raise AIClientError("AI response is not valid JSON.") from exc

            return _extract_text(data)
    finally:
        if own_client:
            http_client.close()

    raise AIClientError(f"AI request failed after retries: {last_error}")
