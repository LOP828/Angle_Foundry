from __future__ import annotations

from app.models import TopicRequest


def build_prompt(
    request: TopicRequest, recent_titles: list[str] | None = None
) -> str:
    directions = "、".join(request.directions)
    style_rules = (
        "\n".join(f"- {rule}" for rule in request.style_rules)
        if request.style_rules
        else "- 标题要具体、清晰、可直接作为文章选题"
    )
    recent_titles_block = ""
    if recent_titles:
        recent_title_lines = "\n".join(f"- {title}" for title in recent_titles)
        recent_titles_block = (
            "以下标题最近已推送，禁止重复生成：\n"
            f"{recent_title_lines}\n"
        )
    json_shape = ",\n".join(
        f'    "{direction}": ["题目1", "题目2"]' for direction in request.directions
    )

    return (
        f"你是一个内容选题策划助手。\n"
        f"请围绕主题“{request.topic}”，按以下 {len(request.directions)} 个方向生成选题：{directions}。\n"
        f"每个方向必须生成 {request.count_per_direction} 个题目。\n"
        "前四个方向必须围绕主题内部问题展开。\n"
        "“跨界话题”必须把该主题与大众熟悉的人物、作品、热点、生活场景、行业或社会现象结合，"
        "形成明显跨界切口；不能写成泛泛的主题延伸，不能退化成普通疑问或普通痛点。\n"
        "输出必须是严格 JSON，对象结构如下：\n"
        "{\n"
        f'  "topic": "{request.topic}",\n'
        '  "items_by_direction": {\n'
        f"{json_shape}\n"
        "  }\n"
        "}\n"
        "只返回 JSON 本体，不要附加任何解释，不要使用 Markdown，不要使用 ```json 代码块。\n"
        f"{recent_titles_block}"
        "标题风格要求：\n"
        f"{style_rules}\n"
    )
