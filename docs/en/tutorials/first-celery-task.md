# Your First Celery Task

Create a background task using the controller pattern and add it to the beat schedule.

## Goal

Build a `cleanup_old_sessions` task that:

- Runs as a background task
- Can be scheduled with Celery Beat
- Uses the controller pattern for consistency

## Step 1: Create the Task Controller

Create `src/delivery/tasks/tasks/cleanup.py`:

```python
from datetime import timedelta
from typing import TypedDict

from celery import Celery
from django.utils import timezone

from delivery.tasks.registry import TaskName
from infrastructure.delivery.controllers import Controller
from infrastructure.django.refresh_sessions.models import BaseRefreshSession


class CleanupResult(TypedDict):
    deleted_count: int


class CleanupTaskController(Controller):
    def __init__(
        self,
        refresh_session_model: type[BaseRefreshSession],
    ) -> None:
        self._refresh_session_model = refresh_session_model

    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.CLEANUP_SESSIONS)(self.cleanup_old_sessions)

    def cleanup_old_sessions(self, days_old: int = 30) -> CleanupResult:
        """Delete refresh sessions older than specified days."""
        cutoff_date = timezone.now() - timedelta(days=days_old)

        deleted_count, _ = self._refresh_session_model.objects.filter(
            expires_at__lt=cutoff_date,
        ).delete()

        return CleanupResult(deleted_count=deleted_count)
```

## Step 2: Add Task Name to Registry

Edit `src/delivery/tasks/registry.py`:

```python
from enum import StrEnum
from typing import TYPE_CHECKING

from celery import Task

from infrastructure.celery.registry import BaseTasksRegistry

if TYPE_CHECKING:
    from delivery.tasks.tasks.cleanup import CleanupResult
    from delivery.tasks.tasks.ping import PingResult


class TaskName(StrEnum):
    PING = "ping"
    CLEANUP_SESSIONS = "cleanup_sessions"  # Add this


class TasksRegistry(BaseTasksRegistry):
    @property
    def ping(self) -> Task[[], PingResult]:
        return self._get_task_by_name(TaskName.PING)

    @property
    def cleanup_sessions(self) -> Task[[int], CleanupResult]:  # Add this
        return self._get_task_by_name(TaskName.CLEANUP_SESSIONS)
```

## Step 3: Register in IoC Container

Edit `src/ioc/container.py`:

```python
from delivery.tasks.tasks.cleanup import CleanupTaskController  # Add import


def _register_celery(container: Container) -> None:
    container.register(CelerySettings, factory=lambda: CelerySettings(), scope=Scope.singleton)

    container.register(CeleryAppFactory, scope=Scope.singleton)
    container.register(
        Celery,
        factory=lambda: container.resolve(CeleryAppFactory)(),
        scope=Scope.singleton,
    )

    container.register(TasksRegistryFactory, scope=Scope.singleton)
    container.register(
        TasksRegistry,
        factory=lambda: container.resolve(TasksRegistryFactory)(),
        scope=Scope.singleton,
    )

    container.register(PingTaskController, scope=Scope.singleton)
    container.register(CleanupTaskController, scope=Scope.singleton)  # Add this
```

## Step 4: Register in Tasks Registry Factory

Edit `src/delivery/tasks/factories.py`:

```python
from delivery.tasks.tasks.cleanup import CleanupTaskController  # Add import


class TasksRegistryFactory:
    def __init__(
        self,
        celery_app: Celery,
        ping_controller: PingTaskController,
        cleanup_controller: CleanupTaskController,  # Add parameter
    ) -> None:
        self._instance: TasksRegistry | None = None
        self._celery_app = celery_app
        self._ping_controller = ping_controller
        self._cleanup_controller = cleanup_controller  # Store it

    def __call__(self) -> TasksRegistry:
        if self._instance is not None:
            return self._instance

        registry = TasksRegistry(app=self._celery_app)
        self._ping_controller.register(self._celery_app)
        self._cleanup_controller.register(self._celery_app)  # Register it

        self._instance = registry
        return self._instance
```

## Step 5: Add to Beat Schedule

Edit `src/delivery/tasks/factories.py` in the `CeleryAppFactory` class:

```python
class CeleryAppFactory:
    # ... existing code ...

    def _configure_beat_schedule(self, celery_app: Celery) -> None:
        celery_app.conf.beat_schedule = {
            "ping-every-minute": {
                "task": TaskName.PING,
                "schedule": 60.0,
            },
            # Add this
            "cleanup-sessions-daily": {
                "task": TaskName.CLEANUP_SESSIONS,
                "schedule": 86400.0,  # 24 hours
                "args": [30],  # Delete sessions older than 30 days
            },
        }
```

## Step 6: Test It

### Start the Celery Worker

```bash
make celery-dev
```

### Call the Task Manually

Using Django shell:

```bash
uv run manage.py shell
```

```python
from ioc.container import get_container
from delivery.tasks.registry import TasksRegistry

container = get_container()
registry = container.resolve(TasksRegistry)

# Call synchronously
result = registry.cleanup_sessions.delay(days_old=7).get(timeout=10)
print(f"Deleted {result['deleted_count']} sessions")

# Or call asynchronously (fire and forget)
registry.cleanup_sessions.delay(days_old=30)
```

### Start Beat Scheduler

To run scheduled tasks:

```bash
make celery-beat-dev
```

## Writing Tests

Create `tests/integration/tasks/test_cleanup.py`:

```python
import pytest
from django.utils import timezone
from datetime import timedelta

from delivery.tasks.registry import TasksRegistry
from tests.integration.factories import TestCeleryWorkerFactory


@pytest.mark.django_db(transaction=True)
def test_cleanup_old_sessions(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
    user_factory,
) -> None:
    # Create a user with old session
    user = user_factory()

    # Create an expired session (you'd need to set this up)
    # ...

    with celery_worker_factory():
        result = tasks_registry.cleanup_sessions.delay(days_old=0).get(timeout=10)

    assert result["deleted_count"] >= 0
```

## Task Options

Celery tasks support various options:

```python
def register(self, registry: Celery) -> None:
    registry.task(
        name=TaskName.CLEANUP_SESSIONS,
        bind=True,  # Pass task instance as first argument
        max_retries=3,  # Retry up to 3 times
        default_retry_delay=60,  # Wait 60 seconds between retries
        autoretry_for=(Exception,),  # Auto-retry on exceptions
        acks_late=True,  # Acknowledge after task completes
    )(self.cleanup_old_sessions)
```

## Next Steps

- [Task Controllers](../celery/task-controllers.md) — Deep dive into the pattern
- [Task Registry](../celery/task-registry.md) — Type-safe task access
- [Beat Scheduler](../celery/beat-scheduler.md) — Scheduling options
- [Celery Task Tests](../testing/celery-tests.md) — Testing best practices
