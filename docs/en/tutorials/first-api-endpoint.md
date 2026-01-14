# Your First API Endpoint

Create a new HTTP endpoint following the service layer architecture. This tutorial demonstrates the correct pattern: Controller → Service → Model.

## Goal

Build a `/v1/items/` endpoint that:

- Returns a list of items (GET)
- Creates a new item (POST, authenticated)

## Step 1: Create the Model

Create `src/core/item/models.py`:

```python
from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name
```

Create an empty `src/core/item/__init__.py` file.

Run migrations:

```bash
make makemigrations
make migrate
```

## Step 2: Create the Service

Create `src/core/item/services.py`:

```python
from django.db import transaction

from core.item.models import Item


class ItemNotFoundError(Exception):
    """Raised when an item is not found."""


class ItemService:
    """Service for managing items. All database operations go through this service."""

    def get_item_by_id(self, item_id: int) -> Item:
        """Get an item by ID or raise ItemNotFoundError."""
        try:
            return Item.objects.get(id=item_id)
        except Item.DoesNotExist as e:
            raise ItemNotFoundError(f"Item {item_id} not found") from e

    def list_items(self) -> list[Item]:
        """Return all items."""
        return list(Item.objects.all())

    @transaction.atomic
    def create_item(self, name: str, description: str) -> Item:
        """Create a new item."""
        return Item.objects.create(
            name=name,
            description=description,
        )
```

Key points:

- Service contains all business logic and ORM access
- Domain-specific exceptions (`ItemNotFoundError`) are raised for error cases
- Use `@transaction.atomic` for write operations

## Step 3: Create the Controller

Create `src/delivery/http/item/controllers.py`:

```python
from http import HTTPStatus
from typing import NoReturn

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from core.item.services import ItemNotFoundError, ItemService
from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import JWTAuth


class ItemSchema(BaseModel):
    id: int
    name: str
    description: str


class CreateItemSchema(BaseModel):
    name: str
    description: str


class ItemController(Controller):
    def __init__(
        self,
        item_service: ItemService,
        auth: JWTAuth,
    ) -> None:
        self._item_service = item_service
        self._auth = auth

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/items/",
            methods=["GET"],
            view_func=self.list_items,
            auth=None,  # Public endpoint
        )

        registry.add_api_operation(
            path="/v1/items/",
            methods=["POST"],
            view_func=self.create_item,
            auth=self._auth,  # Requires authentication
        )

    def list_items(self, request: HttpRequest) -> list[ItemSchema]:
        items = self._item_service.list_items()
        return [
            ItemSchema.model_validate(item, from_attributes=True)
            for item in items
        ]

    def create_item(
        self,
        request: HttpRequest,
        body: CreateItemSchema,
    ) -> ItemSchema:
        item = self._item_service.create_item(
            name=body.name,
            description=body.description,
        )
        return ItemSchema.model_validate(item, from_attributes=True)

    def handle_exception(self, exception: Exception) -> NoReturn:
        if isinstance(exception, ItemNotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message="Item not found",
            ) from exception

        raise exception
```

Create an empty `src/delivery/http/item/__init__.py` file.

Key points:

- Controller imports **service**, not model
- Dependencies (`ItemService`, `JWTAuth`) are injected via `__init__`
- `handle_exception()` translates domain exceptions to HTTP errors
- Pydantic schemas for request/response validation

## Step 4: Register Service in IoC Container

Edit `src/ioc/registries/core.py`:

```python
from core.item.services import ItemService  # Add import


def register_core(container: Container) -> None:
    # ... existing registrations ...

    # Add item service
    container.register(ItemService, scope=Scope.singleton)
```

## Step 5: Register Controller in IoC Container

Edit `src/ioc/registries/delivery.py`:

```python
from delivery.http.item.controllers import ItemController  # Add import


def _register_http(container: Container) -> None:
    # ... existing registrations ...

    container.register(ItemController, scope=Scope.singleton)
```

## Step 6: Register Routes in Factory

Edit `src/delivery/http/factories.py`:

```python
from delivery.http.item.controllers import ItemController  # Add import


class NinjaAPIFactory:
    def __init__(
        self,
        settings: ApplicationSettings,
        health_controller: HealthController,
        user_token_controller: UserTokenController,
        user_controller: UserController,
        item_controller: ItemController,  # Add parameter
    ) -> None:
        self._settings = settings
        self._health_controller = health_controller
        self._user_token_controller = user_token_controller
        self._user_controller = user_controller
        self._item_controller = item_controller  # Store it

    def __call__(
        self,
        urls_namespace: str | None = None,
    ) -> NinjaAPI:
        # ... existing code ...

        # Add item router
        item_router = Router(tags=["item"])
        ninja_api.add_router("/", item_router)
        self._item_controller.register(registry=item_router)

        return ninja_api
```

## Step 7: Test It

### Start the Server

```bash
make dev
```

### List Items (Public)

```bash
curl http://localhost:8000/api/v1/items/
```

Response:

```json
[]
```

### Create Item (Authenticated)

First, get a token:

```bash
# Create a user (if needed)
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser", "first_name": "Test", "last_name": "User", "password": "SecurePass123!"}'

# Get access token
curl -X POST http://localhost:8000/api/v1/users/me/token \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "SecurePass123!"}'
```

Then create an item:

```bash
curl -X POST http://localhost:8000/api/v1/items/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "New Item", "description": "Created via API"}'
```

### View API Docs

Open `http://localhost:8000/api/docs` to see your new endpoint in the interactive documentation.

## Architecture Summary

The complete data flow:

```
HTTP Request
    │
    ▼
ItemController (delivery layer)
    │
    ├── Validates request (Pydantic schemas)
    │
    ▼
ItemService (core layer)
    │
    ├── Contains business logic
    ├── Performs ORM queries
    │
    ▼
Item Model (database)
    │
    ▼
ItemController (continues)
    │
    ├── Converts model to response schema
    │
    ▼
HTTP Response
```

## Common Mistakes to Avoid

### 1. Direct Model Import in Controller

```python
# ❌ Wrong
from core.item.models import Item

class ItemController(Controller):
    def list_items(self, request: HttpRequest) -> list[ItemSchema]:
        items = Item.objects.all()  # Direct ORM access
```

### 2. Business Logic in Controller

```python
# ❌ Wrong - validation logic belongs in service
class ItemController(Controller):
    def create_item(self, request: HttpRequest, body: CreateItemSchema) -> ItemSchema:
        if len(body.name) < 3:  # Business rule in controller
            raise HttpError(400, "Name too short")
```

### 3. Forgetting to Register Service

If you see `punq.MissingDependencyError`, ensure the service is registered in the IoC container.

## Next Steps

- [Service Layer Architecture](../concepts/service-layer.md) - Deep dive into the pattern
- [Controllers](../http/controllers.md) - Controller patterns and best practices
- [JWT Authentication](../http/jwt-authentication.md) - Understand the auth system
- [Testing HTTP APIs](../testing/http-tests.md) - Write tests for your endpoint
