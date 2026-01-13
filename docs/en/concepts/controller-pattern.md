# Controller Pattern

The Controller pattern provides a consistent interface for handling requests across HTTP, Telegram bot, and Celery task contexts.

## Base Controller

The abstract base class is defined in `src/infrastructure/delivery/controllers.py`:

```python
from abc import ABC, abstractmethod
from typing import Any, NoReturn


class Controller(ABC):
    def __new__(cls, *_args: Any, **_kwargs: Any) -> Self:
        self = super().__new__(cls)
        _wrap_methods(self)
        return self

    @abstractmethod
    def register(self, registry: Any) -> None: ...

    def handle_exception(self, exception: Exception) -> NoReturn:
        raise exception
```

## Key Features

### 1. Automatic Exception Wrapping

When a controller is instantiated, all public methods are wrapped with exception handling:

```python
def _wrap_methods(controller: Controller) -> None:
    for attr_name in dir(controller):
        attr = getattr(controller, attr_name)
        if (
            callable(attr)
            and not attr_name.startswith("_")
            and attr_name not in ("register_routes", "handle_exception")
        ):
            setattr(
                controller,
                attr_name,
                _wrap_route(attr, controller=controller),
            )
```

Every public method is wrapped to catch exceptions and route them to `handle_exception()`.

### 2. Custom Exception Handling

Override `handle_exception()` to convert domain exceptions to appropriate responses:

```python
class UserTokenController(Controller):
    def handle_exception(self, exception: Exception) -> NoReturn:
        if isinstance(exception, InvalidRefreshTokenError):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Invalid refresh token",
            ) from exception

        if isinstance(exception, ExpiredRefreshTokenError):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Refresh token expired or revoked",
            ) from exception

        # Re-raise unhandled exceptions
        raise exception
```

### 3. Registry-Based Route Registration

The `register()` method connects controller methods to their respective frameworks:

**HTTP (Django-Ninja Router):**

```python
class UserController(Controller):
    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/users/",
            methods=["POST"],
            view_func=self.create_user,
            auth=None,
        )

        registry.add_api_operation(
            path="/v1/users/me",
            methods=["GET"],
            view_func=self.get_current_user,
            auth=self._auth,
        )
```

**Celery:**

```python
class PingTaskController(Controller):
    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.PING)(self.ping)
```

## HTTP Controllers

HTTP controllers receive Django-Ninja `Router` as their registry:

```python
from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel

from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import JWTAuth


class UserSchema(BaseModel):
    id: int
    username: str
    email: str


class UserController(Controller):
    def __init__(self, auth: JWTAuth) -> None:
        self._auth = auth

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/users/me",
            methods=["GET"],
            view_func=self.get_current_user,
            auth=self._auth,
        )

    def get_current_user(self, request: HttpRequest) -> UserSchema:
        return UserSchema.model_validate(request.user, from_attributes=True)
```

Key points:

- Use `add_api_operation()` for explicit route registration
- Pass `auth` parameter for authentication requirements
- Use Pydantic models for request/response schemas

## Celery Task Controllers

Task controllers receive `Celery` app as their registry:

```python
from typing import TypedDict

from celery import Celery

from delivery.tasks.registry import TaskName
from infrastructure.delivery.controllers import Controller


class PingResult(TypedDict):
    result: str


class PingTaskController(Controller):
    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.PING)(self.ping)

    def ping(self) -> PingResult:
        return PingResult(result="pong")
```

Key points:

- Use `registry.task()` to register as Celery task
- Task name should be defined in `TaskName` enum
- Return typed dict for type-safe results

## Dependency Injection

Controllers declare dependencies in `__init__`:

```python
class UserTokenController(Controller):
    def __init__(
        self,
        jwt_service: JWTService,
        refresh_token_service: RefreshSessionService,
        jwt_auth: JWTAuth,
    ) -> None:
        self._jwt_service = jwt_service
        self._refresh_token_service = refresh_token_service
        self._jwt_auth = jwt_auth
```

The IoC container resolves these dependencies automatically when the controller is created.

## Testing Controllers

Controllers are easily testable because dependencies are injectable:

```python
def test_user_controller():
    # Mock dependencies
    mock_auth = MagicMock(spec=JWTAuth)

    # Create controller with mocks
    controller = UserController(auth=mock_auth)

    # Test methods directly
    # ...
```

See [Mocking IoC Dependencies](../testing/mocking-ioc.md) for integration testing patterns.

## Best Practices

### 1. Single Responsibility

Each controller should handle one resource or feature area:

```python
# Good: Focused on user tokens
class UserTokenController(Controller): ...

# Good: Focused on user CRUD
class UserController(Controller): ...

# Avoid: Mixed responsibilities
class UserAndTokenController(Controller): ...
```

### 2. Explicit Error Handling

Handle known exceptions explicitly:

```python
def handle_exception(self, exception: Exception) -> NoReturn:
    if isinstance(exception, InvalidRefreshTokenError):
        raise HttpError(status_code=401, message="Invalid token")

    # Always re-raise unknown exceptions
    raise exception
```

### 3. Type-Safe Schemas

Use Pydantic models for all request/response schemas:

```python
class CreateUserSchema(BaseModel):
    email: EmailStr
    username: Annotated[str, Len(max_length=150)]
    password: Annotated[str, Len(max_length=128)]
```

## Related Topics

- [HTTP Controllers](../http/controllers.md) — HTTP-specific patterns
- [Task Controllers](../celery/task-controllers.md) — Celery-specific patterns
- [IoC Container](ioc-container.md) — Dependency resolution
