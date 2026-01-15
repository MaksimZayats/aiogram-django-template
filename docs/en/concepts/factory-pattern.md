# Factory Pattern

Factories create and configure complex objects. They encapsulate the construction logic and receive dependencies via injection.

## Why Factories?

Some objects require:

- Multiple dependencies
- Configuration from settings
- Complex initialization logic
- Framework-specific setup

Instead of putting this logic in the IoC container, we use factories.

## Factory Structure

A factory is a callable class that creates and configures an object:

```python
class SomeFactory:
    def __init__(
        self,
        setting: SomeSetting,
        dependency: SomeDependency,
    ) -> None:
        self._setting = setting
        self._dependency = dependency

    def __call__(self) -> SomeObject:
        return SomeObject(
            config=self._setting.value,
            dependency=self._dependency,
        )
```

## HTTP API Factory

```python
# src/delivery/http/factories.py
from ninja import NinjaAPI, Router

from core.configs.core import ApplicationSettings
from delivery.http.health.controllers import HealthController
from delivery.http.user.controllers import UserController


class NinjaAPIFactory:
    def __init__(
        self,
        settings: ApplicationSettings,
        health_controller: HealthController,
        user_controller: UserController,
    ) -> None:
        self._settings = settings
        self._health_controller = health_controller
        self._user_controller = user_controller

    def __call__(
        self,
        urls_namespace: str | None = None,
    ) -> NinjaAPI:
        # Create API instance
        ninja_api = NinjaAPI(
            urls_namespace=urls_namespace,
            docs_decorator=self._get_docs_decorator(),
        )

        # Create routers and register controllers
        health_router = Router(tags=["health"])
        ninja_api.add_router("/", health_router)
        self._health_controller.register(registry=health_router)

        user_router = Router(tags=["user"])
        ninja_api.add_router("/", user_router)
        self._user_controller.register(registry=user_router)

        return ninja_api

    def _get_docs_decorator(self):
        if self._settings.environment == Environment.PRODUCTION:
            return staff_member_required
        return None
```

Key patterns:

- **Dependencies injected** - Controllers and settings come from IoC
- **Optional parameters** - `urls_namespace` allows customization for tests
- **Configuration logic** - Production vs development docs access

## Celery App Factory

```python
# src/delivery/tasks/factories.py
from celery import Celery
from celery.schedules import crontab

from core.configs.core import RedisSettings
from delivery.tasks.registry import TaskName
from delivery.tasks.settings import CelerySettings


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

        self._configure_app(celery_app)
        self._configure_beat_schedule(celery_app)

        self._instance = celery_app
        return self._instance

    def _configure_app(self, celery_app: Celery) -> None:
        celery_app.conf.update(**self._settings.model_dump())

    def _configure_beat_schedule(self, celery_app: Celery) -> None:
        celery_app.conf.beat_schedule = {
            "ping-every-minute": {
                "task": TaskName.PING,
                "schedule": 60.0,
            },
        }
```

Key patterns:

- **Singleton caching** - `_instance` prevents recreating the Celery app
- **Settings from Pydantic** - `model_dump()` converts settings to dict
- **Beat schedule** - Periodic tasks configured in factory

## Tasks Registry Factory

```python
# src/delivery/tasks/factories.py
from celery import Celery

from delivery.tasks.registry import TasksRegistry
from delivery.tasks.tasks.ping import PingTaskController


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

        # Register task controllers
        self._ping_controller.register(self._celery_app)

        self._instance = registry
        return self._instance
```

## Bot Factory

```python
# src/delivery/bot/factories.py
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties

from delivery.bot.controllers.commands import CommandsController
from delivery.bot.settings import TelegramBotSettings


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


class DispatcherFactory:
    def __init__(
        self,
        bot: Bot,
        commands_controller: CommandsController,
    ) -> None:
        self._bot = bot
        self._commands_controller = commands_controller

    def __call__(self) -> Dispatcher:
        dispatcher = Dispatcher()

        router = Router(name="commands")
        dispatcher.include_router(router)
        self._commands_controller.register(router)

        dispatcher.startup()(self._set_bot_commands)

        return dispatcher

    async def _set_bot_commands(self) -> None:
        await self._bot.set_my_commands([
            BotCommand(command="/start", description="Start the bot"),
        ])
```

## Admin Factory

```python
# src/delivery/http/factories.py
from django.contrib.admin import AdminSite
from django.contrib.admin.sites import site as default_site

from core.user.models import User
from delivery.http.user.admin import UserAdmin


class AdminSiteFactory:
    def __call__(self) -> AdminSite:
        default_site.register(User, admin_class=UserAdmin)
        return default_site
```

Note: Admin factories don't use IoC for admin classes because:

- Admin classes are only used once at startup
- They require direct model imports (acceptable exception)

## IoC Registration

Factories are registered and called via IoC:

```python
# src/ioc/registries/delivery.py
def _register_http(container: Container) -> None:
    # Register factory
    container.register(NinjaAPIFactory, scope=Scope.singleton)

    # Register product via factory call
    container.register(
        NinjaAPI,
        factory=lambda: container.resolve(NinjaAPIFactory)(),
        scope=Scope.singleton,
    )
```

This pattern:

1. Registers the factory as a singleton
2. Registers the product with a lambda that resolves and calls the factory
3. The product is also a singleton (created once, reused)

## Test Factories

For testing, we create extended factories:

```python
# tests/integration/factories.py
from delivery.http.factories import NinjaAPIFactory


class TestNinjaAPIFactory(NinjaAPIFactory):
    __test__ = False  # Prevent pytest collection

    def __call__(
        self,
        urls_namespace: str | None = None,
    ) -> NinjaAPI:
        # Use unique namespace per test to avoid conflicts
        return super().__call__(urls_namespace=str(uuid.uuid7()))


class TestClientFactory:
    __test__ = False

    def __init__(
        self,
        api_factory: TestNinjaAPIFactory,
        jwt_service: JWTService,
    ) -> None:
        self._api_factory = api_factory
        self._jwt_service = jwt_service

    def __call__(
        self,
        auth_for_user: User | None = None,
        headers: dict[str, str] | None = None,
    ) -> TestClient:
        headers = headers or {}

        if auth_for_user is not None:
            token = self._jwt_service.issue_access_token(user_id=auth_for_user.pk)
            headers["Authorization"] = f"Bearer {token}"

        return TestClient(self._api_factory(), headers=headers)
```

## Best Practices

### 1. Singleton Caching

For expensive objects, cache the instance:

```python
class ExpensiveFactory:
    def __init__(self) -> None:
        self._instance: ExpensiveObject | None = None

    def __call__(self) -> ExpensiveObject:
        if self._instance is not None:
            return self._instance
        self._instance = ExpensiveObject()
        return self._instance
```

### 2. Configuration from Settings

Use Pydantic settings for configuration:

```python
class ApiFactory:
    def __init__(self, settings: ApiSettings) -> None:
        self._settings = settings

    def __call__(self) -> Api:
        return Api(
            timeout=self._settings.timeout,
            retries=self._settings.retries,
        )
```

### 3. Optional Customization

Allow customization for tests:

```python
class ApiFactory:
    def __call__(
        self,
        base_url: str | None = None,  # Override for tests
    ) -> Api:
        return Api(
            base_url=base_url or self._settings.base_url,
        )
```

## Related Concepts

- [IoC Container](ioc-container.md) - How factories are registered
- [Controller Pattern](controller-pattern.md) - What factories create
- [Pydantic Settings](pydantic-settings.md) - Configuration for factories
