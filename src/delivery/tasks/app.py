from typing import Any

from celery import Celery
from celery.signals import beat_init, worker_init

from core.configs.infrastructure import configure_infrastructure
from delivery.tasks.registry import TasksRegistry
from ioc.container import get_container


@worker_init.connect()
def _worker_init(*_args: Any, **_kwargs: Any) -> None:
    configure_infrastructure(service_name="celery-worker")


@beat_init.connect()
def _beat_init(*_args: Any, **_kwargs: Any) -> None:
    configure_infrastructure(service_name="celery-beat")


_container = get_container()
_registry = _container.resolve(TasksRegistry)

app = _container.resolve(Celery)
