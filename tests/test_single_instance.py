from __future__ import annotations

from pathlib import Path

import pytest

from app.core.single_instance import SchedulerInstanceLock
from app.core.single_instance import SingleInstanceError


def test_scheduler_instance_lock_rejects_second_holder(tmp_path: Path) -> None:
    lock_path = tmp_path / "scheduler.lock"

    with SchedulerInstanceLock(lock_path):
        with pytest.raises(SingleInstanceError):
            with SchedulerInstanceLock(lock_path):
                pass


def test_scheduler_instance_lock_can_be_reacquired_after_release(tmp_path: Path) -> None:
    lock_path = tmp_path / "scheduler.lock"

    with SchedulerInstanceLock(lock_path):
        pass

    with SchedulerInstanceLock(lock_path):
        assert lock_path.exists()
