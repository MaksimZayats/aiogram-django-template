# Step 3: HTTP API & Admin

In this step, you will create the HTTP API endpoints for the Todo feature using Django Ninja and set up the Django admin interface.

## Files Overview

| Action | File Path |
|--------|-----------|
| Create | `src/delivery/http/todo/__init__.py` |
| Create | `src/delivery/http/todo/controllers.py` |
| Create | `src/delivery/http/todo/admin.py` |
| Modify | `src/ioc/registries/delivery.py` |
| Modify | `src/delivery/http/factories.py` |

## Step 3.1: Create the Directory Structure

```bash
mkdir -p src/delivery/http/todo
touch src/delivery/http/todo/__init__.py
```

## Step 3.2: Create Pydantic Schemas and Controller

Create the controller with request/response schemas in `src/delivery/http/todo/controllers.py`:

```python title="src/delivery/http/todo/controllers.py"
from datetime import datetime
from http import HTTPStatus
from typing import Any

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from ninja.throttling import AuthRateThrottle
from pydantic import BaseModel

from core.todo.services import (
    TodoAccessDeniedError,
    TodoNotFoundError,
    TodoService,
)
from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import AuthenticatedHttpRequest, JWTAuth


# ============================================================================
# Request Schemas
# ============================================================================


class CreateTodoRequestSchema(BaseModel):
    """Schema for creating a new todo item."""

    title: str
    description: str = ""


# ============================================================================
# Response Schemas
# ============================================================================


class TodoSchema(BaseModel):
    """Schema for a single todo item."""

    id: int
    title: str
    description: str
    is_completed: bool
    created_at: datetime
    completed_at: datetime | None


class TodoListSchema(BaseModel):
    """Schema for a list of todo items."""

    items: list[TodoSchema]
    count: int


# ============================================================================
# Controller
# ============================================================================


class TodoController(Controller):
    """HTTP controller for todo operations.

    All endpoints require JWT authentication. The controller uses the
    TodoService for all data operations and never accesses models directly.
    """

    def __init__(
        self,
        jwt_auth: JWTAuth,
        todo_service: TodoService,
    ) -> None:
        self._jwt_auth = jwt_auth
        self._todo_service = todo_service

    def register(self, registry: Router) -> None:
        """Register all todo endpoints with the router."""
        registry.add_api_operation(
            path="/v1/todos/",
            methods=["GET"],
            view_func=self.list_todos,
            response=TodoListSchema,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="60/min"),
        )

        registry.add_api_operation(
            path="/v1/todos/",
            methods=["POST"],
            view_func=self.create_todo,
            response=TodoSchema,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )

        registry.add_api_operation(
            path="/v1/todos/{todo_id}",
            methods=["GET"],
            view_func=self.get_todo,
            response=TodoSchema,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="60/min"),
        )

        registry.add_api_operation(
            path="/v1/todos/{todo_id}/complete",
            methods=["POST"],
            view_func=self.complete_todo,
            response=TodoSchema,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )

        registry.add_api_operation(
            path="/v1/todos/{todo_id}",
            methods=["DELETE"],
            view_func=self.delete_todo,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )

    def list_todos(
        self,
        request: AuthenticatedHttpRequest,
    ) -> TodoListSchema:
        """List all todos for the authenticated user."""
        todos = self._todo_service.list_todos_for_user(user=request.user)
        return TodoListSchema(
            items=[
                TodoSchema.model_validate(todo, from_attributes=True)
                for todo in todos
            ],
            count=len(todos),
        )

    def create_todo(
        self,
        request: AuthenticatedHttpRequest,
        body: CreateTodoRequestSchema,
    ) -> TodoSchema:
        """Create a new todo for the authenticated user."""
        todo = self._todo_service.create_todo(
            title=body.title,
            description=body.description,
            user=request.user,
        )
        return TodoSchema.model_validate(todo, from_attributes=True)

    def get_todo(
        self,
        request: AuthenticatedHttpRequest,
        todo_id: int,
    ) -> TodoSchema:
        """Get a specific todo by ID."""
        todo = self._todo_service.get_todo_by_id(
            todo_id=todo_id,
            user=request.user,
        )
        return TodoSchema.model_validate(todo, from_attributes=True)

    def complete_todo(
        self,
        request: AuthenticatedHttpRequest,
        todo_id: int,
    ) -> TodoSchema:
        """Mark a todo as completed."""
        todo = self._todo_service.complete_todo(
            todo_id=todo_id,
            user=request.user,
        )
        return TodoSchema.model_validate(todo, from_attributes=True)

    def delete_todo(
        self,
        request: AuthenticatedHttpRequest,
        todo_id: int,
    ) -> None:
        """Delete a todo."""
        self._todo_service.delete_todo(
            todo_id=todo_id,
            user=request.user,
        )

    def handle_exception(self, exception: Exception) -> Any:
        """Convert domain exceptions to HTTP errors."""
        if isinstance(exception, TodoNotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message=f"Todo with id {exception.todo_id} not found",
            ) from exception

        if isinstance(exception, TodoAccessDeniedError):
            raise HttpError(
                status_code=HTTPStatus.FORBIDDEN,
                message="You do not have permission to access this todo",
            ) from exception

        return super().handle_exception(exception)
```

### Controller Anatomy

Let's break down the key parts of the controller:

#### Constructor Injection

```python
def __init__(
    self,
    jwt_auth: JWTAuth,
    todo_service: TodoService,
) -> None:
    self._jwt_auth = jwt_auth
    self._todo_service = todo_service
```

The container automatically injects these dependencies when creating the controller.

#### Route Registration

```python
def register(self, registry: Router) -> None:
    registry.add_api_operation(
        path="/v1/todos/",
        methods=["GET"],
        view_func=self.list_todos,
        response=TodoListSchema,
        auth=self._jwt_auth,
        throttle=AuthRateThrottle(rate="60/min"),
    )
```

Each endpoint specifies:

- **path**: The URL path
- **methods**: HTTP methods (GET, POST, etc.)
- **view_func**: The handler method
- **response**: The Pydantic schema for the response (for API documentation)
- **auth**: Authentication backend (JWT in this case)
- **throttle**: Rate limiting configuration

#### Request Types

```python
def list_todos(
    self,
    request: AuthenticatedHttpRequest,  # User is available via request.user
) -> TodoListSchema:
```

Use `AuthenticatedHttpRequest` for endpoints that require authentication. This provides type-safe access to `request.user`.

#### Exception Handling

```python
def handle_exception(self, exception: Exception) -> Any:
    if isinstance(exception, TodoNotFoundError):
        raise HttpError(
            status_code=HTTPStatus.NOT_FOUND,
            message=f"Todo with id {exception.todo_id} not found",
        ) from exception
    # ...
    return super().handle_exception(exception)
```

The `handle_exception` method catches domain exceptions and converts them to HTTP errors. Always call `super().handle_exception(exception)` for unhandled exceptions.

!!! info "Automatic Exception Wrapping"
    The `Controller` base class automatically wraps all handler methods with exception handling. You don't need to add try/except blocks in your handlers.

## Step 3.3: Create the Admin Interface

Create the Django admin configuration in `src/delivery/http/todo/admin.py`:

```python title="src/delivery/http/todo/admin.py"
from django.contrib import admin

from core.todo.models import Todo


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin[Todo]):
    """Admin interface for Todo model."""

    list_display = (
        "id",
        "title",
        "user",
        "is_completed",
        "created_at",
        "completed_at",
    )

    list_filter = (
        "is_completed",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "user__username",
    )

    readonly_fields = (
        "created_at",
        "completed_at",
    )

    raw_id_fields = ("user",)
```

!!! note "Admin and Models"
    Django admin is one of the acceptable places to import models directly, as documented in `CLAUDE.md`. The admin requires direct model access for its functionality.

## Step 3.4: Register the Controller in IoC

Add the controller registration in `src/ioc/registries/delivery.py`.

First, add the import:

```python title="src/ioc/registries/delivery.py" hl_lines="4"
from delivery.http.factories import AdminSiteFactory, NinjaAPIFactory, URLPatternsFactory
from delivery.http.health.controllers import HealthController
from delivery.http.user.controllers import UserController, UserTokenController
from delivery.http.todo.controllers import TodoController  # Add this import
```

Then add the registration in `_register_http_controllers`:

```python title="src/ioc/registries/delivery.py" hl_lines="5"
def _register_http_controllers(container: Container) -> None:
    container.register(HealthController, scope=Scope.singleton)
    container.register(UserController, scope=Scope.singleton)
    container.register(UserTokenController, scope=Scope.singleton)
    container.register(TodoController, scope=Scope.singleton)  # Add this line
```

## Step 3.5: Update the API Factory

Modify `src/delivery/http/factories.py` to include the todo controller and router.

First, add the import:

```python title="src/delivery/http/factories.py" hl_lines="4"
from delivery.http.health.controllers import HealthController
from delivery.http.user.controllers import UserController, UserTokenController
from delivery.http.todo.controllers import TodoController  # Add this import
```

Then update the `NinjaAPIFactory` class:

```python title="src/delivery/http/factories.py" hl_lines="8 14 39-42"
class NinjaAPIFactory:
    def __init__(
        self,
        settings: ApplicationSettings,
        health_controller: HealthController,
        user_token_controller: UserTokenController,
        user_controller: UserController,
        todo_controller: TodoController,  # Add this parameter
    ) -> None:
        self._settings = settings
        self._health_controller = health_controller
        self._user_token_controller = user_token_controller
        self._user_controller = user_controller
        self._todo_controller = todo_controller  # Store the controller

    def __call__(
        self,
        urls_namespace: str | None = None,
    ) -> NinjaAPI:
        if self._settings.environment == Environment.PRODUCTION:
            docs_decorator = staff_member_required
        else:
            docs_decorator = None

        ninja_api = NinjaAPI(
            urls_namespace=urls_namespace,
            docs_decorator=docs_decorator,
        )

        health_router = Router(tags=["health"])
        ninja_api.add_router("/", health_router)
        self._health_controller.register(registry=health_router)

        user_router = Router(tags=["user"])
        ninja_api.add_router("/", user_router)
        self._user_controller.register(registry=user_router)
        self._user_token_controller.register(registry=user_router)

        # Add todo router
        todo_router = Router(tags=["todo"])
        ninja_api.add_router("/", todo_router)
        self._todo_controller.register(registry=todo_router)

        return ninja_api
```

Finally, update the `AdminSiteFactory` to import the todo admin:

```python title="src/delivery/http/factories.py" hl_lines="4"
class AdminSiteFactory:
    def __call__(self) -> AdminSite:
        from delivery.http.user import admin as _user_admin  # noqa: F401, PLC0415
        from delivery.http.todo import admin as _todo_admin  # noqa: F401, PLC0415

        return default_site
```

## Step 3.6: Test the API

Start the development server:

```bash
make dev
```

### API Documentation

Visit http://localhost:8000/api/docs to see the Swagger UI with your new endpoints:

- `GET /api/v1/todos/` - List all todos
- `POST /api/v1/todos/` - Create a new todo
- `GET /api/v1/todos/{todo_id}` - Get a specific todo
- `POST /api/v1/todos/{todo_id}/complete` - Mark a todo as complete
- `DELETE /api/v1/todos/{todo_id}` - Delete a todo

### Test with curl

First, create a user and get a token:

```bash
# Create a user
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "SecurePass123!"
  }'

# Get an access token
curl -X POST http://localhost:8000/api/v1/users/me/token \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "SecurePass123!"}'
```

Save the `access_token` from the response, then test the todo endpoints:

```bash
# Set your token
TOKEN="your_access_token_here"

# Create a todo
curl -X POST http://localhost:8000/api/v1/todos/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "Learn Django Ninja", "description": "Complete the tutorial"}'

# List todos
curl -X GET http://localhost:8000/api/v1/todos/ \
  -H "Authorization: Bearer $TOKEN"

# Complete a todo (replace 1 with actual todo ID)
curl -X POST http://localhost:8000/api/v1/todos/1/complete \
  -H "Authorization: Bearer $TOKEN"
```

### Django Admin

Visit http://localhost:8000/admin/ to manage todos through the admin interface. You'll need to create a superuser first:

```bash
python src/manage.py createsuperuser
```

## Rate Limiting

The controller uses Django Ninja's built-in rate limiting:

```python
throttle=AuthRateThrottle(rate="60/min")
```

| Throttle Class | Use Case |
|----------------|----------|
| `AuthRateThrottle` | Authenticated endpoints (per-user limits) |
| `AnonRateThrottle` | Public endpoints (per-IP limits) |

Rate limits are specified in `{count}/{period}` format:

- `60/min` - 60 requests per minute
- `1000/day` - 1000 requests per day
- `5/second` - 5 requests per second

## What's Next

You have created a complete HTTP API for the Todo feature:

- [x] Pydantic schemas for request/response validation
- [x] Controller with CRUD endpoints
- [x] JWT authentication on all endpoints
- [x] Rate limiting
- [x] Exception handling
- [x] Django admin interface
- [x] IoC registration

In the next step, you will create a Celery task to clean up old completed todos.

[Continue to Step 4: Celery Tasks](04-celery-tasks.md){ .md-button .md-button--primary }

---

!!! abstract "See Also"
    - [Controller Pattern](../concepts/controller-pattern.md) - Deep dive into the controller pattern
