# Celery Task Tests

Testing background tasks with in-process worker.

## Basic Test Structure

```python
import pytest

from delivery.tasks.registry import TasksRegistry
from tests.integration.factories import TestCeleryWorkerFactory


def test_ping_task(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
) -> None:
    with celery_worker_factory():
        result = tasks_registry.ping.delay().get(timeout=10)

    assert result == {"result": "pong"}
```

## Worker Context Manager

The `TestCeleryWorkerFactory` creates an in-process worker:

```python
with celery_worker_factory():
    # Worker is running
    result = tasks_registry.my_task.delay().get(timeout=10)
# Worker is stopped
```

## Testing with Arguments

```python
def test_cleanup_task(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
) -> None:
    with celery_worker_factory():
        result = tasks_registry.cleanup_sessions.delay(days_old=7).get(timeout=10)

    assert result["deleted_count"] >= 0
```

## Testing with Database

```python
@pytest.mark.django_db(transaction=True)
def test_task_with_database(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
    user_factory: TestUserFactory,
) -> None:
    # Setup
    user = user_factory()

    with celery_worker_factory():
        result = tasks_registry.process_user.delay(user_id=user.pk).get(timeout=10)

    assert result["processed"] is True
```

## Fixtures

### Container Fixture

```python
@pytest.fixture(scope="function")
def container() -> Container:
    return get_container()
```

### Worker Factory Fixture

```python
@pytest.fixture(scope="function")
def celery_worker_factory(container: Container) -> TestCeleryWorkerFactory:
    return container.resolve(TestCeleryWorkerFactory)
```

### Tasks Registry Fixture

```python
@pytest.fixture(scope="function")
def tasks_registry(container: Container) -> TasksRegistry:
    return container.resolve(TasksRegistry)
```

## Testing Task Failures

### Expected Failures

```python
def test_task_handles_error(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
) -> None:
    with celery_worker_factory():
        result = tasks_registry.risky_task.delay(
            invalid_input=True,
        ).get(timeout=10)

    assert result["status"] == "error"
    assert "error_message" in result
```

### Exceptions

```python
import pytest
from celery.exceptions import TimeoutError


def test_task_timeout(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
) -> None:
    with celery_worker_factory():
        with pytest.raises(TimeoutError):
            tasks_registry.slow_task.delay().get(timeout=1)
```

## Testing Async Behavior

### Fire and Forget

```python
def test_async_task(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
) -> None:
    with celery_worker_factory():
        async_result = tasks_registry.background_task.delay()

        # Task is queued
        assert async_result.id is not None

        # Wait for completion
        async_result.get(timeout=10)
        assert async_result.successful()
```

### Check Status

```python
def test_task_status(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
) -> None:
    with celery_worker_factory():
        async_result = tasks_registry.ping.delay()

        # Wait and check
        async_result.get(timeout=10)
        assert async_result.status == "SUCCESS"
        assert async_result.ready()
        assert async_result.successful()
```

## Mocking Task Dependencies

```python
from unittest.mock import MagicMock


def test_task_with_mocked_service(
    container: Container,
    celery_worker_factory: TestCeleryWorkerFactory,
) -> None:
    # Mock the service
    mock_service = MagicMock()
    mock_service.process.return_value = {"processed": True}
    container.register(ExternalService, instance=mock_service)

    tasks_registry = container.resolve(TasksRegistry)

    with celery_worker_factory():
        result = tasks_registry.process_with_service.delay().get(timeout=10)

    assert result["processed"] is True
    mock_service.process.assert_called_once()
```

## Complete Test Example

```python
import pytest
from punq import Container

from delivery.tasks.registry import TasksRegistry
from tests.integration.factories import TestCeleryWorkerFactory, TestUserFactory


class TestCleanupTask:
    @pytest.mark.django_db(transaction=True)
    def test_cleanup_old_sessions(
        self,
        celery_worker_factory: TestCeleryWorkerFactory,
        tasks_registry: TasksRegistry,
        user_factory: TestUserFactory,
    ) -> None:
        # Setup: Create user (sessions would be created in real scenario)
        user_factory()

        # Execute
        with celery_worker_factory():
            result = tasks_registry.cleanup_sessions.delay(
                days_old=0,
            ).get(timeout=10)

        # Assert
        assert "deleted_count" in result
        assert result["deleted_count"] >= 0

    def test_ping_task_returns_pong(
        self,
        celery_worker_factory: TestCeleryWorkerFactory,
        tasks_registry: TasksRegistry,
    ) -> None:
        with celery_worker_factory():
            result = tasks_registry.ping.delay().get(timeout=10)

        assert result == {"result": "pong"}

    def test_task_timeout(
        self,
        celery_worker_factory: TestCeleryWorkerFactory,
        tasks_registry: TasksRegistry,
    ) -> None:
        with celery_worker_factory():
            async_result = tasks_registry.ping.delay()

            # Should complete quickly
            result = async_result.get(timeout=5)

        assert result is not None
```

## Tips

### Use Short Timeouts

```python
# Good: Short timeout for fast tasks
result.get(timeout=10)

# Avoid: Long timeouts that slow tests
result.get(timeout=300)
```

### Test Task Idempotency

```python
def test_task_is_idempotent(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
) -> None:
    with celery_worker_factory():
        result1 = tasks_registry.idempotent_task.delay(data="test").get(timeout=10)
        result2 = tasks_registry.idempotent_task.delay(data="test").get(timeout=10)

    assert result1 == result2
```

### Clean Up After Tests

```python
@pytest.fixture(autouse=True)
def cleanup_after_test():
    yield
    # Cleanup code here
    SomeModel.objects.all().delete()
```

## Related Topics

- [Task Controllers](../celery/task-controllers.md) — Creating tasks
- [Task Registry](../celery/task-registry.md) — Task access
- [Test Factories](test-factories.md) — Factory setup
- [Mocking IoC Dependencies](mocking-ioc.md) — Dependency overrides
