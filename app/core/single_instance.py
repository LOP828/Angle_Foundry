from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
from typing import TextIO


class SingleInstanceError(RuntimeError):
    """Raised when another scheduler instance is already running."""


class SchedulerInstanceLock(AbstractContextManager["SchedulerInstanceLock"]):
    def __init__(self, path: str | Path = "logs/angle_foundry.scheduler.lock") -> None:
        self.path = Path(path)
        self._file: TextIO | None = None

    def __enter__(self) -> "SchedulerInstanceLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        file = self.path.open("a+", encoding="utf-8")
        try:
            self._acquire(file)
            file.seek(0)
            file.truncate()
            file.write("locked\n")
            file.flush()
        except Exception:
            file.close()
            raise

        self._file = file
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._file is None:
            return None

        try:
            self._release(self._file)
        finally:
            self._file.close()
            self._file = None
        return None

    @staticmethod
    def _acquire(file: TextIO) -> None:
        try:
            import msvcrt
        except ImportError:
            import fcntl

            try:
                fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise SingleInstanceError(
                    "Another Angle Foundry scheduler instance is already running."
                ) from exc
            return

        file.seek(0)
        try:
            msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise SingleInstanceError(
                "Another Angle Foundry scheduler instance is already running."
            ) from exc

    @staticmethod
    def _release(file: TextIO) -> None:
        try:
            import msvcrt
        except ImportError:
            import fcntl

            fcntl.flock(file.fileno(), fcntl.LOCK_UN)
            return

        file.seek(0)
        msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
