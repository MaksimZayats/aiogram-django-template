# Bot & Dispatcher Factories

How the bot and dispatcher are created and configured with dependency injection.

## Bot Factory

The `BotFactory` creates the aiogram `Bot` instance:

```python
# src/delivery/bot/factories.py

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

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
```

### Bot Settings

```python
# src/delivery/bot/settings.py

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramBotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TELEGRAM_BOT_")

    token: SecretStr
    parse_mode: str = "HTML"
```

### Parse Modes

- `HTML` — Use HTML tags (`<b>bold</b>`, `<i>italic</i>`)
- `Markdown` — Use Markdown (`**bold**`, `*italic*`)
- `MarkdownV2` — Extended Markdown with escaping rules

## Dispatcher Factory

The `DispatcherFactory` creates the dispatcher and registers controllers:

```python
# src/delivery/bot/factories.py

from aiogram import Bot, Dispatcher, Router
from aiogram.types import BotCommand

from delivery.bot.controllers.commands import CommandsController


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
            BotCommand(command="/start", description="Re-start the bot"),
            BotCommand(command="/id", description="Get the user and chat ids"),
        ])
```

### Key Components

1. **Controller Injection** — Controllers are injected via `__init__` and registered with routers
2. **Router Registration** — Each controller gets its own router via `register(router)`
3. **Startup Hook** — `dispatcher.startup()` runs `_set_bot_commands` on start
4. **Bot Commands** — Sets the command menu shown in Telegram

## IoC Registration

Factories and controllers are registered in the container:

```python
# src/ioc/container.py

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

## Adding New Controllers

To add a new controller to the bot:

### 1. Create the Controller

```python
# src/delivery/bot/controllers/admin.py

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from infrastructure.delivery.controllers import AsyncController


class AdminController(AsyncController):
    def register(self, registry: Router) -> None:
        registry.message.register(
            self.handle_stats,
            Command(commands=["stats"]),
        )

    async def handle_stats(self, message: Message) -> None:
        await message.answer("Admin stats here...")
```

### 2. Register in IoC Container

```python
# src/ioc/container.py

from delivery.bot.controllers.admin import AdminController

def _register_bot(container: Container) -> None:
    # ... existing registrations ...
    container.register(AdminController, scope=Scope.singleton)
```

### 3. Inject into DispatcherFactory

```python
# src/delivery/bot/factories.py

from delivery.bot.controllers.admin import AdminController


class DispatcherFactory:
    def __init__(
        self,
        bot: Bot,
        commands_controller: CommandsController,
        admin_controller: AdminController,  # Add new controller
    ) -> None:
        self._bot = bot
        self._commands_controller = commands_controller
        self._admin_controller = admin_controller

    def __call__(self) -> Dispatcher:
        dispatcher = Dispatcher()

        # Register commands router
        commands_router = Router(name="commands")
        dispatcher.include_router(commands_router)
        self._commands_controller.register(commands_router)

        # Register admin router
        admin_router = Router(name="admin")
        dispatcher.include_router(admin_router)
        self._admin_controller.register(admin_router)

        dispatcher.startup()(self._set_bot_commands)

        return dispatcher
```

### 4. Update Bot Commands

```python
async def _set_bot_commands(self) -> None:
    await self._bot.set_my_commands([
        BotCommand(command="/start", description="Re-start the bot"),
        BotCommand(command="/id", description="Get the user and chat ids"),
        BotCommand(command="/stats", description="Show statistics"),  # New
    ])
```

!!! note "Command Limit"
    Telegram allows up to 100 commands, but keep it reasonable for UX.

## Customizing the Bot

### Default Properties

Modify `DefaultBotProperties` for global settings:

```python
def __call__(self) -> Bot:
    return Bot(
        token=self._settings.token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=self._settings.parse_mode,
            link_preview_is_disabled=True,  # Disable link previews
            protect_content=True,            # Prevent forwarding
        ),
    )
```

### Adding Middleware

Add middleware to the dispatcher:

```python
def __call__(self) -> Dispatcher:
    dispatcher = Dispatcher()

    # Add middleware
    dispatcher.message.middleware(LoggingMiddleware())
    dispatcher.callback_query.middleware(ThrottlingMiddleware())

    # Register controllers
    router = Router(name="commands")
    dispatcher.include_router(router)
    self._commands_controller.register(router)

    return dispatcher
```

## Webhook Mode

For production, you might use webhooks instead of polling:

```python
# In __main__.py
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(
        url="https://your-domain.com/webhook",
        secret_token="your-secret",
    )

def main() -> None:
    configure_infrastructure(service_name="bot")
    container = get_container()

    bot = container.resolve(Bot)
    dispatcher = container.resolve(Dispatcher)

    dispatcher.startup.register(on_startup)

    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token="your-secret",
    ).register(app, path="/webhook")

    web.run_app(app, host="0.0.0.0", port=8080)
```

## Related Topics

- [Handlers](handlers.md) — Controller-based handlers
- [Controller Pattern](../concepts/controller-pattern.md) — Pattern explanation
- [Your First Bot Command](../tutorials/first-bot-command.md) — Tutorial
- [Factory Pattern](../concepts/factory-pattern.md) — Pattern explanation
