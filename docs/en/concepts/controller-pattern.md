# Controller Pattern

Controllers are the entry points for external requests. They handle HTTP requests, Celery tasks, and Telegram bot commands.

## Two Base Classes

The template provides two base controller classes:

| Class | Use Case | Methods |
|-------|----------|---------|
| `Controller` | HTTP API, Celery tasks | Sync methods |
| `AsyncController` | Telegram bot | Async methods |

## Controller Base Class

```python
# src/infrastructure/delivery/controllers.py
from abc import ABC, abstractmethod
from typing import Any


class Controller(ABC):
    @abstractmethod
    def register(self, registry: Any) -> None:
        """Register routes/tasks with the framework."""
        ...

    def handle_exception(self, exception: Exception) -> Any:
        """Override to handle exceptions."""
        raise exception
```

Key features:

- **Abstract `register()`** - Each controller defines how it integrates with its framework
- **Exception wrapping** - All public methods are auto-wrapped with exception handling
- **Override `handle_exception()`** - Custom error responses

## HTTP Controller

```python
# src/delivery/http/user/controllers.py
from http import HTTPStatus
from typing import Any

from ninja import Router
from ninja.errors import HttpError
from ninja.throttling import AuthRateThrottle

from core.user.services import UserService, UserNotFoundError
from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import AuthenticatedHttpRequest, JWTAuth


class UserController(Controller):
    def __init__(
        self,
        jwt_auth: JWTAuth,
        user_service: UserService,
    ) -> None:
        self._jwt_auth = jwt_auth
        self._user_service = user_service

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/users/me",
            methods=["GET"],
            view_func=self.get_current_user,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )

    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, UserNotFoundError):
            raise HttpError(HTTPStatus.NOT_FOUND, "User not found") from exception
        return super().handle_exception(exception)

    def get_current_user(
        self,
        request: AuthenticatedHttpRequest,
    ) -> UserSchema:
        return UserSchema.model_validate(request.user, from_attributes=True)
```

### Registration with Router

HTTP controllers register with a Django Ninja `Router`:

```python
def register(self, registry: Router) -> None:
    registry.add_api_operation(
        path="/v1/users/me",
        methods=["GET"],
        view_func=self.get_current_user,
        auth=self._jwt_auth,
        throttle=AuthRateThrottle(rate="30/min"),
    )
```

### Rate Limiting

Django Ninja provides built-in throttling:

```python
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

# Anonymous users - rate limit by IP
throttle=AnonRateThrottle(rate="10/min")

# Authenticated users - rate limit by user ID
throttle=AuthRateThrottle(rate="30/min")
```

Rate formats: `"30/min"`, `"5/hour"`, `"1000/day"`

## Celery Task Controller

```python
# src/delivery/tasks/tasks/ping.py
from typing import Literal, TypedDict

from celery import Celery

from delivery.tasks.registry import TaskName
from infrastructure.delivery.controllers import Controller


class PingResult(TypedDict):
    result: Literal["pong"]


class PingTaskController(Controller):
    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.PING)(self.ping)

    def ping(self) -> PingResult:
        return PingResult(result="pong")
```

### Task Registration

Celery controllers register tasks with the Celery app:

```python
def register(self, registry: Celery) -> None:
    registry.task(name=TaskName.PING)(self.ping)
```

### Typed Results

Use `TypedDict` for type-safe task results:

```python
class TodoCleanupResult(TypedDict):
    status: Literal["success"]
    deleted_count: int
```

## Async Controller (Telegram Bot)

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

    async def handle_start_command(self, message: Message) -> None:
        if message.from_user is None:
            return
        await message.answer("Hello! This is a bot.")
```

### Async Registration

Bot controllers register with an aiogram `Router`:

```python
def register(self, registry: Router) -> None:
    registry.message.register(
        self.handle_start_command,
        Command(commands=["start"]),
    )
```

## Exception Handling

The base classes auto-wrap public methods with exception handling:

```python
class Controller(ABC):
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        _wrap_methods(instance)  # Auto-wrap all methods
        return instance
```

This means exceptions are caught and passed to `handle_exception()`:

```python
class TodoController(Controller):
    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, TodoNotFoundError):
            raise HttpError(HTTPStatus.NOT_FOUND, "Todo not found") from exception
        if isinstance(exception, TodoAccessDeniedError):
            raise HttpError(HTTPStatus.FORBIDDEN, "Access denied") from exception
        return super().handle_exception(exception)

    def get_todo(self, request, todo_id: int) -> TodoSchema:
        # If TodoNotFoundError is raised, handle_exception() is called
        todo = self._todo_service.get_todo_by_id(todo_id, request.user)
        return TodoSchema.model_validate(todo, from_attributes=True)
```

## IoC Registration

Controllers are registered in `src/ioc/registries/delivery.py`:

```python
from punq import Container, Scope

from delivery.http.user.controllers import UserController
from delivery.http.todo.controllers import TodoController


def _register_http_controllers(container: Container) -> None:
    container.register(UserController, scope=Scope.singleton)
    container.register(TodoController, scope=Scope.singleton)
```

## Factory Integration

Factories inject controllers and call `register()`:

```python
# src/delivery/http/factories.py
class NinjaAPIFactory:
    def __init__(
        self,
        user_controller: UserController,
        todo_controller: TodoController,
    ) -> None:
        self._user_controller = user_controller
        self._todo_controller = todo_controller

    def __call__(self) -> NinjaAPI:
        ninja_api = NinjaAPI()

        user_router = Router(tags=["user"])
        ninja_api.add_router("/", user_router)
        self._user_controller.register(registry=user_router)

        todo_router = Router(tags=["todo"])
        ninja_api.add_router("/", todo_router)
        self._todo_controller.register(registry=todo_router)

        return ninja_api
```

## Best Practices

### 1. Keep Controllers Thin

```python
# ✅ GOOD - Controller delegates to service
def create_todo(self, request, body) -> TodoSchema:
    todo = self._todo_service.create_todo(
        user=request.user,
        title=body.title,
    )
    return TodoSchema.model_validate(todo, from_attributes=True)

# ❌ BAD - Business logic in controller
def create_todo(self, request, body) -> TodoSchema:
    if Todo.objects.filter(user=request.user, title=body.title).exists():
        raise HttpError(409, "Todo exists")
    todo = Todo.objects.create(user=request.user, title=body.title)
    return TodoSchema.model_validate(todo, from_attributes=True)
```

### 2. Use Domain Exceptions

```python
# Service raises domain exception
class TodoService:
    def get_todo_by_id(self, todo_id: int, user: User) -> Todo:
        try:
            todo = Todo.objects.get(id=todo_id)
        except Todo.DoesNotExist as e:
            raise TodoNotFoundError(todo_id) from e
        return todo

# Controller converts to HTTP error
class TodoController(Controller):
    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, TodoNotFoundError):
            raise HttpError(HTTPStatus.NOT_FOUND, "Todo not found") from exception
        return super().handle_exception(exception)
```

### 3. Co-locate Schemas

Keep Pydantic schemas in the same file as the controller:

```python
# src/delivery/http/todo/controllers.py
from pydantic import BaseModel

class CreateTodoRequestSchema(BaseModel):
    title: str
    description: str = ""

class TodoSchema(BaseModel):
    id: int
    title: str
    # ...

class TodoController(Controller):
    # ...
```

## Related Concepts

- [Service Layer](service-layer.md) - What controllers call
- [Factory Pattern](factory-pattern.md) - How controllers are registered
- [IoC Container](ioc-container.md) - How controllers are instantiated
