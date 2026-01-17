# Secure Endpoints

This guide explains how to add authentication to your API endpoints.

## Authentication with JWTAuthFactory

### Basic Setup

Inject `JWTAuthFactory` into your controller and use it with `Depends()` in `add_api_route`:

```python
from dataclasses import dataclass, field

from fastapi import APIRouter, Depends

from infrastructure.delivery.controllers import Controller
from infrastructure.fastapi.auth import AuthenticatedRequest, JWTAuth, JWTAuthFactory


@dataclass
class ProductController(Controller):
    _jwt_auth_factory: JWTAuthFactory
    _product_service: ProductService
    _jwt_auth: JWTAuth = field(init=False)

    def __post_init__(self) -> None:
        self._jwt_auth = self._jwt_auth_factory()

    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/v1/products/",
            methods=["GET"],
            endpoint=self.list_products,
            dependencies=[Depends(self._jwt_auth)],  # Requires valid JWT
            response_model=list[ProductSchema],
        )

    def list_products(
        self,
        request: AuthenticatedRequest,  # Use typed request
    ) -> list[ProductSchema]:
        # Access authenticated user via request.state.user
        user = request.state.user
        return self._product_service.list_for_user(user_id=user.id)
```

### AuthenticatedRequest

Use `AuthenticatedRequest` instead of `Request` for authenticated endpoints:

```python
from infrastructure.fastapi.auth import AuthenticatedRequest


def get_current_user(
    self,
    request: AuthenticatedRequest,
) -> UserSchema:
    # request.state.user contains the authenticated user object
    return UserSchema.model_validate(request.state.user, from_attributes=True)
```

This typed request provides:

- `request.state.user` - The authenticated user object

## Permission-Based Access Control

### Using JWTAuthFactory with Permissions

For endpoints requiring specific permissions (staff or superuser), use `JWTAuthFactory` with permission parameters:

```python
from dataclasses import dataclass, field

from fastapi import APIRouter, Depends

from infrastructure.delivery.controllers import Controller
from infrastructure.fastapi.auth import AuthenticatedRequest, JWTAuth, JWTAuthFactory


@dataclass
class AdminController(Controller):
    _jwt_auth_factory: JWTAuthFactory
    _admin_service: AdminService
    _staff_auth: JWTAuth = field(init=False)
    _superuser_auth: JWTAuth = field(init=False)

    def __post_init__(self) -> None:
        self._staff_auth = self._jwt_auth_factory(require_staff=True)
        self._superuser_auth = self._jwt_auth_factory(require_superuser=True)

    def register(self, registry: APIRouter) -> None:
        # Only staff can view reports
        registry.add_api_route(
            path="/v1/admin/reports",
            methods=["GET"],
            endpoint=self.list_reports,
            dependencies=[Depends(self._staff_auth)],
        )

        # Only superusers can delete users
        registry.add_api_route(
            path="/v1/admin/users/{user_id}",
            methods=["DELETE"],
            endpoint=self.delete_user,
            dependencies=[Depends(self._superuser_auth)],
        )
```

### Permission Options

| Parameter | Type | Description |
|-----------|------|-------------|
| `require_staff` | `bool = False` | If `True`, requires `user.is_staff` to be `True` |
| `require_superuser` | `bool = False` | If `True`, requires `user.is_superuser` to be `True` |

### Error Responses

| Scenario | Status Code | Message |
|----------|-------------|---------|
| Missing/invalid token | 401 Unauthorized | Various auth errors |
| User not staff (when required) | 403 Forbidden | "Staff access required" |
| User not superuser (when required) | 403 Forbidden | "Superuser access required" |

### Combining Permissions

Require both staff AND superuser:

```python
self._strict_auth = self._jwt_auth_factory(require_staff=True, require_superuser=True)
```

## Complete Secure Controller Example

```python
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.orders.services import OrderNotFoundError, OrderService
from infrastructure.delivery.controllers import Controller
from infrastructure.fastapi.auth import AuthenticatedRequest, JWTAuth, JWTAuthFactory


class OrderSchema(BaseModel):
    id: int
    status: str
    total: float


class CreateOrderRequest(BaseModel):
    items: list[int]


@dataclass
class OrderController(Controller):
    _jwt_auth_factory: JWTAuthFactory
    _order_service: OrderService
    _jwt_auth: JWTAuth = field(init=False)

    def __post_init__(self) -> None:
        self._jwt_auth = self._jwt_auth_factory()

    def register(self, registry: APIRouter) -> None:
        # List orders - authenticated
        registry.add_api_route(
            path="/v1/orders/",
            methods=["GET"],
            endpoint=self.list_orders,
            dependencies=[Depends(self._jwt_auth)],
            response_model=list[OrderSchema],
        )

        # Create order - authenticated
        registry.add_api_route(
            path="/v1/orders/",
            methods=["POST"],
            endpoint=self.create_order,
            dependencies=[Depends(self._jwt_auth)],
            response_model=OrderSchema,
        )

        # Get single order - authenticated
        registry.add_api_route(
            path="/v1/orders/{order_id}",
            methods=["GET"],
            endpoint=self.get_order,
            dependencies=[Depends(self._jwt_auth)],
            response_model=OrderSchema,
        )

    def list_orders(
        self,
        request: AuthenticatedRequest,
    ) -> list[OrderSchema]:
        orders = self._order_service.list_for_user(user_id=request.state.user.id)
        return [OrderSchema.model_validate(o, from_attributes=True) for o in orders]

    def create_order(
        self,
        request: AuthenticatedRequest,
        body: CreateOrderRequest,
    ) -> OrderSchema:
        order = self._order_service.create_order(
            user_id=request.state.user.id,
            item_ids=body.items,
        )
        return OrderSchema.model_validate(order, from_attributes=True)

    def get_order(
        self,
        request: AuthenticatedRequest,
        order_id: int,
    ) -> OrderSchema:
        order = self._order_service.get_order_by_id(
            order_id=order_id,
            user_id=request.state.user.id,  # Ensure user owns the order
        )
        return OrderSchema.model_validate(order, from_attributes=True)

    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, OrderNotFoundError):
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=str(exception),
            ) from exception

        return super().handle_exception(exception)
```

## Mixed Authentication Patterns

Some endpoints may need different auth levels for different methods:

```python
def register(self, registry: APIRouter) -> None:
    # Public: anyone can view products
    registry.add_api_route(
        path="/v1/products/",
        methods=["GET"],
        endpoint=self.list_products,
    )

    # Authenticated: only logged-in users can create
    registry.add_api_route(
        path="/v1/products/",
        methods=["POST"],
        endpoint=self.create_product,
        dependencies=[Depends(self._jwt_auth)],
    )
```

## Summary

1. Inject `JWTAuthFactory` into controllers that need authentication
2. Call `jwt_auth_factory()` to get a basic auth instance, or use `jwt_auth_factory(require_staff=True)` / `jwt_auth_factory(require_superuser=True)` for permission-based auth
3. Use `dependencies=[Depends(self._jwt_auth)]` in `add_api_route` for protected endpoints
4. Use `AuthenticatedRequest` type hint for authenticated handlers
5. Access user via `request.state.user` in authenticated handlers
