from celery import Celery

from core.configs.django import application_settings
from delivery.tasks.registry import TaskName, TasksRegistry
from delivery.tasks.settings import CelerySettings
from delivery.tasks.tasks.ping import PingTaskController


class CeleryAppFactory:
    def __init__(
        self,
        settings: CelerySettings,
    ) -> None:
        self._settings = settings

    def __call__(self) -> Celery:
        celery_app = Celery(
            "main",
            broker=self._settings.redis_settings.redis_url.get_secret_value(),
            backend=self._settings.redis_settings.redis_url.get_secret_value(),
        )

        self._configure_app(celery_app=celery_app)
        self._configure_beat_schedule(celery_app=celery_app)

        return celery_app

    def _configure_app(self, celery_app: Celery) -> None:
        celery_app.conf.update(timezone=application_settings.time_zone)

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
        self._celery_app = celery_app
        self._ping_controller = ping_controller

    def __call__(self) -> TasksRegistry:
        registry = TasksRegistry(app=self._celery_app)
        self._ping_controller.register(self._celery_app)

        return registry
