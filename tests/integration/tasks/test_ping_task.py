from delivery.tasks.tasks.ping import PingResult
from tests.integration.factories import TestCeleryWorkerFactory, TestTasksRegistryFactory


def test_ping_task(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry_factory: TestTasksRegistryFactory,
) -> None:
    registry = tasks_registry_factory()
    with celery_worker_factory():
        ping_result = registry.ping.delay().get(timeout=1)

    assert ping_result == PingResult(result="pong")
