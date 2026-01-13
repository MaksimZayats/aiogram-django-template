# Handlers

Command handlers and message processing with aiogram.

## Handler Structure

Handlers are defined in `src/delivery/bot/handlers.py`:

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
        f"User Id: <b>{message.from_user.id}</b>\n"
        f"Chat Id: <b>{message.chat.id}</b>",
    )
```

## Filters

### Command Filter

Match specific commands:

```python
from aiogram.filters import Command

@router.message(Command(commands=["help"]))
async def handle_help(message: Message) -> None:
    await message.answer("Help message here")

# Multiple commands
@router.message(Command(commands=["start", "help"]))
async def handle_start_or_help(message: Message) -> None:
    await message.answer("Welcome or help!")
```

### Text Filter

Match specific text:

```python
from aiogram import F

@router.message(F.text == "ping")
async def handle_ping(message: Message) -> None:
    await message.answer("pong")

# Case-insensitive
@router.message(F.text.lower() == "hello")
async def handle_hello(message: Message) -> None:
    await message.answer("Hi there!")

# Contains text
@router.message(F.text.contains("help"))
async def handle_help_request(message: Message) -> None:
    await message.answer("How can I help?")
```

### Content Type Filter

Match by message content:

```python
from aiogram.types import ContentType

@router.message(F.content_type == ContentType.PHOTO)
async def handle_photo(message: Message) -> None:
    await message.answer("Nice photo!")

@router.message(F.content_type == ContentType.DOCUMENT)
async def handle_document(message: Message) -> None:
    await message.answer("Document received!")
```

### Combined Filters

```python
@router.message(F.text, F.chat.type == "private")
async def handle_private_text(message: Message) -> None:
    await message.answer("Private message received")
```

## Command Arguments

Parse arguments from commands:

```python
@router.message(Command(commands=["greet"]))
async def handle_greet(message: Message) -> None:
    # /greet John
    if message.text is None:
        return

    parts = message.text.split(maxsplit=1)
    name = parts[1] if len(parts) > 1 else "stranger"
    await message.answer(f"Hello, {name}!")
```

## Callback Queries

Handle inline button clicks:

```python
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

@router.message(Command(commands=["menu"]))
async def show_menu(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Option 1", callback_data="option_1"),
            InlineKeyboardButton(text="Option 2", callback_data="option_2"),
        ]
    ])
    await message.answer("Choose an option:", reply_markup=keyboard)


@router.callback_query(F.data == "option_1")
async def handle_option_1(callback: CallbackQuery) -> None:
    await callback.answer("You chose option 1!")
    await callback.message.edit_text("Option 1 selected")


@router.callback_query(F.data == "option_2")
async def handle_option_2(callback: CallbackQuery) -> None:
    await callback.answer("You chose option 2!")
    await callback.message.edit_text("Option 2 selected")
```

## State Management

For multi-step conversations:

```python
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    name = State()
    age = State()


@router.message(Command(commands=["form"]))
async def start_form(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer("What's your name?")


@router.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("How old are you?")


@router.message(Form.age)
async def process_age(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    name = data.get("name")
    age = message.text

    await state.clear()
    await message.answer(f"Hello {name}, you are {age} years old!")
```

## Middleware

Add custom middleware:

```python
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        print(f"Received: {event.text}")
        result = await handler(event, data)
        print(f"Handled: {event.text}")
        return result


# Register in dispatcher factory
dispatcher.message.middleware(LoggingMiddleware())
```

## Error Handling

Handle errors in handlers:

```python
from aiogram.types import ErrorEvent

@router.error()
async def handle_error(event: ErrorEvent) -> None:
    import logging
    logging.exception("Error in handler", exc_info=event.exception)

    if event.update.message:
        await event.update.message.answer(
            "An error occurred. Please try again."
        )
```

## Dependency Injection

Access container in handlers:

```python
# In __main__.py
dispatcher.run_polling(bot, container=container)

# In handlers
from punq import Container

@router.message(Command(commands=["user_count"]))
async def handle_user_count(
    message: Message,
    container: Container,
) -> None:
    from core.user.models import User
    count = User.objects.count()
    await message.answer(f"Total users: {count}")
```

## Organizing Handlers

Split handlers into modules:

```
delivery/bot/
├── handlers/
│   ├── __init__.py
│   ├── commands.py      # Command handlers
│   ├── callbacks.py     # Callback query handlers
│   └── admin.py         # Admin commands
└── factories.py
```

```python
# handlers/__init__.py
from aiogram import Router

from .commands import router as commands_router
from .callbacks import router as callbacks_router

main_router = Router()
main_router.include_router(commands_router)
main_router.include_router(callbacks_router)
```

## Best Practices

### 1. Always Check for None

```python
@router.message(Command(commands=["start"]))
async def handle_start(message: Message) -> None:
    if message.from_user is None:
        return  # Guard against None
    await message.answer(f"Hello, {message.from_user.first_name}!")
```

### 2. Use HTML Parse Mode

```python
await message.answer(
    "<b>Bold</b> and <i>italic</i> text",
    parse_mode="HTML",
)
```

### 3. Handle Errors Gracefully

```python
@router.message(Command(commands=["data"]))
async def handle_data(message: Message) -> None:
    try:
        data = fetch_data()
        await message.answer(f"Data: {data}")
    except Exception:
        await message.answer("Failed to fetch data. Please try again.")
```

### 4. Use Inline Keyboards for Actions

```python
keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Confirm", callback_data="confirm")],
    [InlineKeyboardButton(text="Cancel", callback_data="cancel")],
])
await message.answer("Are you sure?", reply_markup=keyboard)
```

## Related Topics

- [Bot & Dispatcher Factories](factories.md) — Factory configuration
- [Your First Bot Command](../tutorials/first-bot-command.md) — Tutorial
- [aiogram Documentation](https://docs.aiogram.dev/) — Official docs
