# Your First API Endpoint

Create a new HTTP controller and register it with the IoC container.

## Goal

Build a `/v1/items/` endpoint that:

- Returns a list of items (GET)
- Creates a new item (POST, authenticated)

## Step 1: Create the Controller

Create a new file `src/delivery/http/item/controllers.py`:

```python
from http import HTTPStatus
from typing import NoReturn

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import JWTAuth


class ItemSchema(BaseModel):
    id: int
    name: str
    description: str


class CreateItemSchema(BaseModel):
    name: str
    description: str


# In-memory storage for demo purposes
_items: list[ItemSchema] = [
    ItemSchema(id=1, name="Item 1", description="First item"),
    ItemSchema(id=2, name="Item 2", description="Second item"),
]


class ItemController(Controller):
    def __init__(self, auth: JWTAuth) -> None:
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
        return _items

    def create_item(
        self,
        request: HttpRequest,
        body: CreateItemSchema,
    ) -> ItemSchema:
        new_item = ItemSchema(
            id=len(_items) + 1,
            name=body.name,
            description=body.description,
        )
        _items.append(new_item)
        return new_item
```

Key points:

- Extend `Controller` base class
- Inject dependencies via `__init__` (here: `JWTAuth`)
- Implement `register()` to define routes
- Use Pydantic models for request/response schemas

## Step 2: Create the Module Init

Create `src/delivery/http/item/__init__.py`:

```python
from delivery.http.item.controllers import ItemController

__all__ = ["ItemController"]
```

## Step 3: Register in IoC Container

Edit `src/ioc/container.py`:

```python
from delivery.http.item.controllers import ItemController  # Add import

def _register_controllers(container: Container) -> None:
    container.register(HealthController, scope=Scope.singleton)
    container.register(UserController, scope=Scope.singleton)
    container.register(UserTokenController, scope=Scope.singleton)
    container.register(ItemController, scope=Scope.singleton)  # Add this
```

## Step 4: Register Routes in Factory

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

## Step 5: Test It

### Start the Server

```bash
make dev
```

### List Items (Public)

```bash
curl http://localhost:8000/v1/items/
```

Response:

```json
[
  {"id": 1, "name": "Item 1", "description": "First item"},
  {"id": 2, "name": "Item 2", "description": "Second item"}
]
```

### Create Item (Authenticated)

First, get a token:

```bash
# Create a user (if needed)
curl -X POST http://localhost:8000/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser", "first_name": "Test", "last_name": "User", "password": "SecurePass123!"}'

# Get access token
curl -X POST http://localhost:8000/v1/users/me/token \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "SecurePass123!"}'
```

Then create an item:

```bash
curl -X POST http://localhost:8000/v1/items/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "New Item", "description": "Created via API"}'
```

### View API Docs

Open `http://localhost:8000/docs` to see your new endpoint in the interactive documentation.

## Adding Error Handling

Override `handle_exception()` for custom error responses:

```python
class ItemController(Controller):
    # ... existing code ...

    def handle_exception(self, exception: Exception) -> NoReturn:
        if isinstance(exception, ItemNotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message="Item not found",
            ) from exception

        # Re-raise unhandled exceptions
        raise exception
```

## Next Steps

- [Controllers](../http/controllers.md) — Deep dive into the controller pattern
- [JWT Authentication](../http/jwt-authentication.md) — Understand the auth system
- [Testing HTTP APIs](../testing/http-tests.md) — Write tests for your endpoint
