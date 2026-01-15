# Step 3: HTTP API & Admin

In this step, you'll create REST API endpoints for managing todos and a Django admin panel.

> **See also:** [Controller Pattern concept](../concepts/controller-pattern.md)

## Files to Create/Modify

| Action | File Path |
|--------|-----------|
| Create | `src/delivery/http/todo/__init__.py` |
| Create | `src/delivery/http/todo/controllers.py` |
| Create | `src/delivery/http/todo/admin.py` |
| Modify | `src/ioc/registries/delivery.py` |
| Modify | `src/delivery/http/factories.py` |

## 1. Create Pydantic Schemas

First, create the request/response schemas. In this template, schemas are co-located with controllers:

```python
# src/delivery/http/todo/__init__.py
```

```python
# src/delivery/http/todo/controllers.py
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


# Request/Response Schemas
class CreateTodoRequestSchema(BaseModel):
    title: str
    description: str = ""


class TodoSchema(BaseModel):
    id: int
    title: str
    description: str
    is_completed: bool
    created_at: str
    completed_at: str | None


class TodoListSchema(BaseModel):
    items: list[TodoSchema]


# Controller
class TodoController(Controller):
    def __init__(
        self,
        jwt_auth: JWTAuth,
        todo_service: TodoService,
    ) -> None:
        self._jwt_auth = jwt_auth
        self._todo_service = todo_service

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/todos/",
            methods=["GET"],
            view_func=self.list_todos,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )
        registry.add_api_operation(
            path="/v1/todos/",
            methods=["POST"],
            view_func=self.create_todo,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )
        registry.add_api_operation(
            path="/v1/todos/{todo_id}",
            methods=["GET"],
            view_func=self.get_todo,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )
        registry.add_api_operation(
            path="/v1/todos/{todo_id}/complete",
            methods=["POST"],
            view_func=self.complete_todo,
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

    def handle_exception(self, exception: Exception) -> Any:
        """Convert domain exceptions to HTTP errors."""
        if isinstance(exception, TodoNotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message="Todo not found",
            ) from exception
        if isinstance(exception, TodoAccessDeniedError):
            raise HttpError(
                status_code=HTTPStatus.FORBIDDEN,
                message="Access denied",
            ) from exception
        return super().handle_exception(exception)

    def list_todos(self, request: AuthenticatedHttpRequest) -> TodoListSchema:
        """List all todos for the authenticated user."""
        todos = self._todo_service.list_todos(user=request.user)
        return TodoListSchema(
            items=[
                TodoSchema(
                    id=todo.id,
                    title=todo.title,
                    description=todo.description,
                    is_completed=todo.is_completed,
                    created_at=todo.created_at.isoformat(),
                    completed_at=(
                        todo.completed_at.isoformat()
                        if todo.completed_at
                        else None
                    ),
                )
                for todo in todos
            ]
        )

    def create_todo(
        self,
        request: AuthenticatedHttpRequest,
        request_body: CreateTodoRequestSchema,
    ) -> TodoSchema:
        """Create a new todo."""
        todo = self._todo_service.create_todo(
            user=request.user,
            title=request_body.title,
            description=request_body.description,
        )
        return TodoSchema(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            is_completed=todo.is_completed,
            created_at=todo.created_at.isoformat(),
            completed_at=None,
        )

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
        return TodoSchema(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            is_completed=todo.is_completed,
            created_at=todo.created_at.isoformat(),
            completed_at=(
                todo.completed_at.isoformat()
                if todo.completed_at
                else None
            ),
        )

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
        return TodoSchema(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            is_completed=todo.is_completed,
            created_at=todo.created_at.isoformat(),
            completed_at=(
                todo.completed_at.isoformat()
                if todo.completed_at
                else None
            ),
        )

    def delete_todo(
        self,
        request: AuthenticatedHttpRequest,
        todo_id: int,
    ) -> dict[str, str]:
        """Delete a todo."""
        self._todo_service.delete_todo(
            todo_id=todo_id,
            user=request.user,
        )
        return {"status": "deleted"}
```

**Key patterns:**

- **Constructor injection** - `TodoService` and `JWTAuth` are injected
- **Exception handling** - `handle_exception()` converts domain exceptions to HTTP errors
- **Rate limiting** - `AuthRateThrottle(rate="30/min")` limits requests per user
- **Type safety** - `AuthenticatedHttpRequest` ensures user is available

## 2. Create Django Admin

Admin classes can import models directly (one of the few exceptions to the golden rule):

```python
# src/delivery/http/todo/admin.py
from django.contrib import admin

from core.todo.models import Todo


class TodoAdmin(admin.ModelAdmin[Todo]):
    list_display = (
        "id",
        "title",
        "user",
        "is_completed",
        "created_at",
        "completed_at",
    )
    list_filter = ("is_completed", "created_at")
    search_fields = ("title", "description", "user__username")
    readonly_fields = ("created_at", "completed_at")
    ordering = ("-created_at",)
```

## 3. Register Controller in IoC

Add the controller registration to `src/ioc/registries/delivery.py`:

```python
# src/ioc/registries/delivery.py
# Add this import at the top
from delivery.http.todo.controllers import TodoController

# Add this line in _register_http_controllers()
def _register_http_controllers(container: Container) -> None:
    container.register(HealthController, scope=Scope.singleton)
    container.register(UserController, scope=Scope.singleton)
    container.register(UserTokenController, scope=Scope.singleton)
    container.register(TodoController, scope=Scope.singleton)  # Add this
```

## 4. Update NinjaAPIFactory

Modify `src/delivery/http/factories.py` to inject and register the controller:

```python
# src/delivery/http/factories.py
# Add import at the top
from delivery.http.todo.admin import TodoAdmin
from delivery.http.todo.controllers import TodoController
from core.todo.models import Todo

class NinjaAPIFactory:
    def __init__(
        self,
        settings: ApplicationSettings,
        health_controller: HealthController,
        user_token_controller: UserTokenController,
        user_controller: UserController,
        todo_controller: TodoController,  # Add this
    ) -> None:
        self._settings = settings
        self._health_controller = health_controller
        self._user_token_controller = user_token_controller
        self._user_controller = user_controller
        self._todo_controller = todo_controller  # Add this

    def __call__(
        self,
        urls_namespace: str | None = None,
    ) -> NinjaAPI:
        # ... existing code ...

        # Add todo router after user router
        todo_router = Router(tags=["todo"])
        ninja_api.add_router("/", todo_router)
        self._todo_controller.register(registry=todo_router)

        return ninja_api


class AdminSiteFactory:
    def __call__(self) -> AdminSite:
        default_site.register(User, admin_class=UserAdmin)
        default_site.register(Todo, admin_class=TodoAdmin)  # Add this
        return default_site
```

## 5. Test the API

Start the development server:

```bash
make dev
```

### Create a User and Get Token

```bash
# Create a user
curl -X POST http://localhost:8000/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "todouser", "email": "todo@example.com", "password": "SecurePass123!", "first_name": "Todo", "last_name": "User"}'

# Get JWT token
curl -X POST http://localhost:8000/v1/users/me/token \
  -H "Content-Type: application/json" \
  -d '{"username": "todouser", "password": "SecurePass123!"}'
```

Save the `access_token` from the response.

### Test Todo Endpoints

```bash
# Set your token
TOKEN="your-access-token-here"

# Create a todo
curl -X POST http://localhost:8000/v1/todos/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn the tutorial", "description": "Step 3: HTTP API"}'

# List todos
curl http://localhost:8000/v1/todos/ \
  -H "Authorization: Bearer $TOKEN"

# Complete a todo (replace 1 with actual ID)
curl -X POST http://localhost:8000/v1/todos/1/complete \
  -H "Authorization: Bearer $TOKEN"
```

### Access the Admin Panel

Open [http://localhost:8000/admin](http://localhost:8000/admin) and log in with your superuser credentials. You should see the "Todos" section.

## Understanding Rate Limiting

The template uses Django Ninja's built-in throttling with Django cache backend (Redis in production):

| Throttle Class | Description |
|----------------|-------------|
| `AnonRateThrottle` | Rate limit by IP for anonymous users |
| `AuthRateThrottle` | Rate limit by user ID for authenticated users |

Rate format examples:

- `"30/min"` - 30 requests per minute
- `"5/min"` - 5 requests per minute
- `"1000/day"` - 1000 requests per day

## What You've Learned

In this step, you:

1. Created a controller with CRUD endpoints
2. Implemented exception handling with `handle_exception()`
3. Added rate limiting with Django Ninja's throttling
4. Set up Django admin for the Todo model
5. Registered the controller in the IoC container

## Next Step

In [Step 4: Celery Tasks](04-celery-tasks.md), you'll create a background task to clean up old completed todos.
