from typing import Any

from celery.signals import beat_init, worker_init

from core.configs.infrastructure import configure_infrastructure
from delivery.tasks.factories import CeleryAppFactory, TasksRegistryFactory
from ioc.container import get_container


@worker_init.connect()
def _worker_init(*_args: Any, **_kwargs: Any) -> None:
    configure_infrastructure(service_name="celery-worker")


@beat_init.connect()
def _beat_init(*_args: Any, **_kwargs: Any) -> None:
    configure_infrastructure(service_name="celery-beat")


_container = get_container()
_registry_factory = _container.resolve(TasksRegistryFactory)
_app_factory = _container.resolve(CeleryAppFactory)

# Register tasks
_registry = _registry_factory()

app = _app_factory()
