# Task Controllers

Using the controller pattern for Celery tasks.

## Controller Structure

Task controllers extend the base `Controller` class:

```python
# src/delivery/tasks/tasks/ping.py

from typing import Literal, TypedDict

from celery import Celery

from delivery.tasks.registry import TaskName
from infrastructure.delivery.controllers import Controller


class PingResult(TypedDict):
    result: Literal["pong"]


class PingTaskController(Controller):
    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.PING)(self.ping)

    def ping(self) -> PingResult:
        return PingResult(result="pong")
```

## Key Components

### 1. Result Type

Use `TypedDict` for type-safe results:

```python
from typing import TypedDict


class CleanupResult(TypedDict):
    deleted_count: int
    errors: list[str]
```

**Why `TypedDict` for Celery results?**

| Type | Use Case |
|------|----------|
| `TypedDict` | Celery tasks — results are serialized as JSON dicts, `TypedDict` maps directly |
| `BaseModel` | HTTP responses — provides validation, serialization, and OpenAPI schema generation |
| `dataclass` | Internal domain objects — when you need methods or instance behavior |

`TypedDict` is ideal for Celery because task results are stored and retrieved as plain dictionaries. No deserialization step is needed.

### 2. Register Method

Register the task with Celery:

```python
def register(self, registry: Celery) -> None:
    registry.task(name=TaskName.MY_TASK)(self.my_task)
```

### 3. Task Method

The actual task logic:

```python
def my_task(self, arg1: str, arg2: int = 10) -> MyResult:
    # Task logic here
    return MyResult(status="completed")
```

## Dependency Injection

Controllers can receive dependencies:

```python
from infrastructure.django.refresh_sessions.models import BaseRefreshSession


class CleanupTaskController(Controller):
    def __init__(
        self,
        refresh_session_model: type[BaseRefreshSession],
    ) -> None:
        self._refresh_session_model = refresh_session_model

    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.CLEANUP)(self.cleanup)

    def cleanup(self, days_old: int = 30) -> dict:
        deleted, _ = self._refresh_session_model.objects.filter(
            expires_at__lt=timezone.now() - timedelta(days=days_old)
        ).delete()
        return {"deleted_count": deleted}
```

## Task Options

Configure task behavior:

```python
def register(self, registry: Celery) -> None:
    registry.task(
        name=TaskName.PROCESS_DATA,
        bind=True,                    # Pass task instance as first arg
        max_retries=3,                # Retry up to 3 times
        default_retry_delay=60,       # Wait 60s between retries
        autoretry_for=(Exception,),   # Auto-retry on exceptions
        acks_late=True,               # Acknowledge after completion
        time_limit=300,               # Task timeout (5 minutes)
        soft_time_limit=270,          # Soft timeout (4.5 minutes)
    )(self.process_data)
```

### Bound Tasks

Access task instance with `bind=True`:

```python
from celery import Task


def register(self, registry: Celery) -> None:
    registry.task(name=TaskName.RETRY_TASK, bind=True)(self.retry_task)


def retry_task(self, task: Task, data: dict) -> dict:
    try:
        result = process(data)
        return {"status": "success", "result": result}
    except TransientError as e:
        # Retry with exponential backoff
        raise task.retry(exc=e, countdown=2 ** task.request.retries)
```

## IoC Registration

Register controllers in the container:

```python
# src/ioc/container.py

def _register_celery(container: Container) -> None:
    # ... existing registrations ...

    container.register(PingTaskController, scope=Scope.singleton)
    container.register(CleanupTaskController, scope=Scope.singleton)
```

## Factory Registration

Register controllers in the factory:

```python
# src/delivery/tasks/factories.py

class TasksRegistryFactory:
    def __init__(
        self,
        celery_app: Celery,
        ping_controller: PingTaskController,
        cleanup_controller: CleanupTaskController,
    ) -> None:
        self._celery_app = celery_app
        self._ping_controller = ping_controller
        self._cleanup_controller = cleanup_controller

    def __call__(self) -> TasksRegistry:
        registry = TasksRegistry(app=self._celery_app)

        self._ping_controller.register(self._celery_app)
        self._cleanup_controller.register(self._celery_app)

        return registry
```

## Complete Example

```python
# src/delivery/tasks/tasks/email.py

from typing import TypedDict

from celery import Celery, Task
from django.core.mail import send_mail

from delivery.tasks.registry import TaskName
from infrastructure.delivery.controllers import Controller


class EmailResult(TypedDict):
    sent: bool
    message_id: str | None


class EmailTaskController(Controller):
    def register(self, registry: Celery) -> None:
        registry.task(
            name=TaskName.SEND_EMAIL,
            bind=True,
            max_retries=3,
            autoretry_for=(Exception,),
            default_retry_delay=300,
        )(self.send_email)

    def send_email(
        self,
        task: Task,
        to: str,
        subject: str,
        body: str,
    ) -> EmailResult:
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=None,  # Use default
                recipient_list=[to],
            )
            return EmailResult(sent=True, message_id=task.request.id)
        except Exception as e:
            if task.request.retries < task.max_retries:
                raise task.retry(exc=e)
            return EmailResult(sent=False, message_id=None)
```

## Exception Handling

Override `handle_exception` for task-specific error handling. Note that `handle_exception` must always raise an exception (return type is `NoReturn`):

```python
class EmailTaskController(Controller):
    def handle_exception(self, exception: Exception) -> NoReturn:
        if isinstance(exception, SMTPError):
            logger.error("SMTP error: %s", exception)
            raise TaskFailure(f"Email delivery failed: {exception}") from exception

        raise exception
```

If you need to swallow exceptions without failing the task, handle them in the task method itself:

```python
def send_email(self, task: Task, to: str, subject: str, body: str) -> EmailResult:
    try:
        send_mail(subject=subject, message=body, from_email=None, recipient_list=[to])
        return EmailResult(sent=True, message_id=task.request.id)
    except SMTPError as e:
        logger.error("SMTP error: %s", e)
        return EmailResult(sent=False, message_id=None)
```

!!! warning "Task Exceptions"
    Unlike HTTP controllers, task exceptions might be retried. Handle carefully.

## Related Topics

- [Task Registry](task-registry.md) — Type-safe task access
- [Beat Scheduler](beat-scheduler.md) — Scheduling tasks
- [Controller Pattern](../concepts/controller-pattern.md) — Base pattern
- [Your First Celery Task](../tutorials/first-celery-task.md) — Tutorial
