# HTTP Controllers

HTTP controllers handle REST API requests using Django-Ninja routers.

## Controller Structure

```python
from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel

from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import JWTAuth


class ItemSchema(BaseModel):
    id: int
    name: str


class CreateItemSchema(BaseModel):
    name: str


class ItemController(Controller):
    def __init__(self, auth: JWTAuth) -> None:
        self._auth = auth

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/items/",
            methods=["GET"],
            view_func=self.list_items,
            auth=None,
        )

        registry.add_api_operation(
            path="/v1/items/",
            methods=["POST"],
            view_func=self.create_item,
            auth=self._auth,
        )

    def list_items(self, request: HttpRequest) -> list[ItemSchema]:
        return [ItemSchema(id=1, name="Item 1")]

    def create_item(
        self,
        request: HttpRequest,
        body: CreateItemSchema,
    ) -> ItemSchema:
        return ItemSchema(id=2, name=body.name)
```

## Route Registration

Use `add_api_operation()` for explicit route configuration:

```python
registry.add_api_operation(
    path="/v1/users/me",           # URL path
    methods=["GET"],               # HTTP methods
    view_func=self.get_user,       # Handler method
    auth=self._auth,               # Authentication (or None)
    tags=["user"],                 # OpenAPI tags (optional)
    summary="Get current user",    # OpenAPI summary (optional)
)
```

### Path Parameters

```python
registry.add_api_operation(
    path="/v1/items/{item_id}",
    methods=["GET"],
    view_func=self.get_item,
    auth=None,
)

def get_item(self, request: HttpRequest, item_id: int) -> ItemSchema:
    # item_id is automatically parsed from URL
    return ItemSchema(id=item_id, name="Item")
```

### Query Parameters

```python
def list_items(
    self,
    request: HttpRequest,
    page: int = 1,
    limit: int = 10,
) -> list[ItemSchema]:
    # ?page=2&limit=20
    return items[page * limit : (page + 1) * limit]
```

## Request Body

Use Pydantic models for request validation:

```python
from pydantic import BaseModel, EmailStr, Field
from annotated_types import Len
from typing import Annotated


class CreateUserSchema(BaseModel):
    email: EmailStr
    username: Annotated[str, Len(min_length=3, max_length=150)]
    password: Annotated[str, Len(min_length=8, max_length=128)]
    bio: str | None = None


def create_user(
    self,
    request: HttpRequest,
    body: CreateUserSchema,
) -> UserSchema:
    # body is validated automatically
    user = User.objects.create_user(
        username=body.username,
        email=str(body.email),
        password=body.password,
    )
    return UserSchema.model_validate(user, from_attributes=True)
```

## Response Schemas

### Single Object

```python
def get_item(self, request: HttpRequest, item_id: int) -> ItemSchema:
    return ItemSchema(id=item_id, name="Item")
```

### List of Objects

```python
def list_items(self, request: HttpRequest) -> list[ItemSchema]:
    return [ItemSchema(id=1, name="Item 1")]
```

### No Content

```python
def delete_item(self, request: HttpRequest, item_id: int) -> None:
    Item.objects.filter(id=item_id).delete()
    # Returns 200 with no body
```

### Custom Status Code

```python
from ninja import Router
from http import HTTPStatus


registry.add_api_operation(
    path="/v1/items/",
    methods=["POST"],
    view_func=self.create_item,
    response={HTTPStatus.CREATED: ItemSchema},
)
```

## Authentication

### Public Endpoint

```python
registry.add_api_operation(
    path="/v1/items/",
    methods=["GET"],
    view_func=self.list_items,
    auth=None,  # No authentication required
)
```

### Protected Endpoint

```python
registry.add_api_operation(
    path="/v1/items/",
    methods=["POST"],
    view_func=self.create_item,
    auth=self._auth,  # JWT authentication required
)
```

### Accessing Current User

```python
def get_current_user(self, request: HttpRequest) -> UserSchema:
    # request.user is set by JWTAuth
    return UserSchema.model_validate(request.user, from_attributes=True)
```

## Factory Integration

Controllers are registered in `NinjaAPIFactory`:

```python
class NinjaAPIFactory:
    def __init__(
        self,
        settings: ApplicationSettings,
        health_controller: HealthController,
        user_controller: UserController,
        item_controller: ItemController,  # Add new controller
    ) -> None:
        # ...
        self._item_controller = item_controller

    def __call__(self, urls_namespace: str | None = None) -> NinjaAPI:
        ninja_api = NinjaAPI(urls_namespace=urls_namespace)

        # Register item routes
        item_router = Router(tags=["item"])
        ninja_api.add_router("/", item_router)
        self._item_controller.register(registry=item_router)

        return ninja_api
```

## IoC Registration

Register controller in container:

```python
# src/ioc/container.py

def _register_controllers(container: Container) -> None:
    container.register(HealthController, scope=Scope.singleton)
    container.register(UserController, scope=Scope.singleton)
    container.register(ItemController, scope=Scope.singleton)  # Add
```

## Complete Example

```python
# src/delivery/http/item/controllers.py

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
    description: str | None = None


class CreateItemSchema(BaseModel):
    name: str
    description: str | None = None


class ItemNotFoundError(Exception):
    pass


class ItemController(Controller):
    def __init__(self, auth: JWTAuth) -> None:
        self._auth = auth
        self._items: dict[int, ItemSchema] = {}
        self._counter = 0

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/items/",
            methods=["GET"],
            view_func=self.list_items,
            auth=None,
        )

        registry.add_api_operation(
            path="/v1/items/",
            methods=["POST"],
            view_func=self.create_item,
            auth=self._auth,
        )

        registry.add_api_operation(
            path="/v1/items/{item_id}",
            methods=["GET"],
            view_func=self.get_item,
            auth=None,
        )

        registry.add_api_operation(
            path="/v1/items/{item_id}",
            methods=["DELETE"],
            view_func=self.delete_item,
            auth=self._auth,
        )

    def list_items(self, request: HttpRequest) -> list[ItemSchema]:
        return list(self._items.values())

    def create_item(
        self,
        request: HttpRequest,
        body: CreateItemSchema,
    ) -> ItemSchema:
        self._counter += 1
        item = ItemSchema(
            id=self._counter,
            name=body.name,
            description=body.description,
        )
        self._items[item.id] = item
        return item

    def get_item(self, request: HttpRequest, item_id: int) -> ItemSchema:
        if item_id not in self._items:
            raise ItemNotFoundError()
        return self._items[item_id]

    def delete_item(self, request: HttpRequest, item_id: int) -> None:
        if item_id not in self._items:
            raise ItemNotFoundError()
        del self._items[item_id]

    def handle_exception(self, exception: Exception) -> NoReturn:
        if isinstance(exception, ItemNotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message="Item not found",
            ) from exception
        raise exception
```

## Related Topics

- [Controller Pattern](../concepts/controller-pattern.md) — Base controller class
- [JWT Authentication](jwt-authentication.md) — Authentication details
- [Error Handling](error-handling.md) — Exception handling
- [HTTP API Tests](../testing/http-tests.md) — Testing controllers
