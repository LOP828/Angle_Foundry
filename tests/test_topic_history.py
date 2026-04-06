from __future__ import annotations

from datetime import date

from app.history.topic_history import append_history
from app.history.topic_history import has_history_for_day
from app.history.topic_history import load_recent_titles


def test_append_history_writes_jsonl_record(tmp_path) -> None:
    history_path = tmp_path / "topic_history.jsonl"

    append_history(
        date_value=date(2026, 4, 5),
        topic="理财",
        direction="坑",
        title="年轻人最容易踩的理财坑",
        path=history_path,
    )

    assert (
        history_path.read_text(encoding="utf-8").strip()
        == '{"date": "2026-04-05", "topic": "理财", "direction": "坑", "title": "年轻人最容易踩的理财坑"}'
    )


def test_load_recent_titles_filters_by_recent_days(tmp_path) -> None:
    history_path = tmp_path / "topic_history.jsonl"

    append_history(
        date_value="2026-04-05",
        topic="理财",
        direction="坑",
        title="今天的标题",
        path=history_path,
    )
    append_history(
        date_value="2026-04-04",
        topic="AI使用",
        direction="盲区",
        title="昨天的标题",
        path=history_path,
    )
    append_history(
        date_value="2026-04-03",
        topic="AI使用",
        direction="痛点",
        title="前天的标题",
        path=history_path,
    )

    titles = load_recent_titles(days=2, path=history_path, today=date(2026, 4, 5))

    assert titles == ["今天的标题", "昨天的标题"]


def test_load_recent_titles_returns_empty_when_file_missing(tmp_path) -> None:
    history_path = tmp_path / "missing.jsonl"

    assert load_recent_titles(path=history_path) == []


def test_load_recent_titles_ignores_invalid_lines(tmp_path) -> None:
    history_path = tmp_path / "topic_history.jsonl"
    history_path.write_text(
        "\n".join(
            [
                "not-json",
                '{"date": "bad-date", "topic": "理财", "direction": "坑", "title": "bad"}',
                '{"date": "2026-04-05", "topic": "理财", "direction": "坑", "title": "valid"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    titles = load_recent_titles(path=history_path, today=date(2026, 4, 5))

    assert titles == ["valid"]


def test_has_history_for_day_returns_true_when_day_exists(tmp_path) -> None:
    history_path = tmp_path / "topic_history.jsonl"
    append_history(
        date_value="2026-04-06",
        topic="理财",
        direction="坑",
        title="valid",
        path=history_path,
    )

    assert has_history_for_day(day=date(2026, 4, 6), path=history_path) is True


def test_has_history_for_day_returns_false_when_day_missing(tmp_path) -> None:
    history_path = tmp_path / "topic_history.jsonl"
    append_history(
        date_value="2026-04-05",
        topic="理财",
        direction="坑",
        title="valid",
        path=history_path,
    )

    assert has_history_for_day(day=date(2026, 4, 6), path=history_path) is False
