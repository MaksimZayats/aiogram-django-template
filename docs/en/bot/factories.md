# Bot & Dispatcher Factories

How the bot and dispatcher are created and configured.

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

The `DispatcherFactory` creates the dispatcher with routers and commands:

```python
# src/delivery/bot/factories.py

from aiogram import Dispatcher
from aiogram.types import BotCommand

from delivery.bot.handlers import router


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

### Key Components

1. **Router Registration** — `dispatcher.include_router(router)` adds all handlers
2. **Startup Hook** — `dispatcher.startup()` runs `_set_bot_commands` on start
3. **Bot Commands** — Sets the command menu shown in Telegram

## IoC Registration

Factories are registered in the container:

```python
# src/ioc/container.py

def _register_bot(container: Container) -> None:
    container.register(
        TelegramBotSettings,
        lambda: TelegramBotSettings(),
        scope=Scope.singleton,
    )

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

## Adding Bot Commands

To add a new command to the menu, update `_set_bot_commands`:

```python
async def _set_bot_commands(self) -> None:
    await self._bot.set_my_commands([
        BotCommand(command="/start", description="Re-start the bot"),
        BotCommand(command="/id", description="Get the user and chat ids"),
        BotCommand(command="/help", description="Show help message"),  # New
        BotCommand(command="/settings", description="Bot settings"),   # New
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

    dispatcher.include_router(router)
    return dispatcher
```

## Multiple Routers

Organize handlers with multiple routers:

```python
from delivery.bot.handlers.commands import commands_router
from delivery.bot.handlers.callbacks import callbacks_router
from delivery.bot.handlers.admin import admin_router


def __call__(self) -> Dispatcher:
    dispatcher = Dispatcher()

    dispatcher.include_router(commands_router)
    dispatcher.include_router(callbacks_router)
    dispatcher.include_router(admin_router)

    return dispatcher
```

## Webhook Mode

For production, you might use webhooks instead of polling:

```python
# In main.py
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

- [Handlers](handlers.md) — Command handlers
- [Your First Bot Command](../tutorials/first-bot-command.md) — Tutorial
- [Factory Pattern](../concepts/factory-pattern.md) — Pattern explanation
