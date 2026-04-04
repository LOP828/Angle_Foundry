from __future__ import annotations

import json

from app.models import TopicResult


def _extract_json_object(raw_response: str) -> str:
    start = raw_response.find("{")
    if start == -1:
        raise ValueError("No JSON object found in raw response.")

    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(raw_response)):
        char = raw_response[index]
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return raw_response[start : index + 1]

    raise ValueError("Incomplete JSON object in raw response.")


def parse_topic_result(raw_response: str) -> TopicResult:
    json_text = _extract_json_object(raw_response)
    data = json.loads(json_text)

    if "items_by_direction" not in data:
        items_by_direction = {
            key: value
            for key, value in data.items()
            if key not in {"topic", "raw_response", "is_valid", "errors"}
        }
        data = {
            "topic": data.get("topic", ""),
            "items_by_direction": items_by_direction,
        }

    data["raw_response"] = raw_response
    data.setdefault("is_valid", False)
    data.setdefault("errors", [])

    return TopicResult.model_validate(data)
