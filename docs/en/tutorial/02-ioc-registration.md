# Step 2: IoC Registration

In this step, you'll register the TodoService in the IoC container so it can be automatically injected into controllers.

> **See also:** [IoC Container concept](../concepts/ioc-container.md)

## Files to Modify

| Action | File Path |
|--------|-----------|
| Modify | `src/ioc/registries/core.py` |

## Understanding the Container

The IoC (Inversion of Control) container is configured in `src/ioc/`. It uses **punq**, a simple dependency injection library for Python.

The container configuration is split into registries:

```
ioc/
├── container.py              # get_container() function
└── registries/
    ├── core.py               # Services, settings, models
    ├── infrastructure.py     # JWT, auth, base classes
    └── delivery.py           # Controllers, factories
```

**Registration order matters:**

1. `core.py` - Services must be registered first
2. `infrastructure.py` - Infrastructure depends on services
3. `delivery.py` - Controllers depend on both

## Register TodoService

Open `src/ioc/registries/core.py` and add the TodoService registration:

```python
# src/ioc/registries/core.py
from punq import Container, Scope

from core.configs.core import ApplicationSettings, RedisSettings
from core.health.services import HealthService
from core.todo.services import TodoService  # Add this import
from core.user.models import RefreshSession
from core.user.services import UserService
from infrastructure.django.refresh_sessions.models import BaseRefreshSession


def register_core(container: Container) -> None:
    _register_settings(container)
    _register_models(container)
    _register_services(container)


def _register_settings(container: Container) -> None:
    container.register(
        ApplicationSettings,
        factory=lambda: ApplicationSettings(),
        scope=Scope.singleton,
    )
    container.register(
        RedisSettings,
        factory=lambda: RedisSettings(),
        scope=Scope.singleton,
    )


def _register_models(container: Container) -> None:
    container.register(
        type[BaseRefreshSession],
        instance=RefreshSession,
    )


def _register_services(container: Container) -> None:
    container.register(HealthService, scope=Scope.singleton)
    container.register(UserService, scope=Scope.singleton)
    container.register(TodoService, scope=Scope.singleton)  # Add this line
```

## Understanding Registration Options

The container supports several registration patterns:

### Type-Based Registration (Most Common)

```python
container.register(TodoService, scope=Scope.singleton)
```

punq auto-resolves dependencies from the `__init__` signature. Since `TodoService.__init__` takes no parameters, no dependencies need to be injected.

### Factory-Based Registration

Used when the service needs configuration from environment variables:

```python
container.register(
    ApplicationSettings,
    factory=lambda: ApplicationSettings(),
    scope=Scope.singleton,
)
```

### Instance Registration

Used for concrete implementations of abstract types:

```python
container.register(
    type[BaseRefreshSession],
    instance=RefreshSession,
)
```

## Scopes

| Scope | Description |
|-------|-------------|
| `Scope.singleton` | One instance per container (most common) |
| `Scope.transient` | New instance every time (rarely needed) |

For stateless services like `TodoService`, always use `Scope.singleton`.

## Verify Registration

You can verify the registration works:

```bash
uv run python src/manage.py shell
```

```python
from ioc.container import get_container
from core.todo.services import TodoService

container = get_container()
todo_service = container.resolve(TodoService)

print(todo_service)  # <core.todo.services.TodoService object at ...>

# Verify it's a singleton
todo_service_2 = container.resolve(TodoService)
print(todo_service is todo_service_2)  # True
```

## What You've Learned

In this step, you:

1. Understood the IoC container structure
2. Registered `TodoService` as a singleton
3. Learned about different registration patterns
4. Verified the registration works

## Next Step

In [Step 3: HTTP API & Admin](03-http-api.md), you'll create REST endpoints and a Django admin panel for managing todos.
