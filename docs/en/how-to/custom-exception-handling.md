# Custom Exception Handling

This guide shows how to map domain exceptions to HTTP responses.

## The Pattern

1. Define domain exceptions in services
2. Override `handle_exception()` in controllers
3. Convert domain exceptions to `HttpError`

## Step 1: Define Domain Exceptions

Create exceptions that inherit from `ApplicationError`:

```python
# src/core/order/services.py
from core.exceptions import ApplicationError


class OrderNotFoundError(ApplicationError):
    """Raised when order cannot be found."""

    def __init__(self, order_id: int) -> None:
        self.order_id = order_id
        super().__init__(f"Order {order_id} not found")


class OrderAlreadyPaidError(ApplicationError):
    """Raised when trying to pay an already paid order."""


class InsufficientStockError(ApplicationError):
    """Raised when product stock is insufficient."""

    def __init__(self, product_id: int, requested: int, available: int) -> None:
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for product {product_id}: "
            f"requested {requested}, available {available}"
        )
```

## Step 2: Override handle_exception()

In your controller, override `handle_exception()` to convert domain exceptions:

```python
# src/delivery/http/order/controllers.py
from http import HTTPStatus
from typing import Any

from ninja.errors import HttpError

from core.order.services import (
    InsufficientStockError,
    OrderAlreadyPaidError,
    OrderNotFoundError,
)
from infrastructure.delivery.controllers import Controller


class OrderController(Controller):
    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, OrderNotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message="Order not found",
            ) from exception

        if isinstance(exception, OrderAlreadyPaidError):
            raise HttpError(
                status_code=HTTPStatus.CONFLICT,
                message="Order has already been paid",
            ) from exception

        if isinstance(exception, InsufficientStockError):
            raise HttpError(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                message=f"Insufficient stock: only {exception.available} available",
            ) from exception

        # Let base class handle unknown exceptions
        return super().handle_exception(exception)
```

## HTTP Status Code Guide

| Domain Exception | HTTP Status | Description |
|-----------------|-------------|-------------|
| `NotFoundError` | 404 | Resource doesn't exist |
| `AccessDeniedError` | 403 | User lacks permission |
| `AlreadyExistsError` | 409 | Resource conflict |
| `ValidationError` | 422 | Invalid data |
| `InvalidStateError` | 409 | Invalid state transition |
| `ExternalServiceError` | 502 | Third-party failure |

## Including Error Details

For API clients that need structured error responses:

```python
from typing import Any

from ninja import NinjaAPI
from ninja.errors import HttpError
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class OrderController(Controller):
    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, InsufficientStockError):
            # Include structured details
            raise HttpError(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                message=ErrorResponse(
                    code="INSUFFICIENT_STOCK",
                    message="Insufficient stock",
                    details={
                        "product_id": exception.product_id,
                        "requested": exception.requested,
                        "available": exception.available,
                    },
                ).model_dump(),
            ) from exception

        return super().handle_exception(exception)
```

## Handling Multiple Exception Types

Group related exceptions:

```python
def handle_exception(self, exception: Exception) -> Any:
    # Not found errors -> 404
    if isinstance(exception, (OrderNotFoundError, ProductNotFoundError)):
        raise HttpError(HTTPStatus.NOT_FOUND, "Resource not found") from exception

    # Permission errors -> 403
    if isinstance(exception, (OrderAccessDeniedError, ProductAccessDeniedError)):
        raise HttpError(HTTPStatus.FORBIDDEN, "Access denied") from exception

    # Validation errors -> 422
    if isinstance(exception, (InvalidQuantityError, InvalidAddressError)):
        raise HttpError(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            str(exception),
        ) from exception

    return super().handle_exception(exception)
```

## Logging Exceptions

Add logging for debugging:

```python
import logging

logger = logging.getLogger(__name__)


class OrderController(Controller):
    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, OrderNotFoundError):
            logger.warning(
                "Order not found",
                extra={"order_id": exception.order_id},
            )
            raise HttpError(HTTPStatus.NOT_FOUND, "Order not found") from exception

        if isinstance(exception, InsufficientStockError):
            logger.warning(
                "Insufficient stock",
                extra={
                    "product_id": exception.product_id,
                    "requested": exception.requested,
                    "available": exception.available,
                },
            )
            raise HttpError(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Insufficient stock",
            ) from exception

        # Log unexpected exceptions as errors
        logger.exception("Unexpected error in OrderController")
        return super().handle_exception(exception)
```

## Testing Exception Handling

```python
# tests/integration/http/test_v1_orders.py
from http import HTTPStatus

import pytest

from tests.integration.factories import TestClientFactory


@pytest.mark.django_db(transaction=True)
def test_get_nonexistent_order_returns_404(
    test_client_factory: TestClientFactory,
    user,
) -> None:
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.get("/v1/orders/99999")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.django_db(transaction=True)
def test_access_other_users_order_returns_403(
    test_client_factory: TestClientFactory,
    user,
    other_user_order,
) -> None:
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.get(f"/v1/orders/{other_user_order.id}")

    assert response.status_code == HTTPStatus.FORBIDDEN
```

## Best Practices

### 1. Be Specific in Services, Generic in Responses

```python
# Service - specific exception
raise InsufficientStockError(
    product_id=product.id,
    requested=quantity,
    available=product.stock,
)

# Controller - generic message for clients
raise HttpError(
    HTTPStatus.UNPROCESSABLE_ENTITY,
    "Insufficient stock",  # Don't expose internal details
)
```

### 2. Always Use `from exception`

```python
# ✅ GOOD - Preserves stack trace
raise HttpError(HTTPStatus.NOT_FOUND, "Not found") from exception

# ❌ BAD - Loses original exception info
raise HttpError(HTTPStatus.NOT_FOUND, "Not found")
```

### 3. Don't Catch Too Broadly

```python
# ✅ GOOD - Specific handling
if isinstance(exception, OrderNotFoundError):
    raise HttpError(HTTPStatus.NOT_FOUND, "Order not found") from exception

# ❌ BAD - Catches everything
try:
    order = self._order_service.get_order(order_id)
except Exception:  # Too broad!
    raise HttpError(HTTPStatus.NOT_FOUND, "Order not found")
```

## Related

- [Service Layer](../concepts/service-layer.md) - Where exceptions are defined
- [Controller Pattern](../concepts/controller-pattern.md) - How `handle_exception()` works
