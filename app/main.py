from __future__ import annotations

import argparse
import logging

from app.core.config import load_config
from app.core.logger import setup_logger
from app.core.scheduler import start_scheduler
from app.core.single_instance import SchedulerInstanceLock
from app.core.single_instance import SingleInstanceError
from app.tasks.daily_topic_task import run_daily_topic_task


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Angle Foundry")
    parser.add_argument(
        "--config",
        default="config/config.toml",
        help="Path to config.toml",
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run the daily topic flow once.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logger = setup_logger(level=logging.INFO)
    config = load_config(args.config)

    if args.run_once:
        summary = run_daily_topic_task(config, logger=logger)
        logger.info("Run-once summary: %s", summary)
        return 0 if int(summary["failure_count"]) == 0 else 1

    try:
        with SchedulerInstanceLock():
            start_scheduler(config, logger=logger)
    except SingleInstanceError as exc:
        logger.error("%s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
