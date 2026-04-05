from __future__ import annotations

from app.generator.prompt_builder import build_prompt
from app.models import TopicRequest


def test_build_prompt_is_stable_and_includes_json_only_contract() -> None:
    request = TopicRequest(
        topic="理财",
        directions=["坑", "盲区", "痛点", "疑问", "跨界话题"],
        count_per_direction=2,
        style_rules=["标题不要空泛", "尽量贴近日常表达"],
    )

    prompt_a = build_prompt(request)
    prompt_b = build_prompt(request)

    assert prompt_a == prompt_b
    assert "只返回 JSON 本体" in prompt_a
    assert "不要使用 Markdown" in prompt_a
    assert "不要使用 ```json 代码块" in prompt_a
    assert '"topic": "理财"' in prompt_a
    assert '"跨界话题": ["题目1", "题目2"]' in prompt_a
    assert "不能退化成普通疑问或普通痛点" in prompt_a
    assert "标题不要空泛" in prompt_a
    assert "尽量贴近日常表达" in prompt_a


def test_build_prompt_includes_recent_title_dedup_constraint() -> None:
    request = TopicRequest(
        topic="理财",
        directions=["坑", "盲区", "痛点", "疑问", "跨界话题"],
        count_per_direction=2,
    )

    prompt = build_prompt(
        request,
        recent_titles=["年轻人最容易踩的理财坑", "为什么你越记账越焦虑"],
    )

    assert "以下标题最近已推送，禁止重复生成" in prompt
    assert "- 年轻人最容易踩的理财坑" in prompt
    assert "- 为什么你越记账越焦虑" in prompt


def test_build_prompt_omits_recent_title_block_when_recent_titles_is_empty() -> None:
    request = TopicRequest(
        topic="理财",
        directions=["坑", "盲区", "痛点", "疑问", "跨界话题"],
        count_per_direction=2,
    )

    prompt = build_prompt(request, recent_titles=[])

    assert "以下标题最近已推送，禁止重复生成" not in prompt
