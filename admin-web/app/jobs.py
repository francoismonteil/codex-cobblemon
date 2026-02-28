from __future__ import annotations

import queue
import threading
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

OutputTuple = tuple[str, str]
JobCallable = Callable[[], OutputTuple]


@dataclass
class JobRecord:
    id: str
    action: str
    status: str = "queued"
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    exit_code: Optional[int] = None
    stdout_tail: str = ""
    stderr_tail: str = ""

    def to_dict(self) -> dict[str, str | int | None]:
        return {
            "id": self.id,
            "action": self.action,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "exit_code": self.exit_code,
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
        }


@dataclass
class _QueuedJob:
    record: JobRecord
    fn: JobCallable = field(repr=False)


class JobQueue:
    def __init__(self, history_limit: int = 100) -> None:
        self._history_limit = history_limit
        self._queue: "queue.Queue[Optional[_QueuedJob]]" = queue.Queue()
        self._records: OrderedDict[str, JobRecord] = OrderedDict()
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._worker_loop, name="mc-admin-worker", daemon=True)
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._thread.start()
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        self._queue.put(None)
        self._thread.join(timeout=5)
        self._started = False

    def enqueue(self, action: str, fn: JobCallable) -> JobRecord:
        record = JobRecord(id=str(uuid.uuid4()), action=action)
        with self._lock:
            self._records[record.id] = record
            self._records.move_to_end(record.id)
            while len(self._records) > self._history_limit:
                self._records.popitem(last=False)
        self._queue.put(_QueuedJob(record=record, fn=fn))
        return record

    def list(self) -> list[JobRecord]:
        with self._lock:
            return list(reversed([self._copy(record) for record in self._records.values()]))

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            record = self._records.get(job_id)
            return self._copy(record) if record else None

    def _worker_loop(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                self._queue.task_done()
                return

            self._mark_running(item.record.id)
            try:
                stdout, stderr = item.fn()
            except Exception as exc:  # noqa: BLE001
                self._mark_finished(item.record.id, succeeded=False, exit_code=1, stdout="", stderr=str(exc))
            else:
                self._mark_finished(item.record.id, succeeded=True, exit_code=0, stdout=stdout, stderr=stderr)
            finally:
                self._queue.task_done()

    def _mark_running(self, job_id: str) -> None:
        with self._lock:
            record = self._records[job_id]
            record.status = "running"
            record.started_at = self._utcnow()

    def _mark_finished(self, job_id: str, *, succeeded: bool, exit_code: int, stdout: str, stderr: str) -> None:
        with self._lock:
            record = self._records[job_id]
            record.status = "succeeded" if succeeded else "failed"
            record.exit_code = exit_code
            record.stdout_tail = stdout[-8192:]
            record.stderr_tail = stderr[-8192:]
            record.finished_at = self._utcnow()

    @staticmethod
    def _utcnow() -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    @staticmethod
    def _copy(record: JobRecord) -> JobRecord:
        return JobRecord(
            id=record.id,
            action=record.action,
            status=record.status,
            started_at=record.started_at,
            finished_at=record.finished_at,
            exit_code=record.exit_code,
            stdout_tail=record.stdout_tail,
            stderr_tail=record.stderr_tail,
        )
