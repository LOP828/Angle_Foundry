from __future__ import annotations

from app.generator.validator import validate_topic_result
from app.models import TopicResult


def make_result() -> TopicResult:
    return TopicResult(
        topic="理财",
        items_by_direction={
            "坑": ["普通人理财最容易踩的坑是什么", "为什么跟风买基金容易亏"],
            "盲区": ["很多人忽略的现金流盲区", "记账为什么不等于会理财"],
            "痛点": ["工资不低却总存不下钱怎么办", "为什么越省钱越焦虑"],
            "疑问": ["普通人该先存钱还是先投资", "年轻人要不要太早配置保险"],
            "跨界话题": ["理财 × 短视频：为什么越刷越想买", "从奶茶联名看年轻人的消费决策"],
        },
        raw_response="mock",
    )


def test_validate_topic_result_accepts_valid_result() -> None:
    result = validate_topic_result(make_result(), expected_count=2)

    assert result.is_valid is True
    assert result.errors == []


def test_validate_topic_result_rejects_invalid_structure() -> None:
    invalid = TopicResult(
        topic="理财",
        items_by_direction={
            "坑": ["普通人理财最容易踩的坑是什么", ""],
            "盲区": ["很多人忽略的现金流盲区"],
            "痛点": ["工资不低却总存不下钱怎么办", "为什么越省钱越焦虑"],
            "疑问": ["普通人该先存钱还是先投资", "年轻人要不要太早配置保险"],
        },
        raw_response="mock",
    )

    result = validate_topic_result(invalid, expected_count=2)

    assert result.is_valid is False
    assert any("exactly 5 directions" in error for error in result.errors)
    assert any("坑[2] must be a non-empty string" in error for error in result.errors)
    assert any("盲区 must contain 2 items" in error for error in result.errors)


def test_validate_topic_result_rejects_off_target_cross_topic_items() -> None:
    invalid = TopicResult(
        topic="理财",
        items_by_direction={
            "坑": ["普通人理财最容易踩的坑是什么", "为什么跟风买基金容易亏"],
            "盲区": ["很多人忽略的现金流盲区", "记账为什么不等于会理财"],
            "痛点": ["工资不低却总存不下钱怎么办", "为什么越省钱越焦虑"],
            "疑问": ["普通人该先存钱还是先投资", "年轻人要不要太早配置保险"],
            "跨界话题": ["普通人理财要注意什么", "为什么要尽早开始理财"],
        },
        raw_response="mock",
    )

    result = validate_topic_result(invalid, expected_count=2)

    assert result.is_valid is False
    assert any("cross-domain signal" in error for error in result.errors)


def test_validate_topic_result_rejects_direction_with_one_less_item() -> None:
    invalid = make_result().model_copy(
        update={
            "items_by_direction": {
                **make_result().items_by_direction,
                "盲区": ["很多人忽略的现金流盲区"],
            }
        }
    )

    result = validate_topic_result(invalid, expected_count=2)

    assert result.is_valid is False
    assert "盲区 must contain 2 items, got 1." in result.errors


def test_validate_topic_result_rejects_direction_with_one_extra_item() -> None:
    invalid = make_result().model_copy(
        update={
            "items_by_direction": {
                **make_result().items_by_direction,
                "痛点": [
                    "工资不低却总存不下钱怎么办",
                    "为什么越省钱越焦虑",
                    "为什么做预算还是会超支",
                ],
            }
        }
    )

    result = validate_topic_result(invalid, expected_count=2)

    assert result.is_valid is False
    assert "痛点 must contain 2 items, got 3." in result.errors


def test_validate_topic_result_rejects_equal_counts_when_not_matching_expected_count() -> None:
    invalid = TopicResult(
        topic="理财",
        items_by_direction={
            "坑": ["普通人理财最容易踩的坑是什么"],
            "盲区": ["很多人忽略的现金流盲区"],
            "痛点": ["工资不低却总存不下钱怎么办"],
            "疑问": ["普通人该先存钱还是先投资"],
            "跨界话题": ["理财 × 短视频：为什么越刷越想买"],
        },
        raw_response="mock",
    )

    result = validate_topic_result(invalid, expected_count=2)

    assert result.is_valid is False
    assert result.errors.count("坑 must contain 2 items, got 1.") == 1
    assert result.errors.count("盲区 must contain 2 items, got 1.") == 1
    assert result.errors.count("痛点 must contain 2 items, got 1.") == 1
    assert result.errors.count("疑问 must contain 2 items, got 1.") == 1
    assert result.errors.count("跨界话题 must contain 2 items, got 1.") == 1


def test_validate_topic_result_rejects_title_duplicated_from_yesterday_history() -> None:
    result = validate_topic_result(
        make_result(),
        expected_count=2,
        recent_titles=["很多人忽略的现金流盲区"],
    )

    assert result.is_valid is False
    assert "[history_duplicate] 盲区[1] duplicates a recent title." in result.errors


def test_validate_topic_result_rejects_title_with_only_punctuation_difference() -> None:
    result = validate_topic_result(
        make_result(),
        expected_count=2,
        recent_titles=["理财 × 短视频:为什么越刷越想买"],
    )

    assert result.is_valid is False
    assert "[history_duplicate] 跨界话题[1] duplicates a recent title." in result.errors


def test_validate_topic_result_does_not_false_positive_when_recent_titles_is_empty() -> None:
    result = validate_topic_result(
        make_result(),
        expected_count=2,
        recent_titles=[],
    )

    assert result.is_valid is True
    assert result.errors == []
