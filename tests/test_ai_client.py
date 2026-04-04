from __future__ import annotations

import httpx
import pytest

from app.generator.ai_client import AIClientError, generate_text


def test_generate_text_returns_raw_text_from_openai_style_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://example.com/v1/chat/completions")
        payload = {
            "choices": [
                {
                    "message": {
                        "content": '{"topic":"理财","items_by_direction":{"坑":["a","b"]}}'
                    }
                }
            ]
        }
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    text = generate_text(
        "prompt",
        model="test-model",
        base_url="https://example.com/v1",
        api_key="secret",
        timeout_seconds=10,
        max_retries=0,
        client=client,
    )

    assert text == '{"topic":"理财","items_by_direction":{"坑":["a","b"]}}'


def test_generate_text_retries_on_server_error_then_succeeds() -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(502, text="bad gateway")
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "final text"}}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    text = generate_text(
        "prompt",
        model="test-model",
        base_url="https://example.com/v1",
        api_key="secret",
        timeout_seconds=10,
        max_retries=1,
        client=client,
    )

    assert attempts["count"] == 2
    assert text == "final text"


def test_generate_text_raises_normalized_error_on_http_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="unauthorized")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(AIClientError, match="HTTP 401"):
        generate_text(
            "prompt",
            model="test-model",
            base_url="https://example.com/v1",
            api_key="secret",
            timeout_seconds=10,
            max_retries=0,
            client=client,
        )
