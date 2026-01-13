# Task Registry

Type-safe task access and invocation.

## Overview

The `TasksRegistry` provides type-safe access to Celery tasks:

```python
from ioc.container import get_container
from delivery.tasks.registry import TasksRegistry

container = get_container()
registry = container.resolve(TasksRegistry)

# Type-safe task access
result = registry.ping.delay()
```

## Registry Structure

### Task Names

Define task names as an enum:

```python
# src/delivery/tasks/registry.py

from enum import StrEnum


class TaskName(StrEnum):
    PING = "ping"
    CLEANUP_SESSIONS = "cleanup_sessions"
    SEND_EMAIL = "send_email"
```

### Base Registry

```python
# src/infrastructure/celery/registry.py

from celery import Celery, Task


class BaseTasksRegistry:
    def __init__(self, app: Celery) -> None:
        self._app = app

    def _get_task_by_name(self, name: str) -> Task:
        return self._app.tasks[name]
```

### Task Registry

```python
# src/delivery/tasks/registry.py

from typing import TYPE_CHECKING

from celery import Task

from infrastructure.celery.registry import BaseTasksRegistry

if TYPE_CHECKING:
    from delivery.tasks.tasks.ping import PingResult


class TasksRegistry(BaseTasksRegistry):
    @property
    def ping(self) -> Task[[], PingResult]:
        return self._get_task_by_name(TaskName.PING)
```

## Type Hints

Use `TYPE_CHECKING` for result types:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from delivery.tasks.tasks.cleanup import CleanupResult
    from delivery.tasks.tasks.email import EmailResult


class TasksRegistry(BaseTasksRegistry):
    @property
    def ping(self) -> Task[[], PingResult]:
        return self._get_task_by_name(TaskName.PING)

    @property
    def cleanup_sessions(self) -> Task[[int], CleanupResult]:
        """
        Args:
            days_old: Delete sessions older than this many days
        """
        return self._get_task_by_name(TaskName.CLEANUP_SESSIONS)

    @property
    def send_email(self) -> Task[[str, str, str], EmailResult]:
        """
        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
        """
        return self._get_task_by_name(TaskName.SEND_EMAIL)
```

## Calling Tasks

### Async (Non-blocking)

```python
# Returns immediately with AsyncResult
result = registry.ping.delay()

# Check status
print(result.status)  # PENDING, STARTED, SUCCESS, FAILURE

# Get result (blocks until complete)
print(result.get(timeout=10))
```

### With Arguments

```python
# Positional arguments
result = registry.send_email.delay(
    "user@example.com",
    "Welcome!",
    "Welcome to our service.",
)

# Keyword arguments
result = registry.cleanup_sessions.delay(days_old=7)
```

### Apply Async (More Options)

```python
result = registry.send_email.apply_async(
    args=["user@example.com", "Subject", "Body"],
    countdown=60,           # Delay execution by 60 seconds
    expires=3600,           # Expire if not started within 1 hour
    retry=True,             # Retry on connection errors
    retry_policy={
        "max_retries": 3,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.5,
    },
)
```

### Synchronous (Blocking)

```python
# Call directly (not recommended in web requests)
result = registry.ping()
print(result)  # {"result": "pong"}
```

!!! warning "Avoid Synchronous Calls in Web Requests"
    Calling tasks synchronously in HTTP handlers causes problems:

    - **Blocks the web worker** — The request hangs until the task completes
    - **Request timeouts** — Long-running tasks will exceed HTTP timeout limits
    - **Database deadlocks** — Tasks requiring the same database connection may deadlock
    - **Poor scalability** — Blocked workers can't serve other requests

    Use `.delay()` or `.apply_async()` instead, and return a task ID for status polling.

## IoC Registration

The registry is created by `TasksRegistryFactory`:

```python
# src/ioc/container.py

def _register_celery(container: Container) -> None:
    container.register(TasksRegistryFactory, scope=Scope.singleton)
    container.register(
        TasksRegistry,
        factory=lambda: container.resolve(TasksRegistryFactory)(),
        scope=Scope.singleton,
    )
```

## Adding New Tasks

### 1. Add Task Name

```python
class TaskName(StrEnum):
    PING = "ping"
    MY_NEW_TASK = "my_new_task"  # Add
```

### 2. Add Registry Property

```python
if TYPE_CHECKING:
    from delivery.tasks.tasks.my_task import MyTaskResult


class TasksRegistry(BaseTasksRegistry):
    @property
    def my_new_task(self) -> Task[[str, int], MyTaskResult]:
        return self._get_task_by_name(TaskName.MY_NEW_TASK)
```

### 3. Create Controller

See [Task Controllers](task-controllers.md).

## Using in HTTP Controllers

```python
class OrderController(Controller):
    def __init__(
        self,
        tasks_registry: TasksRegistry,
    ) -> None:
        self._tasks = tasks_registry

    def create_order(self, request: HttpRequest, body: OrderSchema) -> OrderResponse:
        order = Order.objects.create(**body.model_dump())

        # Send confirmation email asynchronously
        self._tasks.send_email.delay(
            to=order.user.email,
            subject="Order Confirmation",
            body=f"Your order #{order.id} has been placed.",
        )

        return OrderResponse.model_validate(order, from_attributes=True)
```

## Result Handling

### Check Status

```python
result = registry.ping.delay()

if result.ready():
    if result.successful():
        print(result.result)
    else:
        print(f"Failed: {result.result}")
else:
    print("Still processing...")
```

### Timeout

```python
try:
    result = registry.ping.delay().get(timeout=30)
except TimeoutError:
    print("Task took too long")
```

### Ignore Results

For fire-and-forget tasks:

```python
registry.send_email.apply_async(
    args=["user@example.com", "Subject", "Body"],
    ignore_result=True,
)
```

## Related Topics

- [Task Controllers](task-controllers.md) — Controller pattern
- [Beat Scheduler](beat-scheduler.md) — Scheduling
- [Celery Task Tests](../testing/celery-tests.md) — Testing
