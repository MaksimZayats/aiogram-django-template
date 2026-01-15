# Secure Endpoints

This guide explains how to add authentication and rate limiting to your API endpoints.

## Authentication with JWTAuth

### Basic Setup

Inject `JWTAuth` into your controller and use it in `add_api_operation`:

```python
from ninja import Router
from ninja.throttling import AuthRateThrottle

from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import AuthenticatedHttpRequest, JWTAuth


class ProductController(Controller):
    def __init__(
        self,
        jwt_auth: JWTAuth,
        product_service: ProductService,
    ) -> None:
        self._jwt_auth = jwt_auth
        self._product_service = product_service

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/products/",
            methods=["GET"],
            view_func=self.list_products,
            auth=self._jwt_auth,  # Requires valid JWT
            throttle=AuthRateThrottle(rate="30/min"),
        )

    def list_products(
        self,
        request: AuthenticatedHttpRequest,  # Use typed request
    ) -> list[ProductSchema]:
        # Access authenticated user via request.user
        user = request.user
        return self._product_service.list_for_user(user.id)
```

### AuthenticatedHttpRequest

Use `AuthenticatedHttpRequest` instead of `HttpRequest` for authenticated endpoints:

```python
from infrastructure.django.auth import AuthenticatedHttpRequest


def get_current_user(
    self,
    request: AuthenticatedHttpRequest,
) -> UserSchema:
    # request.user is guaranteed to be authenticated
    return UserSchema.model_validate(request.user, from_attributes=True)
```

This typed request provides:

- `request.user` - The authenticated Django user
- `request.auth` - The authenticated user (same as `user`)
- `request.jwt_payload` - The decoded JWT payload dictionary

#### Using a Custom User Model

`AuthenticatedHttpRequest` is a generic class that defaults to `AbstractBaseUser`. If you have a custom user model, you can specify it as a type parameter for better type safety:

```python
from core.user.models import User
from infrastructure.django.auth import AuthenticatedHttpRequest


def get_current_user(
    self,
    request: AuthenticatedHttpRequest[User],
) -> UserSchema:
    # request.user is now typed as User, not AbstractBaseUser
    # IDE autocompletion and type checking work with your custom fields
    return UserSchema.model_validate(request.user, from_attributes=True)
```

## Rate Limiting

### Available Throttle Classes

| Class | Use Case |
|-------|----------|
| `AnonRateThrottle` | Unauthenticated endpoints (rate by IP) |
| `AuthRateThrottle` | Authenticated endpoints (rate by user) |

### Rate Format Strings

Rate limits are specified as `"count/period"`:

| Format | Meaning |
|--------|---------|
| `"5/min"` | 5 requests per minute |
| `"30/min"` | 30 requests per minute |
| `"100/hour"` | 100 requests per hour |
| `"1000/day"` | 1000 requests per day |

### Examples

#### Public Endpoint with IP-Based Rate Limiting

```python
from ninja.throttling import AnonRateThrottle


def register(self, registry: Router) -> None:
    registry.add_api_operation(
        path="/v1/users/",
        methods=["POST"],
        view_func=self.create_user,
        auth=None,  # Public endpoint
        throttle=AnonRateThrottle(rate="30/min"),
    )
```

#### Authenticated Endpoint with User-Based Rate Limiting

```python
from ninja.throttling import AuthRateThrottle


def register(self, registry: Router) -> None:
    registry.add_api_operation(
        path="/v1/users/me",
        methods=["GET"],
        view_func=self.get_current_user,
        auth=self._jwt_auth,
        throttle=AuthRateThrottle(rate="30/min"),
    )
```

#### Sensitive Endpoints with Strict Rate Limiting

For login, token refresh, and password reset endpoints:

```python
def register(self, registry: Router) -> None:
    # Login endpoint - strict rate limiting to prevent brute force
    registry.add_api_operation(
        path="/v1/users/me/token",
        methods=["POST"],
        view_func=self.issue_user_token,
        auth=None,
        throttle=AnonRateThrottle(rate="5/min"),  # Only 5 attempts per minute
    )

    # Token refresh - also rate limited
    registry.add_api_operation(
        path="/v1/users/me/token/refresh",
        methods=["POST"],
        view_func=self.refresh_user_token,
        auth=None,
        throttle=AnonRateThrottle(rate="5/min"),
    )

    # Token revocation - authenticated with rate limiting
    registry.add_api_operation(
        path="/v1/users/me/token/revoke",
        methods=["POST"],
        view_func=self.revoke_refresh_token,
        auth=self._jwt_auth,
        throttle=AuthRateThrottle(rate="5/min"),
    )
```

## Complete Secure Controller Example

```python
from http import HTTPStatus
from typing import Any

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from ninja.throttling import AnonRateThrottle, AuthRateThrottle
from pydantic import BaseModel

from core.orders.services import OrderNotFoundError, OrderService
from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import AuthenticatedHttpRequest, JWTAuth


class OrderSchema(BaseModel):
    id: int
    status: str
    total: float


class CreateOrderRequest(BaseModel):
    items: list[int]


class OrderController(Controller):
    def __init__(
        self,
        jwt_auth: JWTAuth,
        order_service: OrderService,
    ) -> None:
        self._jwt_auth = jwt_auth
        self._order_service = order_service

    def register(self, registry: Router) -> None:
        # List orders - authenticated, moderate rate limit
        registry.add_api_operation(
            path="/v1/orders/",
            methods=["GET"],
            view_func=self.list_orders,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )

        # Create order - authenticated, stricter rate limit
        registry.add_api_operation(
            path="/v1/orders/",
            methods=["POST"],
            view_func=self.create_order,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="10/min"),
        )

        # Get single order - authenticated
        registry.add_api_operation(
            path="/v1/orders/{order_id}",
            methods=["GET"],
            view_func=self.get_order,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )

    def list_orders(
        self,
        request: AuthenticatedHttpRequest,
    ) -> list[OrderSchema]:
        orders = self._order_service.list_for_user(request.user.id)
        return [OrderSchema.model_validate(o, from_attributes=True) for o in orders]

    def create_order(
        self,
        request: AuthenticatedHttpRequest,
        body: CreateOrderRequest,
    ) -> OrderSchema:
        order = self._order_service.create_order(
            user_id=request.user.id,
            item_ids=body.items,
        )
        return OrderSchema.model_validate(order, from_attributes=True)

    def get_order(
        self,
        request: AuthenticatedHttpRequest,
        order_id: int,
    ) -> OrderSchema:
        order = self._order_service.get_order_by_id(
            order_id=order_id,
            user_id=request.user.id,  # Ensure user owns the order
        )
        return OrderSchema.model_validate(order, from_attributes=True)

    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, OrderNotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message=str(exception),
            ) from exception

        return super().handle_exception(exception)
```

## Mixed Authentication Patterns

Some endpoints may need different auth levels for different methods:

```python
def register(self, registry: Router) -> None:
    # Public: anyone can view products
    registry.add_api_operation(
        path="/v1/products/",
        methods=["GET"],
        view_func=self.list_products,
        auth=None,
        throttle=AnonRateThrottle(rate="100/min"),
    )

    # Authenticated: only logged-in users can create
    registry.add_api_operation(
        path="/v1/products/",
        methods=["POST"],
        view_func=self.create_product,
        auth=self._jwt_auth,
        throttle=AuthRateThrottle(rate="10/min"),
    )
```

## Rate Limit Recommendations

| Endpoint Type | Recommended Rate |
|---------------|------------------|
| Login/Auth | `5/min` |
| Password reset | `3/min` |
| User registration | `30/min` |
| Read operations | `30-100/min` |
| Write operations | `10-30/min` |
| Expensive operations | `5-10/min` |

## Summary

1. Inject `JWTAuth` into controllers that need authentication
2. Use `auth=self._jwt_auth` in `add_api_operation` for protected endpoints
3. Use `AuthenticatedHttpRequest` type hint for authenticated handlers
4. Apply `AnonRateThrottle` for public endpoints (rate by IP)
5. Apply `AuthRateThrottle` for authenticated endpoints (rate by user)
6. Use stricter rate limits for sensitive operations (login, password reset)
7. Access user via `request.user` in authenticated handlers
