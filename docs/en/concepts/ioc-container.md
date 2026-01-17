# IoC Container

Inversion of Control (IoC) is a design principle where the control of object creation is inverted from the component that needs the dependency to an external container. This template uses **punq**, a lightweight dependency injection container for Python, enhanced with **auto-registration** capabilities.

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

## Auto-Registration

The key feature of this template's IoC implementation is **auto-registration**. Instead of explicitly registering every service, the `AutoRegisteringContainer` automatically registers services when they're first resolved.

### How It Works

```python
from ioc.container import ContainerFactory

# Create container via factory
container = ContainerFactory()()

# No explicit registration needed - just resolve
user_service = container.resolve(UserService)  # Auto-registered as singleton
```

When you resolve a type that hasn't been registered:

1. The container inspects the class's `__init__` type annotations
2. If it's a Pydantic `BaseSettings` subclass, it's registered with a factory (loads from env vars)
3. Otherwise, it's registered as a singleton
4. Dependencies are recursively auto-registered

### Pydantic Settings Auto-Detection

Settings classes are automatically detected and handled specially:

```python
# Pydantic Settings are auto-registered with factory pattern
jwt_settings = container.resolve(JWTServiceSettings)  # Loads from environment

# Equivalent to manually doing:
# container.register(JWTServiceSettings, factory=lambda: JWTServiceSettings())
```

## Container Organization

The container setup is minimal due to auto-registration:

```
ioc/
├── container.py      # ContainerFactory and configuration
└── registries.py     # Explicit registrations (special cases only)
```

### ContainerFactory

The `ContainerFactory` creates and configures the container:

```python
# ioc/container.py
class ContainerFactory:
    def __call__(
        self,
        *,
        configure_django: bool = True,
        configure_logging: bool = True,
        instrument_libraries: bool = True,
    ) -> AutoRegisteringContainer:
        container = AutoRegisteringContainer()

        if configure_django:
            self._configure_django(container)

        if configure_logging:
            self._configure_logging(container)

        if instrument_libraries:
            self._instrument_libraries(container)

        self._register(container)

        return container
```

### Explicit Registry (Special Cases Only)

Only abstract type mappings need explicit registration:

```python
# ioc/registries.py
class Registry:
    def register(self, container: Container) -> None:
        # Map abstract base types to concrete implementations
        container.register(
            type[AbstractBaseUser],
            instance=User,
        )
        container.register(
            type[BaseRefreshSession],
            instance=RefreshSession,
        )
```

!!! note "When to Use Explicit Registration"
    Explicit registration is only needed for:

    - Abstract type → concrete type mappings
    - Named registrations (string keys)
    - Special factory logic beyond Pydantic Settings

## AutoRegisteringContainer

The `AutoRegisteringContainer` extends punq's `Container` with auto-registration:

```python
# infrastructure/punq/container.py
class AutoRegisteringContainer(Container):
    def __init__(
        self,
        settings_scope: Scope = Scope.singleton,
        default_scope: Scope = Scope.singleton,
    ) -> None:
        super().__init__()
        self._settings_scope = settings_scope
        self._default_scope = default_scope

    def resolve(self, service_key: type[T], **kwargs: Any) -> T:
        self._register_if_missing(service_key)
        return super().resolve(service_key, **kwargs)

    def _register_if_missing(self, service_key: Any) -> None:
        if self.registrations[service_key]:
            return  # Already registered

        if issubclass(service_key, BaseSettings):
            # Pydantic Settings: use factory pattern
            self.register(service_key, factory=lambda: service_key(), scope=self._settings_scope)
        else:
            # Regular class: auto-register as singleton
            self.register(service_key, scope=self._default_scope)

        # Recursively register dependencies
        for param_type in get_annotations(service_key.__init__).values():
            self._register_if_missing(param_type)
```

## Scopes

### Singleton Scope (Default)

The same instance is returned for all resolutions:

```python
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

### Transient Scope

A new instance is created for each resolution:

```python
container.register(SomeService, scope=Scope.transient)

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
from ioc.container import ContainerFactory

container = ContainerFactory()()
user_service = container.resolve(UserService)
```

### Automatic Dependency Graph Resolution

The container resolves the entire dependency graph:

```python
# When resolving UserController, the container:
# 1. Sees UserController needs JWTAuthFactory and UserService
# 2. Auto-registers and resolves JWTAuthFactory (which needs JWTService -> JWTServiceSettings)
# 3. Auto-registers and resolves UserService
# 4. Creates UserController with all dependencies

controller = container.resolve(UserController)
```

```
UserController
    │
    ├── JWTAuthFactory
    │       │
    │       └── JWTService
    │               │
    │               └── JWTServiceSettings (from env vars)
    │
    └── UserService
```

## Benefits

### 1. Minimal Boilerplate

No need to register every service explicitly:

```python
# Old approach (explicit registration)
container.register(HealthService, scope=Scope.singleton)
container.register(UserService, scope=Scope.singleton)
container.register(ItemService, scope=Scope.singleton)
# ... and so on for every service

# New approach (auto-registration)
# Just resolve - no registration needed
health_service = container.resolve(HealthService)
```

### 2. Loose Coupling

Components depend on abstractions, not concrete implementations:

```python
class RefreshSessionService:
    def __init__(
        self,
        refresh_session_model: type[BaseRefreshSession],  # Abstract
    ) -> None:
        ...
```

### 3. Testability

Any component can be replaced in tests:

```python
def test_with_mock_service(container: Container) -> None:
    mock_service = MagicMock()
    container.register(UserService, instance=mock_service)

    # All components that depend on UserService now use the mock
    controller = container.resolve(UserController)
```

### 4. Configuration Flexibility

Different configurations for different environments:

```python
# Production: auto-registration loads from env vars
container = ContainerFactory()()

# Testing: override with test values
container.register(
    JWTServiceSettings,
    instance=JWTServiceSettings(
        secret_key=SecretStr("test-secret"),
        algorithm="HS256",
    ),
)
```

### 5. Explicit Dependencies

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

### Adding a New Service

With auto-registration, just create the service - no registration needed:

```python
# 1. Create the service in core/
# core/item/services.py
class ItemService:
    def list_items(self) -> list[Item]:
        return list(Item.objects.all())

# 2. Use it - auto-registered when first resolved
item_service = container.resolve(ItemService)
```

### Adding a New Controller

Controllers are also auto-registered:

```python
# delivery/http/item/controllers.py
@dataclass
class ItemController(Controller):
    _item_service: ItemService  # Auto-injected

    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/v1/items",
            endpoint=self.list_items,
            methods=["GET"],
        )
```

### Mapping Abstract to Concrete Types

The only case requiring explicit registration:

```python
# ioc/registries.py
container.register(
    type[BaseRefreshSession],  # Abstract type
    instance=RefreshSession,   # Concrete implementation
)
```

## Summary

The IoC container provides:

| Feature | Benefit |
|---------|---------|
| Auto-registration | Zero boilerplate for most services |
| Pydantic Settings detection | Automatic env var loading |
| Scopes | Control over object lifecycles |
| Test overrides | Easy mocking and stubbing |
| Explicit dependencies | Self-documenting code |

Understanding the IoC container is essential for extending this template. The auto-registration feature means you can focus on writing services and controllers without worrying about registration boilerplate.
