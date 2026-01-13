# Factory Pattern

Factories encapsulate complex object creation logic, integrating with the IoC container.

## Why Factories?

- **Encapsulation** — Hide complex creation logic
- **IoC Integration** — Dependencies resolved by container
- **Testability** — Override factories in tests
- **Configuration** — Apply settings during creation

## Factory Structure

A factory is a callable class:

```python
class SomeFactory:
    def __init__(self, dependency: SomeDependency) -> None:
        self._dependency = dependency

    def __call__(self) -> SomeObject:
        return SomeObject(self._dependency)
```

## Real Examples

### NinjaAPI Factory

Creates the HTTP API with all controllers registered:

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
        if self._settings.environment == Environment.PRODUCTION:
            docs_decorator = staff_member_required
        else:
            docs_decorator = None

        ninja_api = NinjaAPI(
            urls_namespace=urls_namespace,
            docs_decorator=docs_decorator,
        )

        # Register controllers
        health_router = Router(tags=["health"])
        ninja_api.add_router("/", health_router)
        self._health_controller.register(registry=health_router)

        user_router = Router(tags=["user"])
        ninja_api.add_router("/", user_router)
        self._user_controller.register(registry=user_router)
        self._user_token_controller.register(registry=user_router)

        return ninja_api
```

Key features:

- Receives controllers via dependency injection
- Configures API based on environment
- Returns fully configured `NinjaAPI` instance

### Celery App Factory

Creates the Celery application with beat schedule:

```python
class CeleryAppFactory:
    def __init__(self, settings: CelerySettings) -> None:
        self._instance: Celery | None = None
        self._settings = settings

    def __call__(self) -> Celery:
        if self._instance is not None:
            return self._instance

        celery_app = Celery(
            "main",
            broker=self._settings.redis_settings.redis_url.get_secret_value(),
            backend=self._settings.redis_settings.redis_url.get_secret_value(),
        )

        self._configure_app(celery_app)
        self._configure_beat_schedule(celery_app)

        self._instance = celery_app
        return self._instance

    def _configure_app(self, celery_app: Celery) -> None:
        celery_app.conf.update(timezone=application_settings.time_zone)

    def _configure_beat_schedule(self, celery_app: Celery) -> None:
        celery_app.conf.beat_schedule = {
            "ping-every-minute": {
                "task": TaskName.PING,
                "schedule": 60.0,
            },
        }
```

Key features:

- Caches instance (singleton pattern)
- Configures broker and backend from settings
- Sets up beat schedule

!!! note "Testing with Cached Instances"
    The cached instance doesn't require manual cleanup in tests. Each test receives a fresh IoC container (function-scoped fixture), which creates a new factory instance with its own cache. See [Testing Architecture](../testing/overview.md) for details.

### Bot Factory

Creates the Telegram bot:

```python
class BotFactory:
    def __init__(self, settings: TelegramBotSettings) -> None:
        self._settings = settings

    def __call__(self) -> Bot:
        return Bot(
            token=self._settings.token.get_secret_value(),
            default=DefaultBotProperties(
                parse_mode=self._settings.parse_mode,
            ),
        )
```

### Dispatcher Factory

Creates the bot dispatcher with handlers:

```python
class DispatcherFactory:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    def __call__(self) -> Dispatcher:
        dispatcher = Dispatcher()
        dispatcher.include_router(router)
        dispatcher.startup()(self._set_bot_commands)
        return dispatcher

    async def _set_bot_commands(self) -> None:
        await self._bot.set_my_commands([
            BotCommand(command="/start", description="Re-start the bot"),
            BotCommand(command="/id", description="Get the user and chat ids"),
        ])
```

## IoC Container Registration

Factories are registered in the container:

```python
def _register_http(container: Container) -> None:
    container.register(NinjaAPIFactory, scope=Scope.singleton)
    container.register(
        NinjaAPI,
        factory=lambda: container.resolve(NinjaAPIFactory)(),
        scope=Scope.singleton,
    )
```

This pattern:

1. Registers the factory class
2. Registers the product type with a factory function that resolves and calls the factory

## Test Factories

Test factories extend production factories for testing:

```python
class TestNinjaAPIFactory(NinjaAPIFactory):
    __test__ = False  # Tell pytest this isn't a test class

    def __call__(self, urls_namespace: str | None = None) -> NinjaAPI:
        # Always use unique namespace to avoid URL conflicts
        return super().__call__(urls_namespace=str(uuid.uuid7()))
```

```python
class TestClientFactory:
    __test__ = False

    def __init__(self, api_factory: TestNinjaAPIFactory) -> None:
        self._api_factory = api_factory

    def __call__(self, **kwargs: Any) -> TestClient:
        return TestClient(self._api_factory(), **kwargs)
```

## Tasks Registry Factory

Creates the task registry with all task controllers registered:

```python
class TasksRegistryFactory:
    def __init__(
        self,
        celery_app: Celery,
        ping_controller: PingTaskController,
    ) -> None:
        self._instance: TasksRegistry | None = None
        self._celery_app = celery_app
        self._ping_controller = ping_controller

    def __call__(self) -> TasksRegistry:
        if self._instance is not None:
            return self._instance

        registry = TasksRegistry(app=self._celery_app)
        self._ping_controller.register(self._celery_app)

        self._instance = registry
        return self._instance
```

## Best Practices

### 1. Dependencies via Constructor

```python
# Good: Dependencies injected
class MyFactory:
    def __init__(self, settings: Settings, service: Service) -> None:
        self._settings = settings
        self._service = service

# Avoid: Resolving inside factory
class MyFactory:
    def __call__(self) -> Object:
        service = get_container().resolve(Service)  # Hidden dependency
```

### 2. Cache When Appropriate

```python
class ExpensiveFactory:
    def __init__(self) -> None:
        self._instance: ExpensiveObject | None = None

    def __call__(self) -> ExpensiveObject:
        if self._instance is None:
            self._instance = ExpensiveObject()
        return self._instance
```

### 3. Parameter Support

```python
class APIFactory:
    def __call__(
        self,
        urls_namespace: str | None = None,  # Optional customization
    ) -> NinjaAPI:
        return NinjaAPI(urls_namespace=urls_namespace)
```

### 4. Configuration in Factory

Apply settings during creation, not after:

```python
# Good: Configuration during creation
class AppFactory:
    def __call__(self) -> App:
        app = App()
        app.config.from_object(self._settings)
        return app
```

## Related Topics

- [IoC Container](ioc-container.md) — How factories integrate with IoC
- [Test Factories](../testing/test-factories.md) — Testing patterns
- [Controller Pattern](controller-pattern.md) — Controllers created by factories
