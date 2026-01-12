from enum import StrEnum
from typing import TYPE_CHECKING

from celery import Task

from infrastructure.celery.registry import BaseTasksRegistry

if TYPE_CHECKING:
    from tasks.tasks.ping import PingResult


class TaskName(StrEnum):
    PING = "ping"


class TasksRegistry(BaseTasksRegistry):
    @property
    def ping(self) -> Task[[], PingResult]:
        return self._get_task_by_name(TaskName.PING)
