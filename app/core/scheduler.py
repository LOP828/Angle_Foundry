from __future__ import annotations

from datetime import datetime, time
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.history.topic_history import has_history_for_day
from app.models import AppConfig
from app.tasks.daily_topic_task import run_daily_topic_task


def _should_run_startup_catchup(
    *,
    trigger: CronTrigger,
    history_checker=has_history_for_day,
    now: datetime | None = None,
) -> bool:
    if now is None:
        current_time = datetime.now(tz=trigger.timezone)
    elif now.tzinfo is None:
        current_time = datetime.combine(
            now.date(),
            now.time(),
            tzinfo=trigger.timezone,
        )
    else:
        current_time = now.astimezone(trigger.timezone)

    start_of_day = datetime.combine(
        current_time.date(),
        time.min,
        tzinfo=current_time.tzinfo,
    )
    scheduled_time = trigger.get_next_fire_time(None, start_of_day)

    if scheduled_time is None:
        return False
    if scheduled_time.date() != current_time.date():
        return False
    if scheduled_time > current_time:
        return False
    if history_checker(day=current_time.date()):
        return False

    return True


def start_scheduler(
    config: AppConfig,
    *,
    logger: logging.Logger | None = None,
    scheduler_factory: type[BlockingScheduler] = BlockingScheduler,
    task_runner=run_daily_topic_task,
    history_checker=has_history_for_day,
    now: datetime | None = None,
) -> BlockingScheduler | None:
    task_logger = logger or logging.getLogger("angle_foundry")
    if not config.schedule_enabled:
        task_logger.info("Scheduler is disabled in config.")
        return None

    trigger = CronTrigger.from_crontab(config.schedule_cron)
    if _should_run_startup_catchup(
        trigger=trigger,
        history_checker=history_checker,
        now=now,
    ):
        task_logger.info(
            "Missed today's scheduled run at '%s'; running startup catch-up now.",
            config.schedule_cron,
        )
        task_runner(config, logger=task_logger)

    scheduler = scheduler_factory()
    scheduler.add_job(
        lambda: task_runner(config, logger=task_logger),
        trigger=trigger,
        id="daily_topic_task",
        replace_existing=True,
    )
    task_logger.info("Scheduler started with cron '%s'.", config.schedule_cron)
    scheduler.start()
    return scheduler
