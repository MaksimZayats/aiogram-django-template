from celery import Celery

from configs.core import ApplicationSettings
from configs.infrastructure import RedisSettings
from delivery.tasks.registry import TaskName, TasksRegistry
from delivery.tasks.settings import CelerySettings
from delivery.tasks.tasks.ping import PingTaskController


class CeleryAppFactory:
    def __init__(
        self,
        application_settings: ApplicationSettings,
        celery_settings: CelerySettings,
        redis_settings: RedisSettings,
    ) -> None:
        self._instance: Celery | None = None
        self._application_settings = application_settings
        self._celery_settings = celery_settings
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
            timezone=self._application_settings.time_zone,
            enable_utc=True,
            **self._celery_settings.model_dump(),
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
        celery_app_factory: CeleryAppFactory,
        ping_controller: PingTaskController,
    ) -> None:
        self._instance: TasksRegistry | None = None
        self._celery_app_factory = celery_app_factory
        self._ping_controller = ping_controller

    def __call__(self) -> TasksRegistry:
        if self._instance is not None:
            return self._instance

        celery_app = self._celery_app_factory()
        registry = TasksRegistry(app=celery_app)
        self._ping_controller.register(celery_app)

        self._instance = registry
        return self._instance
