# Service Layer Architecture

The Service Layer pattern separates business logic from delivery mechanisms (HTTP controllers, bot handlers, Celery tasks). This ensures that controllers never access Django models directly.

## Architecture Principle

```
┌─────────────────────────────────────────┐
│         Delivery Layer                   │
│  (HTTP Controllers, Bot, Celery Tasks)  │
│                                          │
│  ✗ NO direct model imports              │
│  ✓ Only import and use services         │
└────────────────┬────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│         Service Layer                    │
│     (core/*/services.py)                │
│                                          │
│  ✓ Contains business logic              │
│  ✓ Performs ORM queries                 │
│  ✓ Raises domain exceptions             │
└────────────────┬────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│         Model Layer                      │
│     (core/*/models.py)                  │
│                                          │
│  ✓ Django ORM models                    │
│  ✓ Database schema                      │
└─────────────────────────────────────────┘
```

## The Golden Rule

**Controllers must NEVER import or use Django models directly. All database operations must go through services.**

### Correct Pattern

```python
# delivery/http/user/controllers.py
from core.user.services import UserService  # ✅ Import service

class UserController(Controller):
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    def get_user(self, request: HttpRequest, user_id: int) -> UserSchema:
        user = self._user_service.get_user_by_id(user_id)  # ✅ Use service
        return UserSchema.model_validate(user, from_attributes=True)
```

### Incorrect Pattern

```python
# delivery/http/user/controllers.py
from core.user.models import User  # ❌ NEVER import models in controllers

class UserController(Controller):
    def get_user(self, request: HttpRequest, user_id: int) -> UserSchema:
        user = User.objects.get(id=user_id)  # ❌ Direct ORM access
        return UserSchema.model_validate(user, from_attributes=True)
```

## Creating a Service

Services are placed in `core/<domain>/services.py`:

```python
# core/item/services.py
from django.db import transaction

from core.item.models import Item


class ItemNotFoundError(Exception):
    """Raised when an item is not found."""


class ItemService:
    def get_item_by_id(self, item_id: int) -> Item:
        try:
            return Item.objects.get(id=item_id)
        except Item.DoesNotExist as e:
            raise ItemNotFoundError(f"Item {item_id} not found") from e

    def list_items(self) -> list[Item]:
        return list(Item.objects.all())

    @transaction.atomic
    def create_item(self, name: str, description: str) -> Item:
        return Item.objects.create(
            name=name,
            description=description,
        )

    @transaction.atomic
    def delete_item(self, item_id: int) -> None:
        item = self.get_item_by_id(item_id)
        item.delete()
```

## Registering Services in IoC

Services must be registered in the IoC container at `src/ioc/registries/core.py`:

```python
from punq import Container, Scope

from core.item.services import ItemService


def register_core(container: Container) -> None:
    # Register services
    container.register(ItemService, scope=Scope.singleton)
```

## Using Services in Controllers

Inject services via constructor:

```python
# delivery/http/item/controllers.py
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
            auth=None,
        )
        registry.add_api_operation(
            path="/v1/items/{item_id}",
            methods=["GET"],
            view_func=self.get_item,
            auth=None,
        )
        registry.add_api_operation(
            path="/v1/items/",
            methods=["POST"],
            view_func=self.create_item,
            auth=self._auth,
        )

    def list_items(self, request: HttpRequest) -> list[ItemSchema]:
        items = self._item_service.list_items()
        return [
            ItemSchema.model_validate(item, from_attributes=True)
            for item in items
        ]

    def get_item(self, request: HttpRequest, item_id: int) -> ItemSchema:
        item = self._item_service.get_item_by_id(item_id)
        return ItemSchema.model_validate(item, from_attributes=True)

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

## Data Flow Example

Here's the complete data flow for a user creation request:

```
HTTP POST /v1/users/
    │
    ▼
UserController.create_user()
    │
    ├── Validates request body (Pydantic)
    │
    ▼
UserService.is_valid_password()
    │
    ├── Checks password strength
    │
    ▼
UserService.get_user_by_username_or_email()
    │
    ├── User.objects.filter() - checks for duplicates
    │
    ▼
UserService.create_user()
    │
    ├── User.objects.create_user() - creates in database
    │
    ▼
UserController.create_user() (continues)
    │
    ├── Converts User model to UserSchema (Pydantic)
    │
    ▼
HTTP Response 201 Created
```

## Benefits

### 1. Testability

Services can be mocked in tests:

```python
def test_get_item(container: Container, test_client_factory: TestClientFactory) -> None:
    mock_service = MagicMock(spec=ItemService)
    mock_service.get_item_by_id.return_value = Item(id=1, name="Test", description="Desc")

    container.register(ItemService, instance=mock_service)

    client = test_client_factory()
    response = client.get("/v1/items/1")

    assert response.status_code == 200
    mock_service.get_item_by_id.assert_called_once_with(1)
```

### 2. Reusability

Services can be shared across delivery mechanisms:

```python
# HTTP Controller
class ItemController(Controller):
    def __init__(self, item_service: ItemService) -> None:
        self._item_service = item_service

# Celery Task Controller
class ItemSyncTaskController(Controller):
    def __init__(self, item_service: ItemService) -> None:
        self._item_service = item_service

# Bot Controller
class ItemBotController(AsyncController):
    def __init__(self, item_service: ItemService) -> None:
        self._item_service = item_service
```

### 3. Separation of Concerns

- **Controllers**: Handle HTTP/Bot/Task specifics (routing, auth, response formatting)
- **Services**: Contain business logic and data access
- **Models**: Define database schema

### 4. Domain Exceptions

Services raise domain-specific exceptions that controllers translate to appropriate responses:

```python
# Service raises domain exception
class UserAlreadyExistsError(Exception):
    pass

class UserService:
    def create_user(self, username: str, email: str) -> User:
        if User.objects.filter(username=username).exists():
            raise UserAlreadyExistsError(f"User {username} already exists")

# Controller translates to HTTP response
class UserController(Controller):
    def handle_exception(self, exception: Exception) -> NoReturn:
        if isinstance(exception, UserAlreadyExistsError):
            raise HttpError(status_code=409, message=str(exception))
        raise exception
```

## Acceptable Exceptions

Direct model imports are acceptable in these specific cases:

1. **Django Admin** (`admin.py`) - Required for admin registration
2. **Migrations** - Auto-generated by Django
3. **Factory setup** - For registering admin site
4. **Tests** - For creating test data with factories

## Related Topics

- [Controller Pattern](controller-pattern.md) - How controllers use services
- [IoC Container](ioc-container.md) - How services are registered and resolved
- [Your First API Endpoint](../tutorials/first-api-endpoint.md) - Tutorial using services
