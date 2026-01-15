# Step 4: Celery Tasks

In this step, you'll create a background task to clean up old completed todos automatically.

> **See also:** [Controller Pattern concept](../concepts/controller-pattern.md)

## Files to Create/Modify

| Action | File Path |
|--------|-----------|
| Create | `src/delivery/tasks/tasks/todo_cleanup.py` |
| Modify | `src/delivery/tasks/registry.py` |
| Modify | `src/ioc/registries/delivery.py` |
| Modify | `src/delivery/tasks/factories.py` |

## 1. Add Task Name to Registry

First, add the task name to the `TaskName` enum:

```python
# src/delivery/tasks/registry.py
from enum import StrEnum
from typing import TYPE_CHECKING

from celery import Task

from infrastructure.celery.registry import BaseTasksRegistry

if TYPE_CHECKING:
    from delivery.tasks.tasks.ping import PingResult
    from delivery.tasks.tasks.todo_cleanup import TodoCleanupResult  # Add this


class TaskName(StrEnum):
    PING = "ping"
    TODO_CLEANUP = "todo.cleanup"  # Add this


class TasksRegistry(BaseTasksRegistry):
    @property
    def ping(self) -> Task[[], "PingResult"]:
        return self._get_task_by_name(TaskName.PING)

    @property
    def todo_cleanup(self) -> Task[[int], "TodoCleanupResult"]:  # Add this
        return self._get_task_by_name(TaskName.TODO_CLEANUP)
```

The typed properties provide IDE completion and type safety when calling tasks.

## 2. Create the Task Controller

Create the task controller with its result type:

```python
# src/delivery/tasks/tasks/todo_cleanup.py
from typing import Literal, TypedDict

from celery import Celery

from core.todo.services import TodoService
from delivery.tasks.registry import TaskName
from infrastructure.delivery.controllers import Controller


class TodoCleanupResult(TypedDict):
    status: Literal["success"]
    deleted_count: int


class TodoCleanupTaskController(Controller):
    def __init__(self, todo_service: TodoService) -> None:
        self._todo_service = todo_service

    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.TODO_CLEANUP)(self.cleanup)

    def cleanup(self, days: int = 30) -> TodoCleanupResult:
        """Delete completed todos older than N days."""
        deleted_count = self._todo_service.delete_completed_todos_older_than(
            days=days,
        )
        return TodoCleanupResult(
            status="success",
            deleted_count=deleted_count,
        )
```

**Key patterns:**

- **TypedDict result** - Provides type safety for task results
- **Service injection** - `TodoService` is injected via constructor
- **Controller pattern** - Same pattern as HTTP controllers
- **Named task** - Uses `TaskName` enum for consistency

## 3. Register Controller in IoC

Add the controller registration to `src/ioc/registries/delivery.py`:

```python
# src/ioc/registries/delivery.py
# Add this import at the top
from delivery.tasks.tasks.todo_cleanup import TodoCleanupTaskController

# Add this line in _register_celery_controllers()
def _register_celery_controllers(container: Container) -> None:
    container.register(PingTaskController, scope=Scope.singleton)
    container.register(TodoCleanupTaskController, scope=Scope.singleton)  # Add this
```

## 4. Update TasksRegistryFactory

Modify `src/delivery/tasks/factories.py` to inject and register the controller:

```python
# src/delivery/tasks/factories.py
# Add import at the top
from delivery.tasks.tasks.todo_cleanup import TodoCleanupTaskController

class TasksRegistryFactory:
    def __init__(
        self,
        celery_app: Celery,
        ping_controller: PingTaskController,
        todo_cleanup_controller: TodoCleanupTaskController,  # Add this
    ) -> None:
        self._instance: TasksRegistry | None = None
        self._celery_app = celery_app
        self._ping_controller = ping_controller
        self._todo_cleanup_controller = todo_cleanup_controller  # Add this

    def __call__(self) -> TasksRegistry:
        if self._instance is not None:
            return self._instance

        registry = TasksRegistry(app=self._celery_app)
        self._ping_controller.register(self._celery_app)
        self._todo_cleanup_controller.register(self._celery_app)  # Add this

        self._instance = registry
        return self._instance
```

## 5. Add Beat Schedule

Add the task to the beat schedule in `CeleryAppFactory`:

```python
# src/delivery/tasks/factories.py
from celery.schedules import crontab
from delivery.tasks.registry import TaskName

class CeleryAppFactory:
    # ... existing code ...

    def _configure_beat_schedule(self, celery_app: Celery) -> None:
        celery_app.conf.beat_schedule = {
            "ping-every-minute": {
                "task": TaskName.PING,
                "schedule": 60.0,
            },
            "todo-cleanup-daily": {  # Add this
                "task": TaskName.TODO_CLEANUP,
                "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
                "kwargs": {"days": 30},
            },
        }
```

## 6. Test the Task

### Start Celery Worker

```bash
make celery-dev
```

### Call Task Manually

In another terminal:

```bash
uv run python src/manage.py shell
```

```python
from ioc.container import get_container
from delivery.tasks.registry import TasksRegistry

container = get_container()
registry = container.resolve(TasksRegistry)

# Call the task synchronously (for testing)
result = registry.todo_cleanup.delay(days=0).get(timeout=10)
print(result)  # {'status': 'success', 'deleted_count': 0}
```

### Using the Task in Production

```python
# Async call (returns immediately, task runs in background)
registry.todo_cleanup.delay(days=30)

# Sync call with timeout
result = registry.todo_cleanup.delay(days=30).get(timeout=60)

# ETA (run at specific time)
from datetime import datetime, timedelta
registry.todo_cleanup.apply_async(
    kwargs={"days": 30},
    eta=datetime.now() + timedelta(hours=1),
)
```

## Understanding Celery Beat

Celery Beat is a scheduler that runs tasks at specified intervals:

| Schedule Type | Example | Description |
|---------------|---------|-------------|
| `float` | `60.0` | Every 60 seconds |
| `crontab(minute=0)` | Hourly | At minute 0 of every hour |
| `crontab(hour=3, minute=0)` | Daily | At 3:00 AM every day |
| `crontab(day_of_week=1)` | Weekly | Every Monday |

To run beat scheduler:

```bash
uv run celery -A delivery.tasks.app beat --loglevel=info
```

## What You've Learned

In this step, you:

1. Created a typed task controller following the same pattern as HTTP controllers
2. Registered the task in the IoC container
3. Added a beat schedule for automatic execution
4. Learned how to call tasks synchronously and asynchronously

## Next Step

In [Step 5: Observability](05-observability.md), you'll set up Logfire for tracing and monitoring.
