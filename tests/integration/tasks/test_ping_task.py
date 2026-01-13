from celery.worker import WorkController

from delivery.tasks.registry import TasksRegistry
from delivery.tasks.tasks.ping import PingResult
from tests.integration.factories import TestCeleryWorkerFactory


def test_ping_task(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
) -> None:
    with celery_worker_factory():
        ping_result = tasks_registry.ping.delay().get(timeout=1)

    assert ping_result == PingResult(result="pong")
