# IoC Container

Inversion of Control (IoC) is a design principle where the control of object creation is inverted from the component that needs the dependency to an external container. This template uses **punq**, a lightweight dependency injection container for Python.

## What is Dependency Injection?

Dependency Injection (DI) is a technique where an object receives its dependencies from an external source rather than creating them itself.

### Without DI (Tight Coupling)

```python
class UserController:
    def __init__(self) -> None:
        # Controller creates its own dependencies
        self._user_service = UserService()  # Hard to test, hard to replace
```

### With DI (Loose Coupling)

```python
class UserController:
    def __init__(self, user_service: UserService) -> None:
        # Dependencies are provided from outside
        self._user_service = user_service  # Easy to test, easy to replace
```

The IoC container automates this process by:

1. Reading type annotations from `__init__` signatures
2. Resolving dependencies automatically
3. Managing object lifecycles

## Container Organization

The container is organized into three registry modules, each responsible for a different architectural layer:

```
ioc/
+-- container.py          # Main container setup
+-- registries/
    +-- core.py           # Domain services, settings, models
    +-- infrastructure.py # Cross-cutting concerns (JWT, auth)
    +-- delivery.py       # Controllers, factories, external interfaces
```

### Registration Flow

```python
# ioc/container.py
from punq import Container

from ioc.registries.core import register_core
from ioc.registries.delivery import register_delivery
from ioc.registries.infrastructure import register_infrastructure


def get_container() -> Container:
    container = Container()

    register_core(container)           # 1. Domain layer first
    register_infrastructure(container) # 2. Infrastructure depends on core
    register_delivery(container)       # 3. Delivery depends on both

    return container
```

!!! note "Registration Order Matters"
    Components are registered in dependency order. Core components have no dependencies, infrastructure may depend on core, and delivery depends on both.

## Registration Patterns

### Type-Based Registration (Auto-Resolve)

The simplest pattern. The container inspects `__init__` type annotations and automatically resolves dependencies:

```python
# ioc/registries/core.py
from punq import Container, Scope
from core.health.services import HealthService
from core.user.services import UserService


def _register_services(container: Container) -> None:
    container.register(HealthService, scope=Scope.singleton)
    container.register(UserService, scope=Scope.singleton)
```

When `UserController` is resolved, the container sees it needs `UserService` and provides it automatically:

```python
# This happens automatically when you resolve UserController
class UserController(Controller):
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service
```

### Factory-Based Registration

Use factories when components need special initialization, typically for settings that load from environment variables:

```python
# ioc/registries/infrastructure.py
container.register(
    JWTServiceSettings,
    factory=lambda: JWTServiceSettings(),  # Creates instance from env vars
)
```

The factory is called once (for singletons) or each time (for transient) when the type is resolved.

### Instance-Based Registration

Use instance registration for concrete implementations of abstract types:

```python
# ioc/registries/core.py
from core.user.models import RefreshSession
from infrastructure.django.refresh_sessions.models import BaseRefreshSession


def _register_models(container: Container) -> None:
    container.register(
        type[BaseRefreshSession],  # Abstract type
        instance=RefreshSession,   # Concrete implementation
    )
```

This allows services to depend on the abstract type while receiving the concrete implementation:

```python
class RefreshSessionService:
    def __init__(
        self,
        settings: RefreshSessionServiceSettings,
        refresh_session_model: type[BaseRefreshSession],  # Receives RefreshSession
    ) -> None:
        self._refresh_session_model = refresh_session_model
```

## Scopes

### Singleton Scope

The same instance is returned for all resolutions:

```python
container.register(UserService, scope=Scope.singleton)

# Both calls return the same instance
service1 = container.resolve(UserService)
service2 = container.resolve(UserService)
assert service1 is service2  # True
```

!!! tip "When to Use Singleton"
    Use singleton for:

    - Stateless services
    - Settings objects
    - Connection pools
    - Factories (they manage their own caching)

### Transient Scope (Default)

A new instance is created for each resolution:

```python
container.register(SomeService)  # Transient by default

service1 = container.resolve(SomeService)
service2 = container.resolve(SomeService)
assert service1 is service2  # False - different instances
```

!!! tip "When to Use Transient"
    Use transient for:

    - Request-scoped objects
    - Objects with mutable state
    - Objects that should not be shared

## Resolution

### Basic Resolution

```python
container = get_container()
user_service = container.resolve(UserService)
```

### Resolution with Automatic Dependency Injection

The container resolves the entire dependency graph:

```python
# When resolving UserController, the container:
# 1. Sees UserController needs JWTAuthFactory and UserService
# 2. Resolves JWTAuthFactory (which needs JWTService, which needs JWTServiceSettings)
# 3. Resolves UserService
# 4. Creates UserController with both dependencies

controller = container.resolve(UserController)
```

```
UserController
    |
    +-- JWTAuthFactory
    |       |
    |       +-- JWTService
    |               |
    |               +-- JWTServiceSettings
    |
    +-- UserService
```

## Registry Organization

### Core Registry (`registries/core.py`)

Registers domain-layer components:

```python
def register_core(container: Container) -> None:
    _register_settings(container)  # ApplicationSettings, RedisSettings
    _register_models(container)    # Model type mappings
    _register_services(container)  # HealthService, UserService
```

### Infrastructure Registry (`registries/infrastructure.py`)

Registers cross-cutting concerns:

```python
def register_infrastructure(container: Container) -> None:
    _register_jwt(container)              # JWTServiceSettings, JWTService
    _register_refresh_sessions(container) # RefreshSessionService
    _register_auth(container)             # JWTAuthFactory
```

### Delivery Registry (`registries/delivery.py`)

Registers external interface components:

```python
def register_delivery(container: Container) -> None:
    _register_http(container)             # NinjaAPIFactory, URLPatternsFactory
    _register_http_controllers(container) # HealthController, UserController

    _register_celery(container)           # CeleryAppFactory, TasksRegistryFactory
    _register_celery_controllers(container)

    _register_bot(container)              # BotFactory, DispatcherFactory
    _register_bot_controllers(container)
```

## Benefits

### 1. Loose Coupling

Components depend on abstractions, not concrete implementations:

```python
class RefreshSessionService:
    def __init__(
        self,
        refresh_session_model: type[BaseRefreshSession],  # Abstract
    ) -> None:
        ...
```

### 2. Testability

Any component can be replaced in tests:

```python
def test_with_mock_service(container: Container) -> None:
    mock_service = MagicMock()
    container.register(UserService, instance=mock_service)

    # All components that depend on UserService now use the mock
    controller = container.resolve(UserController)
```

### 3. Configuration Flexibility

Different configurations for different environments:

```python
# Production
container.register(
    JWTServiceSettings,
    factory=lambda: JWTServiceSettings(),  # Loads from env vars
)

# Testing
container.register(
    JWTServiceSettings,
    instance=JWTServiceSettings(
        secret_key=SecretStr("test-secret"),
        algorithm="HS256",
    ),
)
```

### 4. Explicit Dependencies

All dependencies are visible in the `__init__` signature:

```python
class UserTokenController(Controller):
    def __init__(
        self,
        jwt_auth_factory: JWTAuthFactory,
        jwt_service: JWTService,
        refresh_token_service: RefreshSessionService,
        user_service: UserService,
    ) -> None:
        # All dependencies are explicit and documented
```

## Common Patterns

### Registering a New Service

```python
# 1. Create the service in core/
# core/item/services.py
class ItemService:
    def list_items(self) -> list[Item]:
        return list(Item.objects.all())

# 2. Register in ioc/registries/core.py
def _register_services(container: Container) -> None:
    container.register(HealthService, scope=Scope.singleton)
    container.register(UserService, scope=Scope.singleton)
    container.register(ItemService, scope=Scope.singleton)  # Add this
```

### Registering Settings

```python
# ioc/registries/core.py
container.register(
    ApplicationSettings,
    factory=lambda: ApplicationSettings(),
    scope=Scope.singleton,
)
```

### Registering Controllers

```python
# ioc/registries/delivery.py
def _register_http_controllers(container: Container) -> None:
    container.register(HealthController, scope=Scope.singleton)
    container.register(UserController, scope=Scope.singleton)
    container.register(ItemController, scope=Scope.singleton)  # Add this
```

## Summary

The IoC container provides:

| Feature | Benefit |
|---------|---------|
| Auto-resolution | Less boilerplate, automatic dependency wiring |
| Scopes | Control over object lifecycles |
| Registry organization | Clear separation by architectural layer |
| Test overrides | Easy mocking and stubbing |
| Explicit dependencies | Self-documenting code |

Understanding the IoC container is essential for extending this template. When adding new components, always register them in the appropriate registry based on their architectural layer.
