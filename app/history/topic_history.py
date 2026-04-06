from __future__ import annotations

from datetime import date, timedelta
import json
from pathlib import Path

DEFAULT_HISTORY_PATH = Path("logs/topic_history.jsonl")


def append_history(
    *,
    date_value: date | str,
    topic: str,
    direction: str,
    title: str,
    path: str | Path = DEFAULT_HISTORY_PATH,
) -> None:
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "date": _normalize_date(date_value),
        "topic": topic,
        "direction": direction,
        "title": title,
    }
    with history_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_recent_titles(
    days: int = 1,
    *,
    path: str | Path = DEFAULT_HISTORY_PATH,
    today: date | None = None,
) -> list[str]:
    if days < 1:
        raise ValueError("days must be greater than or equal to 1")

    history_path = Path(path)
    if not history_path.exists():
        return []

    current_day = today or date.today()
    start_day = current_day - timedelta(days=days - 1)
    titles: list[str] = []

    with history_path.open("r", encoding="utf-8") as file:
        for line in file:
            record = _parse_history_line(line)
            if record is None:
                continue

            record_date = _parse_record_date(record.get("date"))
            if record_date is None or record_date < start_day or record_date > current_day:
                continue

            title = record.get("title")
            if isinstance(title, str):
                titles.append(title)

    return titles


def has_history_for_day(
    *,
    day: date | None = None,
    path: str | Path = DEFAULT_HISTORY_PATH,
) -> bool:
    history_path = Path(path)
    if not history_path.exists():
        return False

    target_day = day or date.today()

    with history_path.open("r", encoding="utf-8") as file:
        for line in file:
            record = _parse_history_line(line)
            if record is None:
                continue

            record_date = _parse_record_date(record.get("date"))
            if record_date == target_day:
                return True

    return False


def _normalize_date(value: date | str) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return date.fromisoformat(value).isoformat()


def _parse_history_line(line: str) -> dict[str, object] | None:
    raw_line = line.strip()
    if not raw_line:
        return None

    try:
        parsed = json.loads(raw_line)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None
    return parsed


def _parse_record_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
