# Your First Bot Command

Add a new Telegram bot command using the AsyncController pattern.

## Goal

Create a `/echo` command that repeats the user's message back to them.

## Prerequisites

1. Get a bot token from [@BotFather](https://t.me/BotFather)
2. Add `TELEGRAM_BOT_TOKEN=your-token` to `.env`

## Step 1: Add the Handler to CommandsController

Edit `src/delivery/bot/controllers/commands.py`:

```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from infrastructure.delivery.controllers import AsyncController


class CommandsController(AsyncController):
    def register(self, registry: Router) -> None:
        registry.message.register(
            self.handle_start_command,
            Command(commands=["start"]),
        )
        registry.message.register(
            self.handle_id_command,
            Command(commands=["id"]),
        )
        # Add your new command
        registry.message.register(
            self.handle_echo_command,
            Command(commands=["echo"]),
        )

    async def handle_start_command(self, message: Message) -> None:
        if message.from_user is None:
            return
        await message.answer("Hello! This is a bot.")

    async def handle_id_command(self, message: Message) -> None:
        if message.from_user is None:
            return
        await message.answer(
            f"User Id: <b>{message.from_user.id}</b>\n"
            f"Chat Id: <b>{message.chat.id}</b>",
        )

    # Add your new handler
    async def handle_echo_command(self, message: Message) -> None:
        if message.from_user is None:
            return

        # Get the text after the command
        text = message.text
        if text is None:
            await message.answer("Please provide text to echo.")
            return

        # Remove the /echo part
        echo_text = text.replace("/echo", "").strip()

        if not echo_text:
            await message.answer("Please provide text to echo. Usage: /echo your message")
            return

        await message.answer(f"You said: {echo_text}")
```

## Step 2: Register the Command (Optional)

To show the command in Telegram's command menu, edit `src/delivery/bot/factories.py`:

```python
class DispatcherFactory:
    # ... existing code ...

    async def _set_bot_commands(self) -> None:
        await self._bot.set_my_commands(
            [
                BotCommand(command="/start", description="Re-start the bot"),
                BotCommand(command="/id", description="Get the user and chat ids"),
                BotCommand(command="/echo", description="Echo your message"),  # Add this
            ],
        )
```

## Step 3: Test It

### Start the Bot

```bash
make bot-dev
```

### Send Commands

In Telegram, message your bot:

```
/echo Hello, world!
```

Expected response:

```
You said: Hello, world!
```

## Creating a New Controller

For more complex features, create a separate controller:

### 1. Create the Controller File

```python
# src/delivery/bot/controllers/echo.py

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from infrastructure.delivery.controllers import AsyncController


class EchoController(AsyncController):
    def register(self, registry: Router) -> None:
        registry.message.register(
            self.handle_echo,
            Command(commands=["echo"]),
        )

    async def handle_echo(self, message: Message) -> None:
        if message.from_user is None:
            return

        text = message.text
        if text is None:
            await message.answer("Please provide text to echo.")
            return

        echo_text = text.replace("/echo", "").strip()
        if not echo_text:
            await message.answer("Usage: /echo your message")
            return

        await message.answer(f"You said: {echo_text}")
```

### 2. Register in IoC Container

```python
# src/ioc/container.py

from delivery.bot.controllers.echo import EchoController

def _register_bot(container: Container) -> None:
    # ... existing registrations ...
    container.register(EchoController, scope=Scope.singleton)
```

### 3. Inject into DispatcherFactory

```python
# src/delivery/bot/factories.py

from delivery.bot.controllers.echo import EchoController


class DispatcherFactory:
    def __init__(
        self,
        bot: Bot,
        commands_controller: CommandsController,
        echo_controller: EchoController,  # Add new controller
    ) -> None:
        self._bot = bot
        self._commands_controller = commands_controller
        self._echo_controller = echo_controller

    def __call__(self) -> Dispatcher:
        dispatcher = Dispatcher()

        commands_router = Router(name="commands")
        dispatcher.include_router(commands_router)
        self._commands_controller.register(commands_router)

        echo_router = Router(name="echo")
        dispatcher.include_router(echo_router)
        self._echo_controller.register(echo_router)

        dispatcher.startup()(self._set_bot_commands)

        return dispatcher
```

## Adding Filters

Use aiogram filters for more complex logic:

```python
from aiogram.filters import Command
from aiogram import F


class AdvancedController(AsyncController):
    def register(self, registry: Router) -> None:
        # Only respond to specific text
        registry.message.register(self.handle_ping, F.text == "ping")

        # Command with arguments
        registry.message.register(self.handle_greet, Command(commands=["greet"]))

        # Handle callback queries (inline buttons)
        registry.callback_query.register(
            self.handle_callback,
            F.data == "button_clicked",
        )

    async def handle_ping(self, message: Message) -> None:
        await message.answer("pong")

    async def handle_greet(self, message: Message) -> None:
        if message.text is None:
            return
        args = message.text.split()[1:]  # Get arguments after command
        name = args[0] if args else "stranger"
        await message.answer(f"Hello, {name}!")

    async def handle_callback(self, callback: CallbackQuery) -> None:
        await callback.answer("Button clicked!")
```

## Using Dependency Injection

For handlers that need services:

```python
from core.user.services import UserService


class UserBotController(AsyncController):
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    def register(self, registry: Router) -> None:
        registry.message.register(
            self.handle_profile,
            Command(commands=["profile"]),
        )

    async def handle_profile(self, message: Message) -> None:
        if message.from_user is None:
            return

        user = await self._user_service.get_by_telegram_id(message.from_user.id)
        if user:
            await message.answer(f"Your profile: {user.username}")
        else:
            await message.answer("Profile not found. Please register first.")
```

The IoC container automatically resolves `UserService` when creating the controller.

## Exception Handling

Override `handle_exception()` for custom error handling:

```python
class CommandsController(AsyncController):
    async def handle_exception(self, exception: Exception) -> None:
        import logging
        logging.exception("Error in bot handler", exc_info=exception)

        # Custom handling for specific exceptions
        if isinstance(exception, UserNotFoundError):
            # Can't easily notify user here without message context
            return

        # Re-raise unhandled exceptions
        raise exception
```

## Next Steps

- [Bot & Dispatcher Factories](../bot/factories.md) — How the bot is configured
- [Handlers](../bot/handlers.md) — Advanced handler patterns
- [Controller Pattern](../concepts/controller-pattern.md) — Understanding AsyncController
- [aiogram Documentation](https://docs.aiogram.dev/) — Official aiogram docs
