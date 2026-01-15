# IoC Container

The IoC (Inversion of Control) container manages dependency injection using [punq](https://github.com/bobthemighty/punq), a simple DI library for Python.

## What is Dependency Injection?

Without DI, classes create their own dependencies:

```python
# ❌ BAD - Class creates its own dependencies
class UserController:
    def __init__(self):
        self._user_service = UserService()  # Tight coupling
        self._jwt_auth = JWTAuth(JWTService(JWTSettings()))  # Hard to test
```

With DI, dependencies are provided from outside:

```python
# ✅ GOOD - Dependencies injected
class UserController:
    def __init__(self, user_service: UserService, jwt_auth: JWTAuth) -> None:
        self._user_service = user_service
        self._jwt_auth = jwt_auth
```

## Container Structure

The container is configured in `src/ioc/`:

```
ioc/
├── container.py              # get_container() function
└── registries/
    ├── core.py               # Services, settings, models
    ├── infrastructure.py     # JWT, auth, base classes
    └── delivery.py           # Controllers, factories
```

## Registration Order

Registration order matters because some components depend on others:

```python
# src/ioc/container.py
def get_container() -> Container:
    container = Container()
    register_core(container)          # 1. Settings, services
    register_infrastructure(container) # 2. JWT, auth
    register_delivery(container)       # 3. Controllers, factories
    return container
```

## Registration Patterns

### Type-Based Registration

The most common pattern. punq auto-resolves dependencies from the `__init__` signature:

```python
# Service with no dependencies
container.register(HealthService, scope=Scope.singleton)

# Service with dependencies - punq resolves automatically
container.register(UserController, scope=Scope.singleton)
# punq sees __init__(user_service: UserService, jwt_auth: JWTAuth)
# and resolves both from the container
```

### Factory-Based Registration

Used when the object needs special construction (e.g., loading from environment):

```python
# Settings loaded from environment variables
container.register(
    ApplicationSettings,
    factory=lambda: ApplicationSettings(),
    scope=Scope.singleton,
)

# Complex object with custom initialization
container.register(
    NinjaAPI,
    factory=lambda: container.resolve(NinjaAPIFactory)(),
    scope=Scope.singleton,
)
```

### Instance Registration

Used to register a specific instance, often for abstract types:

```python
# Concrete implementation of abstract type
container.register(
    type[BaseRefreshSession],
    instance=RefreshSession,
)

# Pre-configured instance
container.register(
    SomeConfig,
    instance=SomeConfig(debug=True, timeout=30),
)
```

## Scopes

| Scope | Description | Use Case |
|-------|-------------|----------|
| `Scope.singleton` | One instance per container | Services, controllers, settings |
| `Scope.transient` | New instance every resolution | Rarely needed |

For stateless services, always use `Scope.singleton`:

```python
container.register(UserService, scope=Scope.singleton)
container.register(TodoService, scope=Scope.singleton)
container.register(HealthService, scope=Scope.singleton)
```

## Resolution

### Manual Resolution

```python
from ioc.container import get_container

container = get_container()
user_service = container.resolve(UserService)
```

### Automatic Resolution

When resolving a class, punq automatically resolves its dependencies:

```python
# UserController.__init__(user_service: UserService, jwt_auth: JWTAuth)
controller = container.resolve(UserController)
# punq automatically:
# 1. Resolves UserService
# 2. Resolves JWTAuth
# 3. Creates UserController with both
```

## Example: Full Registration

```python
# src/ioc/registries/core.py
from punq import Container, Scope

from core.todo.services import TodoService
from core.user.services import UserService
from core.health.services import HealthService


def register_core(container: Container) -> None:
    _register_settings(container)
    _register_services(container)


def _register_settings(container: Container) -> None:
    container.register(
        ApplicationSettings,
        factory=lambda: ApplicationSettings(),
        scope=Scope.singleton,
    )


def _register_services(container: Container) -> None:
    # Services are registered as singletons
    # Dependencies are auto-resolved from __init__ signature
    container.register(HealthService, scope=Scope.singleton)
    container.register(UserService, scope=Scope.singleton)
    container.register(TodoService, scope=Scope.singleton)
```

## Testing with Container

### Per-Test Container

Each test gets a fresh container to avoid state pollution:

```python
@pytest.fixture(scope="function")
def container() -> Container:
    return get_container()
```

### Overriding Registrations

Override registrations for mocking in tests:

```python
def test_with_mock_service(container: Container) -> None:
    # Create mock
    mock_service = MagicMock(spec=TodoService)
    mock_service.list_todos.return_value = []

    # Override registration
    container.register(TodoService, instance=mock_service)

    # Now all resolutions use the mock
    controller = container.resolve(TodoController)
    # controller._todo_service is mock_service
```

## Common Patterns

### Lazy Factories

For objects that need late initialization:

```python
container.register(
    NinjaAPI,
    factory=lambda: container.resolve(NinjaAPIFactory)(),
    scope=Scope.singleton,
)
```

### Type Aliases

For registering concrete types against abstract base classes:

```python
container.register(
    type[BaseRefreshSession],
    instance=RefreshSession,
)

# Now this works:
session_class = container.resolve(type[BaseRefreshSession])
# Returns RefreshSession
```

### Settings with Prefixes

```python
container.register(
    JWTServiceSettings,
    factory=lambda: JWTServiceSettings(),  # Loads JWT_* env vars
    scope=Scope.singleton,
)

container.register(
    CelerySettings,
    factory=lambda: CelerySettings(),  # Loads CELERY_* env vars
    scope=Scope.singleton,
)
```

## Debugging

### Check What's Registered

```python
container = get_container()

# Resolve and inspect
service = container.resolve(TodoService)
print(type(service))  # <class 'core.todo.services.TodoService'>

# Verify singleton behavior
service2 = container.resolve(TodoService)
print(service is service2)  # True
```

### Missing Registration Errors

If you see `punq.MissingDependencyError`, ensure:

1. The dependency is registered before it's needed
2. The type annotation matches exactly
3. Registration order is correct (core → infrastructure → delivery)

## Related Concepts

- [Service Layer](service-layer.md) - What gets registered
- [Factory Pattern](factory-pattern.md) - Creating complex objects
- [Pydantic Settings](pydantic-settings.md) - Configuration registration
