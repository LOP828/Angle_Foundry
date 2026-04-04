from __future__ import annotations

import pytest

from app.generator.parser import parse_topic_result


def test_parse_topic_result_extracts_json_from_wrapped_text() -> None:
    raw_response = """
这里是额外说明，请忽略。
{
  "topic": "理财",
  "items_by_direction": {
    "坑": ["普通人理财最容易踩的坑是什么", "为什么跟风买基金容易亏"],
    "盲区": ["很多人忽略的现金流盲区", "记账为什么不等于会理财"],
    "痛点": ["工资不低却总存不下钱怎么办", "为什么越省钱越焦虑"],
    "疑问": ["普通人该先存钱还是先投资", "年轻人要不要太早配置保险"],
    "跨界话题": ["理财 × 短视频：为什么越刷越想买", "从奶茶联名看年轻人的消费决策"]
  }
}
谢谢。
"""

    result = parse_topic_result(raw_response)

    assert result.topic == "理财"
    assert result.raw_response == raw_response
    assert result.items_by_direction["坑"][0] == "普通人理财最容易踩的坑是什么"
    assert result.items_by_direction["跨界话题"][1] == "从奶茶联名看年轻人的消费决策"


def test_parse_topic_result_supports_flat_direction_shape() -> None:
    raw_response = """
{
  "topic": "AI使用",
  "坑": ["把 AI 当搜索引擎", "只会堆提示词"],
  "盲区": ["不会给上下文", "不会拆任务"],
  "痛点": ["回答不稳定", "不知道怎么追问"],
  "疑问": ["AI 会不会替代新人岗位", "AI 生成内容能直接发吗"],
  "跨界话题": ["AI使用 × 综艺脚本：为什么套路感这么重", "从外卖平台评论看 AI 语气模仿"]
}
"""

    result = parse_topic_result(raw_response)

    assert result.topic == "AI使用"
    assert set(result.items_by_direction) == {"坑", "盲区", "痛点", "疑问", "跨界话题"}


def test_parse_topic_result_raises_when_json_missing() -> None:
    with pytest.raises(ValueError, match="No JSON object found"):
        parse_topic_result("没有任何结构化结果")
