# Factory Pattern

Factories encapsulate complex object construction, especially when objects require configuration, caching, or composition of multiple dependencies. This pattern is essential for creating framework-specific objects like FastAPI apps and Celery apps.

## Why Factories?

### 1. Complex Object Construction

Some objects require multi-step initialization that doesn't fit in a simple constructor:

```python
class CeleryAppFactory:
    def __call__(self) -> Celery:
        celery_app = Celery(
            "main",
            broker=self._redis_settings.redis_url.get_secret_value(),
            backend=self._redis_settings.redis_url.get_secret_value(),
        )

        self._configure_app(celery_app)
        self._configure_beat_schedule(celery_app)

        return celery_app
```

### 2. Configuration-Based Creation

Objects may need different configurations based on environment:

```python
class FastAPIFactory:
    def __call__(self) -> FastAPI:
        if self._settings.environment == Environment.PRODUCTION:
            docs_url = None  # Disable docs in production
        else:
            docs_url = "/docs"

        return FastAPI(docs_url=docs_url)
```

### 3. Caching (Singleton-like Behavior)

Factories can cache expensive objects to avoid repeated construction:

```python
class CeleryAppFactory:
    def __init__(self) -> None:
        self._instance: Celery | None = None

    def __call__(self) -> Celery:
        if self._instance is not None:
            return self._instance

        self._instance = self._create_celery_app()
        return self._instance
```

### 4. Deferred Construction

Objects that should only be created when needed, not at container setup time.

## Factory Structure

A factory follows this pattern:

```python
class SomeFactory:
    def __init__(
        self,
        dependency_a: DependencyA,
        dependency_b: DependencyB,
    ) -> None:
        # Store dependencies for later use
        self._dependency_a = dependency_a
        self._dependency_b = dependency_b

        # Optional: cache for singleton-like behavior
        self._instance: SomeObject | None = None

    def __call__(self, *args, **kwargs) -> SomeObject:
        # Optional: return cached instance
        if self._instance is not None:
            return self._instance

        # Create and configure the object
        obj = self._create_object(*args, **kwargs)

        # Optional: cache the result
        self._instance = obj
        return self._instance

    def _create_object(self, *args, **kwargs) -> SomeObject:
        # Complex construction logic here
        ...
```

## Caching Pattern

Many factories in this template cache their result to ensure only one instance exists:

```python
class TasksRegistryFactory:
    def __init__(
        self,
        celery_app_factory: CeleryAppFactory,
        ping_controller: PingTaskController,
    ) -> None:
        self._instance: TasksRegistry | None = None
        self._celery_app_factory = celery_app_factory
        self._ping_controller = ping_controller

    def __call__(self) -> TasksRegistry:
        if self._instance is not None:
            return self._instance

        celery_app = self._celery_app_factory()
        registry = TasksRegistry(app=celery_app)
        self._ping_controller.register(celery_app)

        self._instance = registry
        return self._instance
```

!!! note "Why Cache in Factories?"
    While the IoC container has `Scope.singleton`, factories need internal caching because:

    1. The factory itself is a singleton, but `__call__` can be invoked multiple times
    2. Some objects (like Celery apps) must be truly single instances
    3. Construction may have side effects that should only happen once

## Real-World Examples

### FastAPIFactory

Creates and configures the FastAPI application with all controllers:

```python
from dataclasses import dataclass
from fastapi import APIRouter, FastAPI

@dataclass
class FastAPIFactory:
    _settings: ApplicationSettings
    _health_controller: HealthController
    _user_token_controller: UserTokenController
    _user_controller: UserController

    def __call__(self) -> FastAPI:
        # Environment-specific configuration
        if self._settings.environment == Environment.PRODUCTION:
            docs_url = None  # Disable docs in production
        else:
            docs_url = "/docs"

        app = FastAPI(docs_url=docs_url)

        # Register all controllers
        health_router = APIRouter(tags=["health"])
        self._health_controller.register(registry=health_router)
        app.include_router(health_router)

        user_router = APIRouter(tags=["user"])
        self._user_controller.register(registry=user_router)
        self._user_token_controller.register(registry=user_router)
        app.include_router(user_router)

        return app
```

!!! note "Simplified Example"
    This example is simplified for clarity. The production implementation in `src/delivery/http/factories.py` includes additional configuration for middleware, CORS, telemetry, and lifespan management.

### CeleryAppFactory

Creates and configures the Celery application:

```python
class CeleryAppFactory:
    def __init__(
        self,
        settings: CelerySettings,
        redis_settings: RedisSettings,
    ) -> None:
        self._instance: Celery | None = None
        self._settings = settings
        self._redis_settings = redis_settings

    def __call__(self) -> Celery:
        if self._instance is not None:
            return self._instance

        celery_app = Celery(
            "main",
            broker=self._redis_settings.redis_url.get_secret_value(),
            backend=self._redis_settings.redis_url.get_secret_value(),
        )

        self._configure_app(celery_app=celery_app)
        self._configure_beat_schedule(celery_app=celery_app)

        self._instance = celery_app
        return self._instance

    def _configure_app(self, celery_app: Celery) -> None:
        celery_app.conf.update(
            timezone=application_settings.time_zone,
            enable_utc=True,
            **self._settings.model_dump(),
        )

    def _configure_beat_schedule(self, celery_app: Celery) -> None:
        celery_app.conf.beat_schedule = {
            "ping-every-minute": {
                "task": TaskName.PING,
                "schedule": 60.0,
            },
        }
```

### TasksRegistryFactory

Composes the Celery app with task controllers:

```python
class TasksRegistryFactory:
    def __init__(
        self,
        celery_app_factory: CeleryAppFactory,
        ping_controller: PingTaskController,
    ) -> None:
        self._instance: TasksRegistry | None = None
        self._celery_app_factory = celery_app_factory
        self._ping_controller = ping_controller

    def __call__(self) -> TasksRegistry:
        if self._instance is not None:
            return self._instance

        celery_app = self._celery_app_factory()
        registry = TasksRegistry(app=celery_app)
        self._ping_controller.register(celery_app)

        self._instance = registry
        return self._instance
```

## Factory Composition

Factories can depend on other factories, forming a construction hierarchy:

```
URLPatternsFactory
    |
    +-- FastAPIFactory
    |       |
    |       +-- HealthController
    |       +-- UserController
    |       +-- UserTokenController
    |
    +-- AdminSiteFactory
```

```python
from dataclasses import dataclass

@dataclass
class URLPatternsFactory:
    _api_factory: FastAPIFactory
    _admin_site_factory: AdminSiteFactory

    def __call__(self) -> list[URLResolver]:
        api = self._api_factory()
        admin_site = self._admin_site_factory()

        return [
            path("admin/", admin_site.urls),
            path("api/", api.urls),
        ]
```

## Integration with IoC Container

Factories are registered as singletons in the IoC container:

```python
# ioc/registries/delivery.py
def _register_http(container: Container) -> None:
    container.register(FastAPIFactory, scope=Scope.singleton)
    container.register(AdminSiteFactory, scope=Scope.singleton)
    container.register(URLPatternsFactory, scope=Scope.singleton)

def _register_celery(container: Container) -> None:
    container.register(CeleryAppFactory, scope=Scope.singleton)
    container.register(TasksRegistryFactory, scope=Scope.singleton)
```

The container resolves factory dependencies automatically:

```python
# When resolving TasksRegistryFactory, the container:
# 1. Resolves CeleryAppFactory (needs CelerySettings, RedisSettings)
# 2. Resolves PingTaskController
# 3. Creates TasksRegistryFactory with both dependencies

registry_factory = container.resolve(TasksRegistryFactory)
registry = registry_factory()  # Creates the actual registry
```

## Testing with Factories

Factories enable test isolation by allowing custom configurations:

```python
from fastapi.testclient import TestClient

# In tests:
def test_create_user(container: Container) -> None:
    api_factory = container.resolve(FastAPIFactory)
    app = api_factory()
    client = TestClient(app)
    ...
```

## When to Use Factories

| Scenario | Use Factory? |
|----------|--------------|
| Object needs multi-step configuration | Yes |
| Object depends on environment settings | Yes |
| Object should be cached/singleton | Yes |
| Object construction has side effects | Yes |
| Simple object with injected dependencies | No - use direct IoC registration |

## Factory vs Direct Registration

### Use Direct Registration When:

```python
# Simple service with no complex construction
container.register(UserService, scope=Scope.singleton)
```

### Use Factory When:

```python
# Complex construction, caching, or composition needed
container.register(FastAPIFactory, scope=Scope.singleton)
```

## Summary

The Factory pattern provides:

| Feature | Benefit |
|---------|---------|
| Encapsulated construction | Complex setup logic is isolated |
| Caching | Expensive objects created once |
| Configuration | Environment-specific behavior |
| Composition | Factories can use other factories |
| Testability | Custom configurations for tests |

Factories are the bridge between the IoC container and framework-specific objects that require careful construction and configuration.
