from __future__ import annotations

from app.models import AppConfig
from app.models import TopicResult

_PUNCT_TRANSLATION = str.maketrans(
    {
        "，": ",",
        "。": ".",
        "！": "!",
        "？": "?",
        "；": ";",
        "：": ":",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "（": "(",
        "）": ")",
        "【": "[",
        "】": "]",
        "《": "<",
        "》": ">",
        "〈": "<",
        "〉": ">",
        "、": ",",
        "—": "-",
        "…": "...",
        "·": ".",
        "×": "x",
    }
)


def _has_cross_topic_signal(item: str) -> bool:
    signal_tokens = (
        "×",
        "x",
        "X",
        "vs",
        "VS",
        "与",
        "和",
        "从",
        "看",
        "借",
        "用",
        "里的",
        "中的",
    )
    external_keywords = (
        "人物",
        "作品",
        "歌曲",
        "电影",
        "电视剧",
        "综艺",
        "明星",
        "品牌",
        "行业",
        "热点",
        "现象",
        "平台",
        "短视频",
        "直播",
        "社交媒体",
        "职场",
        "婚姻",
        "校园",
        "体育",
        "游戏",
        "小说",
        "节日",
        "城市",
        "消费",
        "餐饮",
        "眼镜",
    )
    return any(token in item for token in signal_tokens) or any(
        keyword in item for keyword in external_keywords
    )


def _normalize_title(value: str) -> str:
    return value.strip().translate(_PUNCT_TRANSLATION).casefold()


def validate_topic_result(
    result: TopicResult,
    expected_count: int,
    recent_titles: list[str] | None = None,
) -> TopicResult:
    errors: list[str] = []
    allowed_directions = list(AppConfig.allowed_directions)
    recent_title_set = {
        normalized
        for title in (recent_titles or [])
        if isinstance(title, str)
        for normalized in [_normalize_title(title)]
        if normalized
    }

    if expected_count <= 0:
        raise ValueError("expected_count must be greater than 0.")

    if not result.topic.strip():
        errors.append("topic must be a non-empty string.")

    if not result.items_by_direction:
        errors.append("items_by_direction must not be empty.")

    actual_directions = list(result.items_by_direction.keys())
    if actual_directions != allowed_directions:
        errors.append(
            "items_by_direction must contain exactly 5 directions in order: "
            + " / ".join(allowed_directions)
        )

    for direction in allowed_directions:
        items = result.items_by_direction.get(direction)
        if not isinstance(items, list):
            errors.append(f"{direction} must be a list of strings.")
            continue

        if len(items) != expected_count:
            errors.append(
                f"{direction} must contain {expected_count} items, got {len(items)}."
            )

        if len(items) == 0:
            errors.append(f"{direction} must contain at least 1 item.")

        for index, item in enumerate(items, start=1):
            if not isinstance(item, str) or not item.strip():
                errors.append(f"{direction}[{index}] must be a non-empty string.")
                continue

            if _normalize_title(item) in recent_title_set:
                errors.append(
                    f"[history_duplicate] {direction}[{index}] duplicates a recent title."
                )

    cross_items = result.items_by_direction.get("跨界话题", [])
    if isinstance(cross_items, list):
        for index, item in enumerate(cross_items, start=1):
            if isinstance(item, str) and item.strip() and not _has_cross_topic_signal(item):
                errors.append(
                    f"跨界话题[{index}] lacks a clear cross-domain signal and may be off-topic."
                )

    return result.model_copy(update={"is_valid": not errors, "errors": errors})
