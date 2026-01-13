# Your First Bot Command

Add a new Telegram bot command with message handling.

## Goal

Create a `/echo` command that repeats the user's message back to them.

## Prerequisites

1. Get a bot token from [@BotFather](https://t.me/BotFather)
2. Add `TELEGRAM_BOT_TOKEN=your-token` to `.env`

## Step 1: Add the Handler

Edit `src/delivery/bot/handlers.py`:

```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command(commands=["start"]))
async def handle_start_command(message: Message) -> None:
    if message.from_user is None:
        return

    await message.answer("Hello! This is a bot.")


@router.message(Command(commands=["id"]))
async def handle_id_command(message: Message) -> None:
    if message.from_user is None:
        return

    await message.answer(
        f"User Id: <b>{message.from_user.id}</b>\nChat Id: <b>{message.chat.id}</b>",
    )


# Add your new command
@router.message(Command(commands=["echo"]))
async def handle_echo_command(message: Message) -> None:
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
    def __init__(
        self,
        bot: Bot,
    ) -> None:
        self._bot = bot

    def __call__(self) -> Dispatcher:
        dispatcher = Dispatcher()
        dispatcher.include_router(router)
        dispatcher.startup()(self._set_bot_commands)

        return dispatcher

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

## Adding Filters

Use aiogram filters for more complex logic:

```python
from aiogram.filters import Command, CommandStart
from aiogram import F


# Only respond to specific text
@router.message(F.text == "ping")
async def handle_ping(message: Message) -> None:
    await message.answer("pong")


# Command with arguments
@router.message(Command(commands=["greet"]))
async def handle_greet(message: Message) -> None:
    args = message.text.split()[1:]  # Get arguments after command
    name = args[0] if args else "stranger"
    await message.answer(f"Hello, {name}!")


# Handle callback queries (inline buttons)
from aiogram.types import CallbackQuery

@router.callback_query(F.data == "button_clicked")
async def handle_callback(callback: CallbackQuery) -> None:
    await callback.answer("Button clicked!")
```

## Using Dependency Injection

For handlers that need services, you can access them via the dispatcher:

```python
# In delivery/bot/__main__.py
def main() -> None:
    configure_infrastructure(service_name="bot")
    container = get_container()

    bot = container.resolve(Bot)
    dispatcher = container.resolve(Dispatcher)

    # Pass container to handlers via dispatcher data
    dispatcher.run_polling(bot, container=container)
```

Then in handlers:

```python
from punq import Container

@router.message(Command(commands=["user"]))
async def handle_user_command(
    message: Message,
    container: Container,
) -> None:
    # Resolve services from container
    user_service = container.resolve(UserService)
    # ... use the service
```

## Error Handling

Use aiogram's error handling:

```python
from aiogram import Router
from aiogram.types import ErrorEvent

router = Router()


@router.error()
async def handle_error(event: ErrorEvent) -> None:
    # Log the error
    import logging
    logging.exception("Error in handler", exc_info=event.exception)

    # Optionally notify the user
    if event.update.message:
        await event.update.message.answer(
            "An error occurred. Please try again later."
        )
```

## Next Steps

- [Bot & Dispatcher Factories](../bot/factories.md) — How the bot is configured
- [Handlers](../bot/handlers.md) — Advanced handler patterns
- [aiogram Documentation](https://docs.aiogram.dev/) — Official aiogram docs
