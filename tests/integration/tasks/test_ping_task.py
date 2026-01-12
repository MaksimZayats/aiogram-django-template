from typing import cast

from punq import Container

from tasks.registry import TasksRegistry
from tasks.tasks.ping import PingResult
from tests.integration.factories import CeleryWorkerFactory


def test_ping_task(
    celery_worker_factory: CeleryWorkerFactory,
    container: Container,
) -> None:
    registry = cast(TasksRegistry, container.resolve(TasksRegistry))
    with celery_worker_factory():
        ping_result = registry.ping.delay().get(timeout=1)

    assert ping_result == PingResult(result="pong")
