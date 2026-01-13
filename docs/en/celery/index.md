# Celery Tasks

Background task processing with Celery and the controller pattern.

## Overview

[Celery](https://docs.celeryq.dev/) is used for distributed task processing with Redis as the broker and backend.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────>│    Redis    │────>│   Worker    │
│ (API/Bot)   │     │  (Broker)   │     │  (Celery)   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Results   │
                    │   (Redis)   │
                    └─────────────┘
```

## Topics

<div class="grid cards" markdown>

-   **Task Controllers**

    ---

    Using the controller pattern for Celery tasks.

    [→ Learn More](task-controllers.md)

-   **Task Registry**

    ---

    Type-safe task access and invocation.

    [→ Learn More](task-registry.md)

-   **Beat Scheduler**

    ---

    Scheduled and periodic tasks.

    [→ Learn More](beat-scheduler.md)

</div>

## Quick Start

### Start the Worker

```bash
make celery-dev
```

### Start Beat Scheduler

```bash
make celery-beat-dev
```

### Call a Task

```python
from ioc.container import get_container
from delivery.tasks.registry import TasksRegistry

container = get_container()
registry = container.resolve(TasksRegistry)

# Async call (returns immediately)
result = registry.ping.delay()

# Wait for result
print(result.get(timeout=10))  # {"result": "pong"}
```

## Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | `SecretStr` | **Required** | Redis connection URL |

The Celery app uses Redis for both broker and results:

```python
celery_app = Celery(
    "main",
    broker=settings.redis_settings.redis_url.get_secret_value(),
    backend=settings.redis_settings.redis_url.get_secret_value(),
)
```

## Entry Point

The Celery app is defined in `delivery/tasks/app.py`:

```python
from celery import Celery

from core.configs.infrastructure import configure_infrastructure
from ioc.container import get_container

configure_infrastructure(service_name="celery-worker")

_container = get_container()
app = _container.resolve(Celery)
```

## Available Tasks

| Task Name | Description |
|-----------|-------------|
| `ping` | Health check task returning `{"result": "pong"}` |

## Docker Compose Services

```yaml
celery-worker:
  command:
    - celery
    - --app=delivery.tasks.app
    - worker
    - --loglevel=${LOGGING_LEVEL:-INFO}
    - --concurrency=4

celery-beat:
  command:
    - celery
    - --app=delivery.tasks.app
    - beat
    - --loglevel=${LOGGING_LEVEL:-INFO}
```

## Related Topics

- [Your First Celery Task](../tutorials/first-celery-task.md) — Tutorial
- [Celery Task Tests](../testing/celery-tests.md) — Testing tasks
- [Celery Documentation](https://docs.celeryq.dev/) — Official docs
