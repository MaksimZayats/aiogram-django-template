from typing import Any

from celery import Celery, Task


class TaskNotFoundError(Exception):
    pass


class BaseTasksRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, Task[..., Any]] = {}

    def _get_task_by_name(self, name: str) -> Task[..., Any]:
        try:
            return self._registry[name]
        except KeyError as e:
            msg = f"Task with name '{name}' not found in registry."
            raise TaskNotFoundError(msg) from e

    def update_from_app(self, app: Celery) -> None:
        for name, task in app.tasks.items():
            self._registry[name] = task
