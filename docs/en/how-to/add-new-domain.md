# Add a New Domain

This guide walks you through adding a new business domain to your application. We will use "products" as an example domain.

## Prerequisites

- Understanding of the [Service Layer Architecture](../concepts/service-layer.md)
- Familiarity with the [Controller Pattern](../concepts/controller-pattern.md)

## Complete Checklist

### Step 1: Create the Domain Directory Structure

Create the domain directory in `src/core/`:

```bash
mkdir -p src/core/products
touch src/core/products/__init__.py
```

### Step 2: Create the Django App Configuration

Create `src/core/products/apps.py`:

```python
from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.products"
    label = "products"
```

### Step 3: Add to INSTALLED_APPS

Edit `src/core/configs/core.py` and add the new app to the installed apps list:

```python
class ApplicationSettings(BaseSettings):
    # ... existing fields ...

    @property
    def installed_apps(self) -> list[str]:
        return [
            # ... existing apps ...
            "core.products",
        ]
```

### Step 4: Create the Domain Model

Create `src/core/products/models.py`:

```python
from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Product(id={self.pk}, name={self.name})"
```

### Step 5: Create the Service with Domain Exceptions

Create `src/core/products/services.py`:

```python
from django.db import transaction

from core.products.models import Product


class ProductNotFoundError(Exception):
    """Raised when a product is not found."""


class ProductService:
    def get_product_by_id(self, product_id: int) -> Product:
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist as e:
            raise ProductNotFoundError(f"Product {product_id} not found") from e

    def list_products(self) -> list[Product]:
        return list(Product.objects.all())

    @transaction.atomic
    def create_product(
        self,
        name: str,
        description: str,
        price: float,
    ) -> Product:
        return Product.objects.create(
            name=name,
            description=description,
            price=price,
        )

    @transaction.atomic
    def update_product(
        self,
        product_id: int,
        name: str | None = None,
        description: str | None = None,
        price: float | None = None,
    ) -> Product:
        product = self.get_product_by_id(product_id)

        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if price is not None:
            product.price = price

        product.save()
        return product

    @transaction.atomic
    def delete_product(self, product_id: int) -> None:
        product = self.get_product_by_id(product_id)
        product.delete()
```

!!! warning "Service Layer Rule"
    Services are the **only** place where you should import and use Django models directly. Controllers must never import models.

### Step 6: Register the Service in IoC

Edit `src/ioc/registries/core.py`:

```python
from punq import Container, Scope

from core.products.services import ProductService
# ... other imports ...


def _register_services(container: Container) -> None:
    # ... existing registrations ...
    container.register(ProductService, scope=Scope.singleton)
```

### Step 7: Create the Controller

Create the controller directory and file:

```bash
mkdir -p src/delivery/http/products
touch src/delivery/http/products/__init__.py
```

Create `src/delivery/http/products/controllers.py`:

```python
from http import HTTPStatus
from typing import Any

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from ninja.throttling import AuthRateThrottle
from pydantic import BaseModel

from core.products.services import ProductNotFoundError, ProductService
from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import AuthenticatedHttpRequest, JWTAuth


class ProductSchema(BaseModel):
    id: int
    name: str
    description: str
    price: float


class CreateProductRequest(BaseModel):
    name: str
    description: str = ""
    price: float


class UpdateProductRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None


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
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )
        registry.add_api_operation(
            path="/v1/products/",
            methods=["POST"],
            view_func=self.create_product,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )
        registry.add_api_operation(
            path="/v1/products/{product_id}",
            methods=["GET"],
            view_func=self.get_product,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )
        registry.add_api_operation(
            path="/v1/products/{product_id}",
            methods=["PATCH"],
            view_func=self.update_product,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )
        registry.add_api_operation(
            path="/v1/products/{product_id}",
            methods=["DELETE"],
            view_func=self.delete_product,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )

    def list_products(
        self,
        request: AuthenticatedHttpRequest,
    ) -> list[ProductSchema]:
        products = self._product_service.list_products()
        return [
            ProductSchema.model_validate(p, from_attributes=True)
            for p in products
        ]

    def create_product(
        self,
        request: AuthenticatedHttpRequest,
        body: CreateProductRequest,
    ) -> ProductSchema:
        product = self._product_service.create_product(
            name=body.name,
            description=body.description,
            price=body.price,
        )
        return ProductSchema.model_validate(product, from_attributes=True)

    def get_product(
        self,
        request: AuthenticatedHttpRequest,
        product_id: int,
    ) -> ProductSchema:
        product = self._product_service.get_product_by_id(product_id)
        return ProductSchema.model_validate(product, from_attributes=True)

    def update_product(
        self,
        request: AuthenticatedHttpRequest,
        product_id: int,
        body: UpdateProductRequest,
    ) -> ProductSchema:
        product = self._product_service.update_product(
            product_id=product_id,
            name=body.name,
            description=body.description,
            price=body.price,
        )
        return ProductSchema.model_validate(product, from_attributes=True)

    def delete_product(
        self,
        request: AuthenticatedHttpRequest,
        product_id: int,
    ) -> None:
        self._product_service.delete_product(product_id)

    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, ProductNotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message=str(exception),
            ) from exception

        return super().handle_exception(exception)
```

### Step 8: Register the Controller in IoC

Edit `src/ioc/registries/delivery.py`:

```python
from punq import Container, Scope

from delivery.http.products.controllers import ProductController
# ... other imports ...


def _register_http_controllers(container: Container) -> None:
    # ... existing registrations ...
    container.register(ProductController, scope=Scope.singleton)
```

### Step 9: Update NinjaAPIFactory

Edit `src/delivery/http/factories.py` to include the new controller:

```python
from delivery.http.products.controllers import ProductController
# ... other imports ...


class NinjaAPIFactory:
    def __init__(
        self,
        settings: ApplicationSettings,
        health_controller: HealthController,
        user_token_controller: UserTokenController,
        user_controller: UserController,
        product_controller: ProductController,  # Add this
    ) -> None:
        self._settings = settings
        self._health_controller = health_controller
        self._user_token_controller = user_token_controller
        self._user_controller = user_controller
        self._product_controller = product_controller  # Add this

    def __call__(
        self,
        urls_namespace: str | None = None,
    ) -> NinjaAPI:
        # ... existing code ...

        # Add product router
        product_router = Router(tags=["products"])
        ninja_api.add_router("/", product_router)
        self._product_controller.register(registry=product_router)

        return ninja_api
```

### Step 10: Create and Run Migrations

```bash
# Create migrations
make makemigrations

# Apply migrations
make migrate
```

### Step 11: Create Tests

Create test directory and files:

```bash
mkdir -p tests/integration/http/products
touch tests/integration/http/products/__init__.py
```

Create `tests/integration/http/products/test_products.py`:

```python
from http import HTTPStatus

import pytest

from core.products.models import Product
from tests.integration.factories import TestClientFactory, TestUserFactory


@pytest.fixture
def product() -> Product:
    return Product.objects.create(
        name="Test Product",
        description="A test product",
        price=99.99,
    )


@pytest.mark.django_db(transaction=True)
def test_list_products(
    test_client_factory: TestClientFactory,
    user_factory: TestUserFactory,
    product: Product,
) -> None:
    user = user_factory()
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.get("/v1/products/")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == product.name


@pytest.mark.django_db(transaction=True)
def test_create_product(
    test_client_factory: TestClientFactory,
    user_factory: TestUserFactory,
) -> None:
    user = user_factory()
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.post(
        "/v1/products/",
        json={
            "name": "New Product",
            "description": "A new product",
            "price": 49.99,
        },
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["name"] == "New Product"


@pytest.mark.django_db(transaction=True)
def test_get_product_not_found(
    test_client_factory: TestClientFactory,
    user_factory: TestUserFactory,
) -> None:
    user = user_factory()
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.get("/v1/products/999")

    assert response.status_code == HTTPStatus.NOT_FOUND
```

### Step 12: Run Tests

```bash
make test
```

## Summary

You have now added a complete new domain with:

- [x] Django model in `core/products/models.py`
- [x] Service layer in `core/products/services.py`
- [x] Domain exceptions (`ProductNotFoundError`)
- [x] HTTP controller in `delivery/http/products/controllers.py`
- [x] IoC registrations for service and controller
- [x] API routes with authentication and rate limiting
- [x] Integration tests

The data flow follows the architecture:

```
HTTP Request -> Controller -> Service -> Model -> Database
```

Controllers never import models directly - they only interact with services.
