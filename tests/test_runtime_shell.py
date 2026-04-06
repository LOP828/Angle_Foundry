from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path

from apscheduler.triggers.cron import CronTrigger

from app.core.logger import setup_logger
from app.core.scheduler import _should_run_startup_catchup
from app.core.scheduler import start_scheduler
from app.core.single_instance import SingleInstanceError
from app.main import main
from app.models import AppConfig


def make_config() -> AppConfig:
    return AppConfig(
        schedule_enabled=True,
        schedule_cron="30 8 * * *",
        topics=["理财"],
        directions=["坑", "盲区", "痛点", "疑问", "跨界话题"],
        count_per_direction=2,
        push_provider="feishu",
        push_webhook="https://example.com/webhook",
        ai_model="test-model",
        ai_base_url="https://example.com/v1",
        ai_timeout_seconds=30,
        ai_max_retries=1,
        ai_api_key="secret",
    )


def test_setup_logger_writes_console_and_file(tmp_path: Path) -> None:
    log_file = tmp_path / "angle_foundry.log"
    logger = setup_logger(
        logger_name="angle_foundry_test_logger",
        level=logging.INFO,
        log_file=log_file,
    )

    logger.info("logger smoke message")

    assert log_file.exists()
    assert "logger smoke message" in log_file.read_text(encoding="utf-8")


def test_start_scheduler_registers_cron_job_without_running_blocking_loop() -> None:
    config = make_config()
    events: dict[str, object] = {}

    class FakeScheduler:
        def add_job(self, func, trigger, id, replace_existing):
            events["id"] = id
            events["replace_existing"] = replace_existing
            events["trigger"] = str(trigger)

        def start(self):
            events["started"] = True

    scheduler = start_scheduler(
        config,
        logger=logging.getLogger("scheduler_test"),
        scheduler_factory=FakeScheduler,
        task_runner=lambda cfg, logger=None: None,
    )

    assert isinstance(scheduler, FakeScheduler)
    assert events["id"] == "daily_topic_task"
    assert events["replace_existing"] is True
    assert events["started"] is True


def test_main_run_once_returns_zero_on_success(monkeypatch) -> None:
    config = make_config()

    monkeypatch.setattr("app.main.load_config", lambda path: config)
    monkeypatch.setattr("app.main.setup_logger", lambda level: logging.getLogger("main"))
    monkeypatch.setattr(
        "app.main.run_daily_topic_task",
        lambda cfg, logger=None: {
            "total_topics": 1,
            "success_count": 1,
            "failure_count": 0,
            "succeeded_topics": ["理财"],
            "failed_topics": [],
        },
    )

    assert main(["--run-once"]) == 0


def test_main_run_once_returns_one_on_failure(monkeypatch) -> None:
    config = make_config()

    monkeypatch.setattr("app.main.load_config", lambda path: config)
    monkeypatch.setattr("app.main.setup_logger", lambda level: logging.getLogger("main"))
    monkeypatch.setattr(
        "app.main.run_daily_topic_task",
        lambda cfg, logger=None: {
            "total_topics": 1,
            "success_count": 0,
            "failure_count": 1,
            "succeeded_topics": [],
            "failed_topics": [{"topic": "理财", "error": "mock failure"}],
        },
    )

    assert main(["--run-once"]) == 1


def test_main_default_mode_starts_scheduler(monkeypatch) -> None:
    config = make_config()
    calls: list[str] = []

    monkeypatch.setattr("app.main.load_config", lambda path: config)
    monkeypatch.setattr("app.main.setup_logger", lambda level: logging.getLogger("main"))
    monkeypatch.setattr("app.main.SchedulerInstanceLock", DummyLock)
    monkeypatch.setattr(
        "app.main.start_scheduler",
        lambda cfg, logger=None: calls.append("started"),
    )

    assert main([]) == 0
    assert calls == ["started"]


class DummyLock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


def test_start_scheduler_returns_none_when_disabled() -> None:
    config = make_config().model_copy(update={"schedule_enabled": False})

    scheduler = start_scheduler(
        config,
        logger=logging.getLogger("scheduler_disabled_test"),
    )

    assert scheduler is None


def test_main_default_mode_returns_one_when_scheduler_lock_is_taken(monkeypatch) -> None:
    config = make_config()

    class FailingLock:
        def __enter__(self):
            raise SingleInstanceError("lock taken")

        def __exit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("app.main.load_config", lambda path: config)
    monkeypatch.setattr("app.main.setup_logger", lambda level: logging.getLogger("main"))
    monkeypatch.setattr("app.main.SchedulerInstanceLock", FailingLock)

    assert main([]) == 1


def test_start_scheduler_runs_startup_catchup_after_missed_time() -> None:
    config = make_config().model_copy(update={"schedule_cron": "0 10 * * *"})
    events: dict[str, object] = {"run_count": 0}

    class FakeScheduler:
        def add_job(self, func, trigger, id, replace_existing):
            events["id"] = id
            events["trigger"] = str(trigger)

        def start(self):
            events["started"] = True

    scheduler = start_scheduler(
        config,
        logger=logging.getLogger("scheduler_catchup_test"),
        scheduler_factory=FakeScheduler,
        task_runner=lambda cfg, logger=None: events.__setitem__(
            "run_count", int(events["run_count"]) + 1
        ),
        history_checker=lambda day=None: False,
        now=datetime(2026, 4, 6, 10, 2),
    )

    assert isinstance(scheduler, FakeScheduler)
    assert events["run_count"] == 1
    assert events["started"] is True


def test_start_scheduler_skips_startup_catchup_when_today_already_sent() -> None:
    config = make_config().model_copy(update={"schedule_cron": "0 10 * * *"})
    events: dict[str, object] = {"run_count": 0}

    class FakeScheduler:
        def add_job(self, func, trigger, id, replace_existing):
            events["id"] = id

        def start(self):
            events["started"] = True

    scheduler = start_scheduler(
        config,
        logger=logging.getLogger("scheduler_no_catchup_test"),
        scheduler_factory=FakeScheduler,
        task_runner=lambda cfg, logger=None: events.__setitem__(
            "run_count", int(events["run_count"]) + 1
        ),
        history_checker=lambda day=None: True,
        now=datetime(2026, 4, 6, 10, 2),
    )

    assert isinstance(scheduler, FakeScheduler)
    assert events["run_count"] == 0
    assert events["started"] is True


def test_should_run_startup_catchup_returns_false_before_scheduled_time() -> None:
    trigger = CronTrigger.from_crontab("0 10 * * *")

    should_run = _should_run_startup_catchup(
        trigger=trigger,
        history_checker=lambda day=None: False,
        now=datetime(2026, 4, 6, 9, 59, tzinfo=trigger.timezone),
    )

    assert should_run is False
