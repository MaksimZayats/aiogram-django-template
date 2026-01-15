# Add Celery Task

Quick reference for adding a new background task.

## Checklist

- [ ] Add task name to `TaskName` enum
- [ ] Create task controller
- [ ] Add typed property to `TasksRegistry`
- [ ] Register controller in IoC
- [ ] Update `TasksRegistryFactory`
- [ ] (Optional) Add beat schedule

## Step-by-Step

### 1. Add Task Name

```python
# src/delivery/tasks/registry.py
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from delivery.tasks.tasks.email_digest import EmailDigestResult


class TaskName(StrEnum):
    PING = "ping"
    EMAIL_DIGEST = "email.digest"  # Add this
```

### 2. Create Task Controller

```python
# src/delivery/tasks/tasks/email_digest.py
from typing import Literal, TypedDict

from celery import Celery

from core.email.services import EmailService
from delivery.tasks.registry import TaskName
from infrastructure.delivery.controllers import Controller


class EmailDigestResult(TypedDict):
    status: Literal["success"]
    emails_sent: int


class EmailDigestTaskController(Controller):
    def __init__(self, email_service: EmailService) -> None:
        self._email_service = email_service

    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.EMAIL_DIGEST)(self.send_digest)

    def send_digest(self) -> EmailDigestResult:
        count = self._email_service.send_daily_digest()
        return EmailDigestResult(status="success", emails_sent=count)
```

### 3. Add Typed Property

```python
# src/delivery/tasks/registry.py
from celery import Task

if TYPE_CHECKING:
    from delivery.tasks.tasks.email_digest import EmailDigestResult


class TasksRegistry(BaseTasksRegistry):
    @property
    def ping(self) -> Task[[], "PingResult"]:
        return self._get_task_by_name(TaskName.PING)

    @property
    def email_digest(self) -> Task[[], "EmailDigestResult"]:  # Add this
        return self._get_task_by_name(TaskName.EMAIL_DIGEST)
```

### 4. Register Controller

```python
# src/ioc/registries/delivery.py
from delivery.tasks.tasks.email_digest import EmailDigestTaskController


def _register_celery_controllers(container: Container) -> None:
    container.register(PingTaskController, scope=Scope.singleton)
    container.register(EmailDigestTaskController, scope=Scope.singleton)  # Add this
```

### 5. Update Factory

```python
# src/delivery/tasks/factories.py
from delivery.tasks.tasks.email_digest import EmailDigestTaskController


class TasksRegistryFactory:
    def __init__(
        self,
        celery_app: Celery,
        ping_controller: PingTaskController,
        email_digest_controller: EmailDigestTaskController,  # Add this
    ) -> None:
        self._celery_app = celery_app
        self._ping_controller = ping_controller
        self._email_digest_controller = email_digest_controller  # Add this

    def __call__(self) -> TasksRegistry:
        if self._instance is not None:
            return self._instance

        registry = TasksRegistry(app=self._celery_app)
        self._ping_controller.register(self._celery_app)
        self._email_digest_controller.register(self._celery_app)  # Add this

        self._instance = registry
        return self._instance
```

### 6. (Optional) Add Beat Schedule

```python
# src/delivery/tasks/factories.py
from celery.schedules import crontab


class CeleryAppFactory:
    def _configure_beat_schedule(self, celery_app: Celery) -> None:
        celery_app.conf.beat_schedule = {
            "ping-every-minute": {
                "task": TaskName.PING,
                "schedule": 60.0,
            },
            "email-digest-daily": {  # Add this
                "task": TaskName.EMAIL_DIGEST,
                "schedule": crontab(hour=8, minute=0),  # Daily at 8 AM
            },
        }
```

## Calling Tasks

### Async (Fire and Forget)

```python
registry.email_digest.delay()
```

### Sync (Wait for Result)

```python
result = registry.email_digest.delay().get(timeout=60)
print(result["emails_sent"])
```

### With Arguments

```python
# Task with parameters
def send_digest(self, user_id: int, include_archived: bool = False) -> EmailDigestResult:
    # ...

# Call with args
registry.email_digest.delay(user_id=123, include_archived=True)
```

### Scheduled Execution

```python
from datetime import datetime, timedelta

# Run in 1 hour
registry.email_digest.apply_async(
    eta=datetime.now() + timedelta(hours=1),
)

# Run at specific time
registry.email_digest.apply_async(
    eta=datetime(2024, 1, 15, 8, 0, 0),
)
```

## Beat Schedule Examples

```python
from celery.schedules import crontab

beat_schedule = {
    # Every 30 seconds
    "task-every-30s": {
        "task": TaskName.EXAMPLE,
        "schedule": 30.0,
    },

    # Every hour
    "task-hourly": {
        "task": TaskName.EXAMPLE,
        "schedule": crontab(minute=0),
    },

    # Daily at 3 AM
    "task-daily": {
        "task": TaskName.EXAMPLE,
        "schedule": crontab(hour=3, minute=0),
    },

    # Every Monday at 9 AM
    "task-weekly": {
        "task": TaskName.EXAMPLE,
        "schedule": crontab(hour=9, minute=0, day_of_week=1),
    },

    # First day of month
    "task-monthly": {
        "task": TaskName.EXAMPLE,
        "schedule": crontab(hour=0, minute=0, day_of_month=1),
    },

    # With arguments
    "task-with-args": {
        "task": TaskName.EXAMPLE,
        "schedule": crontab(hour=8, minute=0),
        "kwargs": {"days": 30, "include_draft": False},
    },
}
```

## Testing

```python
# tests/integration/tasks/test_email_digest.py
import pytest

from delivery.tasks.registry import TasksRegistry
from tests.integration.factories import TestCeleryWorkerFactory


@pytest.mark.django_db(transaction=True)
def test_email_digest_task(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
) -> None:
    with celery_worker_factory():
        result = tasks_registry.email_digest.delay().get(timeout=10)

    assert result["status"] == "success"
    assert result["emails_sent"] >= 0
```

## Related

- [Tutorial: Celery Tasks](../tutorial/04-celery-tasks.md) - Detailed walkthrough
- [Controller Pattern](../concepts/controller-pattern.md) - Controller architecture
