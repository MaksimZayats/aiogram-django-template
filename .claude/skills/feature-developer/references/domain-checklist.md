# Complete Domain Checklist

This reference provides the complete, detailed checklist for adding a new domain to the application. Use "products" as an example domain name.

## Contents

- [Phase 1: Core Layer Setup](#phase-1-core-layer-setup)
  - [Step 1: Create Domain Directory](#step-1-create-domain-directory)
  - [Step 2: Create Django App Configuration](#step-2-create-django-app-configuration)
  - [Step 3: Register in Installed Apps](#step-3-register-in-installed-apps)
  - [Step 4: Create the Domain Model](#step-4-create-the-domain-model)
  - [Step 5: Create Service with Domain Exceptions](#step-5-create-service-with-domain-exceptions)
  - [Step 6: Register Service in IoC](#step-6-register-service-in-ioc)
- [Phase 2: Delivery Layer Setup](#phase-2-delivery-layer-setup)
  - [Step 7: Create Controller Directory](#step-7-create-controller-directory)
  - [Step 8: Create Controller with Schemas](#step-8-create-controller-with-schemas)
  - [Step 9: Register Controller in IoC](#step-9-register-controller-in-ioc)
  - [Step 10: Update NinjaAPIFactory](#step-10-update-ninjaapifactory)
- [Phase 3: Finalization](#phase-3-finalization)
  - [Step 11: Create and Run Migrations](#step-11-create-and-run-migrations)
  - [Step 12: Create Tests](#step-12-create-tests)
- [Verification Commands](#verification-commands)
- [Summary Checklist](#summary-checklist)

## Phase 1: Core Layer Setup

### Step 1: Create Domain Directory

```bash
mkdir -p src/core/products
touch src/core/products/__init__.py
```

### Step 2: Create Django App Configuration

Create `src/core/products/apps.py`:

```python
from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.products"
    label = "products"
```

### Step 3: Register in Installed Apps

Edit `src/core/configs/core.py`:

```python
class ApplicationSettings(BaseSettings):
    installed_apps: tuple[str, ...] = (
        # ... existing apps
        "core.products.apps.ProductsConfig",  # Add this line
    )
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

### Step 5: Create Service with Domain Exceptions

Create `src/core/products/services.py`:

```python
from django.db import transaction

from core.products.models import Product


class ProductNotFoundError(Exception):
    """Raised when a product is not found."""


class ProductService:
    def get_product_by_id(self, product_id: int) -> Product:
        """Retrieve a product by ID.

        Raises:
            ProductNotFoundError: If the product does not exist.
        """
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist as e:
            raise ProductNotFoundError(f"Product {product_id} not found") from e

    def list_products(self) -> list[Product]:
        """Return all products."""
        return list(Product.objects.all())

    @transaction.atomic
    def create_product(
        self,
        name: str,
        description: str,
        price: float,
    ) -> Product:
        """Create a new product."""
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
        """Update an existing product.

        Raises:
            ProductNotFoundError: If the product does not exist.
        """
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
        """Delete a product.

        Raises:
            ProductNotFoundError: If the product does not exist.
        """
        product = self.get_product_by_id(product_id)
        product.delete()
```

### Step 6: Register Service in IoC

Edit `src/ioc/registries/core.py`:

```python
from punq import Container, Scope

from core.products.services import ProductService


def _register_services(container: Container) -> None:
    # ... existing registrations
    container.register(ProductService, scope=Scope.singleton)
```

## Phase 2: Delivery Layer Setup

### Step 7: Create Controller Directory

```bash
mkdir -p src/delivery/http/products
touch src/delivery/http/products/__init__.py
```

### Step 8: Create Controller with Schemas

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

### Step 9: Register Controller in IoC

Edit `src/ioc/registries/delivery.py`:

```python
from punq import Container, Scope

from delivery.http.products.controllers import ProductController


def _register_http_controllers(container: Container) -> None:
    # ... existing registrations
    container.register(ProductController, scope=Scope.singleton)
```

### Step 10: Update NinjaAPIFactory

Edit `src/delivery/http/factories.py`:

```python
from delivery.http.products.controllers import ProductController


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
        # ... existing code

        # Add product router
        product_router = Router(tags=["products"])
        ninja_api.add_router("/", product_router)
        self._product_controller.register(registry=product_router)

        return ninja_api
```

## Phase 3: Finalization

### Step 11: Create and Run Migrations

```bash
make makemigrations
make migrate
```

### Step 12: Create Tests

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

## Verification Commands

After completing all steps:

```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test

# Start dev server
make dev
```

## Summary Checklist

- [ ] `src/core/<domain>/__init__.py` created
- [ ] `src/core/<domain>/apps.py` created with AppConfig
- [ ] `src/core/configs/core.py` updated with new app
- [ ] `src/core/<domain>/models.py` created
- [ ] `src/core/<domain>/services.py` created with exceptions
- [ ] `src/ioc/registries/core.py` updated with service registration
- [ ] `src/delivery/http/<domain>/__init__.py` created
- [ ] `src/delivery/http/<domain>/controllers.py` created
- [ ] `src/ioc/registries/delivery.py` updated with controller registration
- [ ] `src/delivery/http/factories.py` updated with new controller
- [ ] Migrations created and applied
- [ ] Tests written and passing
