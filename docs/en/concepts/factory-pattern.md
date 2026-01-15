# Factory Pattern

Factories encapsulate complex object construction, especially when objects require configuration, caching, or composition of multiple dependencies. This pattern is essential for creating framework-specific objects like Django-Ninja APIs, Celery apps, and aiogram dispatchers.

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
class NinjaAPIFactory:
    def __call__(self) -> NinjaAPI:
        if self._settings.environment == Environment.PRODUCTION:
            docs_decorator = staff_member_required
        else:
            docs_decorator = None

        return NinjaAPI(docs_decorator=docs_decorator)
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

### NinjaAPIFactory

Creates and configures the Django-Ninja API with all controllers:

```python
class NinjaAPIFactory:
    def __init__(
        self,
        settings: ApplicationSettings,
        health_controller: HealthController,
        user_token_controller: UserTokenController,
        user_controller: UserController,
    ) -> None:
        self._settings = settings
        self._health_controller = health_controller
        self._user_token_controller = user_token_controller
        self._user_controller = user_controller

    def __call__(
        self,
        urls_namespace: str | None = None,
    ) -> NinjaAPI:
        # Environment-specific configuration
        if self._settings.environment == Environment.PRODUCTION:
            docs_decorator = staff_member_required
        else:
            docs_decorator = None

        ninja_api = NinjaAPI(
            urls_namespace=urls_namespace,
            docs_decorator=docs_decorator,
        )

        # Register all controllers
        health_router = Router(tags=["health"])
        ninja_api.add_router("/", health_router)
        self._health_controller.register(registry=health_router)

        user_router = Router(tags=["user"])
        ninja_api.add_router("/", user_router)
        self._user_controller.register(registry=user_router)
        self._user_token_controller.register(registry=user_router)

        return ninja_api
```

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
    +-- NinjaAPIFactory
    |       |
    |       +-- HealthController
    |       +-- UserController
    |       +-- UserTokenController
    |
    +-- AdminSiteFactory
```

```python
class URLPatternsFactory:
    def __init__(
        self,
        api_factory: NinjaAPIFactory,
        admin_site_factory: AdminSiteFactory,
    ) -> None:
        self._api_factory = api_factory
        self._admin_site_factory = admin_site_factory

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
    container.register(NinjaAPIFactory, scope=Scope.singleton)
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
class NinjaAPIFactory:
    def __call__(
        self,
        urls_namespace: str | None = None,  # Allows unique namespace per test
    ) -> NinjaAPI:
        ...

# In tests:
def test_create_user(container: Container) -> None:
    api_factory = container.resolve(NinjaAPIFactory)
    api = api_factory(urls_namespace="test_create_user")  # Unique namespace
    client = TestClient(api)
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
container.register(NinjaAPIFactory, scope=Scope.singleton)
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
