from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.models import AppConfig
from app.tasks.daily_topic_task import run_daily_topic_task


def start_scheduler(
    config: AppConfig,
    *,
    logger: logging.Logger | None = None,
    scheduler_factory: type[BlockingScheduler] = BlockingScheduler,
    task_runner=run_daily_topic_task,
) -> BlockingScheduler | None:
    task_logger = logger or logging.getLogger("angle_foundry")
    if not config.schedule_enabled:
        task_logger.info("Scheduler is disabled in config.")
        return None

    scheduler = scheduler_factory()
    scheduler.add_job(
        lambda: task_runner(config, logger=task_logger),
        trigger=CronTrigger.from_crontab(config.schedule_cron),
        id="daily_topic_task",
        replace_existing=True,
    )
    task_logger.info("Scheduler started with cron '%s'.", config.schedule_cron)
    scheduler.start()
    return scheduler
