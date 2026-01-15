# Custom Exception Handling

This guide explains how to handle domain exceptions in controllers and map them to appropriate HTTP status codes.

## How Exception Handling Works

Controllers extend the `Controller` base class, which automatically wraps all public methods with exception handling. When an exception occurs, the `handle_exception()` method is called.

```python
class Controller(ABC):
    @abstractmethod
    def register(self, registry: Any) -> None: ...

    def handle_exception(self, exception: Exception) -> Any:
        raise exception  # Default: re-raise the exception
```

By default, exceptions are re-raised. Override `handle_exception()` to customize error responses.

## Basic Pattern

### Step 1: Define Domain Exceptions

Domain exceptions belong in your service module:

```python
# core/orders/services.py

class OrderNotFoundError(Exception):
    """Raised when an order is not found."""


class OrderAlreadyShippedError(Exception):
    """Raised when attempting to modify a shipped order."""


class InsufficientInventoryError(Exception):
    """Raised when there is not enough inventory."""
```

### Step 2: Override handle_exception() in Controller

```python
# delivery/http/orders/controllers.py
from http import HTTPStatus
from typing import Any

from ninja.errors import HttpError

from core.orders.services import (
    InsufficientInventoryError,
    OrderAlreadyShippedError,
    OrderNotFoundError,
    OrderService,
)
from infrastructure.delivery.controllers import Controller


class OrderController(Controller):
    def __init__(self, order_service: OrderService) -> None:
        self._order_service = order_service

    def register(self, registry: Router) -> None:
        # ... register routes ...

    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, OrderNotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message=str(exception),
            ) from exception

        if isinstance(exception, OrderAlreadyShippedError):
            raise HttpError(
                status_code=HTTPStatus.CONFLICT,
                message="Cannot modify a shipped order",
            ) from exception

        if isinstance(exception, InsufficientInventoryError):
            raise HttpError(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                message=str(exception),
            ) from exception

        # Fall back to default behavior for unhandled exceptions
        return super().handle_exception(exception)
```

## Real-World Example: UserTokenController

Here is how the template handles refresh token exceptions:

```python
# delivery/http/user/controllers.py

from http import HTTPStatus
from typing import Any

from ninja.errors import HttpError

from infrastructure.django.refresh_sessions.services import (
    ExpiredRefreshTokenError,
    InvalidRefreshTokenError,
    RefreshTokenError,
)
from infrastructure.delivery.controllers import Controller


class UserTokenController(Controller):
    def __init__(
        self,
        jwt_auth_factory: JWTAuthFactory,
        jwt_service: JWTService,
        refresh_token_service: RefreshSessionService,
        user_service: UserService,
    ) -> None:
        self._jwt_auth = jwt_auth_factory()
        self._jwt_service = jwt_service
        self._refresh_token_service = refresh_token_service
        self._user_service = user_service

    def register(self, registry: Router) -> None:
        # ... route registration ...

    def handle_exception(self, exception: Exception) -> Any:
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

        if isinstance(exception, RefreshTokenError):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Refresh token error",
            ) from exception

        return super().handle_exception(exception)
```

## Exception Chaining

!!! important "Always Chain Exceptions"
    Use `from exception` when raising `HttpError` to preserve the exception chain for debugging and logging.

```python
# Correct: preserves exception chain
raise HttpError(
    status_code=HTTPStatus.NOT_FOUND,
    message="Order not found",
) from exception

# Incorrect: loses original exception context
raise HttpError(
    status_code=HTTPStatus.NOT_FOUND,
    message="Order not found",
)
```

## Common HTTP Status Codes

| Status Code | Use Case |
|-------------|----------|
| `400 BAD_REQUEST` | Invalid input, validation errors |
| `401 UNAUTHORIZED` | Authentication required or failed |
| `403 FORBIDDEN` | Authenticated but not authorized |
| `404 NOT_FOUND` | Resource does not exist |
| `409 CONFLICT` | Resource state conflict (e.g., duplicate) |
| `422 UNPROCESSABLE_ENTITY` | Valid syntax but semantic errors |
| `429 TOO_MANY_REQUESTS` | Rate limit exceeded |

## Exception Hierarchy Pattern

For complex domains, create an exception hierarchy:

```python
# core/payments/services.py

class PaymentError(Exception):
    """Base exception for payment errors."""


class PaymentNotFoundError(PaymentError):
    """Payment does not exist."""


class PaymentDeclinedError(PaymentError):
    """Payment was declined by the processor."""


class PaymentAlreadyProcessedError(PaymentError):
    """Payment has already been processed."""
```

Then handle the base class as a fallback:

```python
def handle_exception(self, exception: Exception) -> Any:
    if isinstance(exception, PaymentNotFoundError):
        raise HttpError(
            status_code=HTTPStatus.NOT_FOUND,
            message=str(exception),
        ) from exception

    if isinstance(exception, PaymentDeclinedError):
        raise HttpError(
            status_code=HTTPStatus.PAYMENT_REQUIRED,
            message="Payment was declined",
        ) from exception

    if isinstance(exception, PaymentAlreadyProcessedError):
        raise HttpError(
            status_code=HTTPStatus.CONFLICT,
            message="Payment has already been processed",
        ) from exception

    # Catch any other PaymentError
    if isinstance(exception, PaymentError):
        raise HttpError(
            status_code=HTTPStatus.BAD_REQUEST,
            message="Payment error occurred",
        ) from exception

    return super().handle_exception(exception)
```

## Async Controllers

For Telegram bot handlers, use `AsyncController` with an async `handle_exception()`:

```python
from infrastructure.delivery.controllers import AsyncController


class BotController(AsyncController):
    def register(self, registry: Router) -> None:
        # ... register handlers ...

    async def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, SomeDomainError):
            # Handle async-specific error responses
            return await self._send_error_message(exception)

        return await super().handle_exception(exception)
```

## Summary

1. Define domain exceptions in your service module
2. Override `handle_exception()` in your controller
3. Use `isinstance()` to check exception types
4. Map exceptions to appropriate HTTP status codes using `HttpError`
5. Always chain exceptions with `from exception`
6. Call `super().handle_exception(exception)` for unhandled cases
