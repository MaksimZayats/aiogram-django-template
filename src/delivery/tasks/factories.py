from celery import Celery

from core.configs.core import RedisSettings
from core.configs.django import application_settings
from delivery.tasks.registry import TaskName, TasksRegistry
from delivery.tasks.settings import CelerySettings
from delivery.tasks.tasks.ping import PingTaskController


class CeleryAppFactory:
    def __init__(
        self,
        settings: CelerySettings,
        redis_settings: RedisSettings,
    ) -> None:
        self._instance: Celery | None = None
        self._settings = settings
        self._redis_settings = redis_settings

    def __call__(self) -> Celery:
        if self._instance is not None:
            return self._instance

        celery_app = Celery(
            "main",
            broker=self._redis_settings.redis_url.get_secret_value(),
            backend=self._redis_settings.redis_url.get_secret_value(),
        )

        self._configure_app(celery_app=celery_app)
        self._configure_beat_schedule(celery_app=celery_app)

        self._instance = celery_app
        return self._instance

    def _configure_app(self, celery_app: Celery) -> None:
        celery_app.conf.update(
            timezone=application_settings.time_zone,
            enable_utc=True,
            **self._settings.model_dump(),
        )

    def _configure_beat_schedule(self, celery_app: Celery) -> None:
        celery_app.conf.beat_schedule = {
            "ping-every-minute": {
                "task": TaskName.PING,
                "schedule": 60.0,
            },
        }


class TasksRegistryFactory:
    def __init__(
        self,
        celery_app: Celery,
        ping_controller: PingTaskController,
    ) -> None:
        self._instance: TasksRegistry | None = None
        self._celery_app = celery_app
        self._ping_controller = ping_controller

    def __call__(self) -> TasksRegistry:
        if self._instance is not None:
            return self._instance

        registry = TasksRegistry(app=self._celery_app)
        self._ping_controller.register(self._celery_app)

        self._instance = registry
        return self._instance
