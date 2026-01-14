# Handlers

Command handlers and message processing with aiogram using the AsyncController pattern.

## Controller Structure

Handlers are organized in controller classes in `src/delivery/bot/controllers/`:

```python
# src/delivery/bot/controllers/commands.py

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
```

Key points:

- Extend `AsyncController` from `infrastructure.delivery.controllers`
- Implement `register()` to register handlers with the Router
- Use `registry.message.register()` to register message handlers
- All handler methods must be `async`

## Filters

### Command Filter

Match specific commands:

```python
from aiogram.filters import Command

class CommandsController(AsyncController):
    def register(self, registry: Router) -> None:
        registry.message.register(
            self.handle_help,
            Command(commands=["help"]),
        )

    async def handle_help(self, message: Message) -> None:
        await message.answer("Help message here")
```

Multiple commands:

```python
def register(self, registry: Router) -> None:
    registry.message.register(
        self.handle_start_or_help,
        Command(commands=["start", "help"]),
    )
```

### Text Filter

Match specific text:

```python
from aiogram import F

class TextController(AsyncController):
    def register(self, registry: Router) -> None:
        registry.message.register(self.handle_ping, F.text == "ping")
        registry.message.register(self.handle_hello, F.text.lower() == "hello")
        registry.message.register(self.handle_help_request, F.text.contains("help"))

    async def handle_ping(self, message: Message) -> None:
        await message.answer("pong")

    async def handle_hello(self, message: Message) -> None:
        await message.answer("Hi there!")

    async def handle_help_request(self, message: Message) -> None:
        await message.answer("How can I help?")
```

### Content Type Filter

Match by message content:

```python
from aiogram.types import ContentType

class MediaController(AsyncController):
    def register(self, registry: Router) -> None:
        registry.message.register(
            self.handle_photo,
            F.content_type == ContentType.PHOTO,
        )
        registry.message.register(
            self.handle_document,
            F.content_type == ContentType.DOCUMENT,
        )

    async def handle_photo(self, message: Message) -> None:
        await message.answer("Nice photo!")

    async def handle_document(self, message: Message) -> None:
        await message.answer("Document received!")
```

### Combined Filters

```python
def register(self, registry: Router) -> None:
    registry.message.register(
        self.handle_private_text,
        F.text,
        F.chat.type == "private",
    )
```

## Command Arguments

Parse arguments from commands:

```python
class GreetController(AsyncController):
    def register(self, registry: Router) -> None:
        registry.message.register(
            self.handle_greet,
            Command(commands=["greet"]),
        )

    async def handle_greet(self, message: Message) -> None:
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

class MenuController(AsyncController):
    def register(self, registry: Router) -> None:
        registry.message.register(self.show_menu, Command(commands=["menu"]))
        registry.callback_query.register(self.handle_option_1, F.data == "option_1")
        registry.callback_query.register(self.handle_option_2, F.data == "option_2")

    async def show_menu(self, message: Message) -> None:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Option 1", callback_data="option_1"),
                InlineKeyboardButton(text="Option 2", callback_data="option_2"),
            ]
        ])
        await message.answer("Choose an option:", reply_markup=keyboard)

    async def handle_option_1(self, callback: CallbackQuery) -> None:
        await callback.answer("You chose option 1!")
        if callback.message:
            await callback.message.edit_text("Option 1 selected")

    async def handle_option_2(self, callback: CallbackQuery) -> None:
        await callback.answer("You chose option 2!")
        if callback.message:
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


class FormController(AsyncController):
    def register(self, registry: Router) -> None:
        registry.message.register(self.start_form, Command(commands=["form"]))
        registry.message.register(self.process_name, Form.name)
        registry.message.register(self.process_age, Form.age)

    async def start_form(self, message: Message, state: FSMContext) -> None:
        await state.set_state(Form.name)
        await message.answer("What's your name?")

    async def process_name(self, message: Message, state: FSMContext) -> None:
        await state.update_data(name=message.text)
        await state.set_state(Form.age)
        await message.answer("How old are you?")

    async def process_age(self, message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        name = data.get("name")
        age = message.text

        await state.clear()
        await message.answer(f"Hello {name}, you are {age} years old!")
```

## Exception Handling

Override `handle_exception()` for custom error handling:

```python
class CommandsController(AsyncController):
    async def handle_exception(self, exception: Exception) -> None:
        # Log the error
        import logging
        logging.exception("Error in bot handler", exc_info=exception)

        # Custom handling for specific exceptions
        if isinstance(exception, SomeCustomError):
            # Handle specific error
            return

        # Re-raise unhandled exceptions
        raise exception
```

## Dependency Injection

Controllers can have dependencies injected via the IoC container:

```python
from core.user.services import UserService

class UserController(AsyncController):
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
            await message.answer("Profile not found")
```

Register in IoC container:

```python
# src/ioc/container.py

def _register_bot(container: Container) -> None:
    container.register(UserController, scope=Scope.singleton)
```

## Organizing Controllers

Split controllers by feature:

```
delivery/bot/
├── controllers/
│   ├── __init__.py
│   ├── commands.py      # Basic commands (/start, /id)
│   ├── callbacks.py     # Callback query handlers
│   ├── admin.py         # Admin commands
│   └── forms.py         # Multi-step forms
├── factories.py
└── settings.py
```

Each controller is registered in the IoC container and injected into `DispatcherFactory`.

## Best Practices

### 1. Always Check for None

```python
async def handle_start(self, message: Message) -> None:
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
async def handle_data(self, message: Message) -> None:
    try:
        data = await fetch_data()
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
- [Controller Pattern](../concepts/controller-pattern.md) — Pattern explanation
- [Your First Bot Command](../tutorials/first-bot-command.md) — Tutorial
- [aiogram Documentation](https://docs.aiogram.dev/) — Official docs
