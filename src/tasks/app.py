from celery import Celery
from punq import Container

from ioc.container import get_container
from tasks.registry import TasksRegistry
from tasks.settings import CelerySettings
from tasks.tasks.ping import PingTaskController


def get_celery_app(container: Container | None = None) -> Celery:
    container = container or get_container()

    celery_settings = container.resolve(CelerySettings)
    celery_app = Celery(
        "main",
        broker=celery_settings.redis_settings.redis_url.get_secret_value(),
        backend=celery_settings.redis_settings.redis_url.get_secret_value(),
    )

    _register_celery_tasks(container=container, celery_app=celery_app)

    return celery_app


def _register_celery_tasks(
    container: Container,
    celery_app: Celery,
) -> None:
    registry = container.resolve(TasksRegistry)

    ping_controller = container.resolve(PingTaskController)
    ping_controller.register(celery_app)

    registry.update_from_app(celery_app)


app = get_celery_app()
