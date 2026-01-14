# IoC Container (punq)

The Inversion of Control (IoC) container is the heart of the application's architecture. It manages object creation and dependency resolution.

## What is punq?

[punq](https://github.com/bobthemighty/punq) is a lightweight dependency injection container for Python. It:

- Resolves dependencies automatically from type hints
- Supports singleton and transient scopes
- Has no external dependencies

## Container Configuration

The container is configured in `src/ioc/container.py`:

```python
from punq import Container, Scope


def get_container() -> Container:
    container = Container()

    _register_services(container)
    _register_http(container)
    _register_controllers(container)
    _register_celery(container)
    _register_bot(container)

    return container
```

All entry points (HTTP, bot, Celery) use the same container configuration, ensuring consistent behavior.

## Registration Methods

### Type-Based Registration

For classes whose dependencies can be resolved from `__init__` signature:

```python
container.register(JWTService, scope=Scope.singleton)
```

punq will automatically resolve `JWTServiceSettings` when creating `JWTService`:

```python
class JWTService:
    def __init__(self, settings: JWTServiceSettings) -> None:
        self._settings = settings
```

### Factory-Based Registration

For objects that need special construction (e.g., loading from environment):

```python
container.register(
    JWTServiceSettings,
    factory=lambda: JWTServiceSettings(),
)
```

This is necessary because Pydantic settings classes read from environment variables during instantiation.

### Instance Registration

For registering concrete implementations of abstract types:

```python
container.register(
    type[BaseRefreshSession],
    instance=RefreshSession,
)
```

This maps the abstract `BaseRefreshSession` to the concrete `RefreshSession` model.

## Scopes

### Singleton

One instance for the entire application lifetime:

```python
container.register(JWTService, scope=Scope.singleton)
```

Use for:

- Services with expensive initialization
- Stateless services
- Configuration objects

### Transient (Default)

New instance on every resolution:

```python
container.register(SomeService)  # Default scope is transient
```

Use for:

- Objects with request-specific state
- Objects that should not be shared

## Resolving Dependencies

### Direct Resolution

```python
container = get_container()
jwt_service = container.resolve(JWTService)
```

### Automatic Resolution

When a registered class depends on another registered type, punq resolves the entire dependency chain:

```python
# JWTAuth depends on JWTService
# JWTService depends on JWTServiceSettings
# punq resolves the full chain automatically

jwt_auth = container.resolve(JWTAuth)
```

## Real Example: HTTP Controllers

```python
def _register_controllers(container: Container) -> None:
    container.register(HealthController, scope=Scope.singleton)
    container.register(UserController, scope=Scope.singleton)
    container.register(UserTokenController, scope=Scope.singleton)
```

The `UserTokenController` has these dependencies:

```python
class UserTokenController(Controller):
    def __init__(
        self,
        jwt_service: JWTService,
        refresh_token_service: RefreshSessionService,
        jwt_auth: JWTAuth,
    ) -> None:
        self._jwt_service = jwt_service
        self._refresh_token_service = refresh_token_service
        self._jwt_auth = jwt_auth
```

punq resolves all three dependencies automatically because they're registered in the container.

## Real Example: Bot Controllers

```python
def _register_bot(container: Container) -> None:
    container.register(
        TelegramBotSettings,
        lambda: TelegramBotSettings(),
        scope=Scope.singleton,
    )

    # Register controllers
    container.register(CommandsController, scope=Scope.singleton)

    # Register factories
    container.register(BotFactory, scope=Scope.singleton)
    container.register(
        Bot,
        factory=lambda: container.resolve(BotFactory)(),
        scope=Scope.singleton,
    )

    container.register(DispatcherFactory, scope=Scope.singleton)
    container.register(
        Dispatcher,
        factory=lambda: container.resolve(DispatcherFactory)(),
        scope=Scope.singleton,
    )
```

The `DispatcherFactory` has these dependencies:

```python
class DispatcherFactory:
    def __init__(
        self,
        bot: Bot,
        commands_controller: CommandsController,
    ) -> None:
        self._bot = bot
        self._commands_controller = commands_controller
```

punq resolves `Bot` and `CommandsController` automatically, then injects them into `DispatcherFactory`.

## Factories with Container Access

For complex creation logic, factories can access the container:

```python
container.register(
    NinjaAPI,
    factory=lambda: container.resolve(NinjaAPIFactory)(),
    scope=Scope.singleton,
)
```

The `NinjaAPIFactory` is resolved first, then called to create the `NinjaAPI` instance.

## Testing with IoC

The IoC pattern enables easy testing through dependency override:

```python
@pytest.fixture(scope="function")
def container(django_user_model: type[User]) -> Container:
    container = get_container()

    # Override registrations for testing
    container.register(TestNinjaAPIFactory, scope=Scope.singleton)
    container.register(TestClientFactory, scope=Scope.singleton)

    return container
```

See [Mocking IoC Dependencies](../testing/mocking-ioc.md) for detailed testing patterns.

## Best Practices

### 1. Register at Startup

All registrations should happen during application startup, not during request handling.

### 2. Use Singletons for Stateless Services

```python
# Good: Stateless service as singleton
container.register(JWTService, scope=Scope.singleton)
```

### 3. Explicit Dependencies

Always declare dependencies in `__init__`:

```python
# Good: Explicit dependency
class UserController:
    def __init__(self, auth: JWTAuth) -> None:
        self._auth = auth

# Avoid: Hidden dependency
class UserController:
    def __init__(self) -> None:
        self._auth = get_container().resolve(JWTAuth)  # Hidden!
```

### 4. Interface-Based Registration

For swappable implementations, register against interfaces:

```python
container.register(
    type[BaseRefreshSession],
    instance=RefreshSession,
)
```

This allows tests to provide mock implementations.

## Related Topics

- [Controller Pattern](controller-pattern.md) — How controllers use IoC
- [Factory Pattern](factory-pattern.md) — Creating complex objects
- [Mocking IoC Dependencies](../testing/mocking-ioc.md) — Testing patterns
