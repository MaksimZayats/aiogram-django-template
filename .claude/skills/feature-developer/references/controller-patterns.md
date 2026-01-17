# Controller Patterns Reference

This reference provides complete examples for controller types: HTTP API and Celery tasks.

## Contents

- [HTTP Controller (FastAPI)](#http-controller-fastapi)
  - [Sync vs Async Handlers](#sync-vs-async-handlers)
  - [Basic CRUD Controller](#basic-crud-controller)
  - [User-Scoped Resources](#user-scoped-resources)
  - [Async Handlers (Advanced)](#async-handlers-advanced)
- [Celery Task Controller](#celery-task-controller)
  - [Basic Task](#basic-task)
  - [Task with Arguments](#task-with-arguments)
  - [Register Task Name](#register-task-name)
  - [Register Task in IoC](#register-task-in-ioc)
  - [Update CeleryAppFactory](#update-celeryappfactory)
- [Exception Handling Patterns](#exception-handling-patterns)

## HTTP Controller (FastAPI)

### Sync vs Async Handlers

**Always use synchronous handler methods.** FastAPI automatically runs sync handlers in a thread pool using `anyio.to_thread.run_sync()`, which provides proper parallelism for Django's synchronous ORM.

```python
# ✅ CORRECT - Sync handler (recommended)
def list_items(self, request: AuthenticatedRequest) -> ItemListSchema:
    items = self._item_service.list_all()  # Sync service call
    return ItemListSchema(items=items)

# ❌ WRONG - Async handler calling sync service directly
async def list_items(self, request: AuthenticatedRequest) -> ItemListSchema:
    items = self._item_service.list_all()  # Blocks the event loop!
    return ItemListSchema(items=items)
```

**Why sync handlers?**

1. Django ORM is synchronous - all database operations block
2. FastAPI runs sync handlers in `anyio.to_thread.run_sync()` automatically
3. Parallelism is controlled via `ANYIO_THREAD_LIMITER_TOKENS` environment variable
4. Default is 40 concurrent threads per worker (configured in `src/infrastructure/anyio/configurator.py`)

### Basic CRUD Controller

```python
# src/delivery/http/<domain>/controllers.py
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.<domain>.services import <Domain>Service, <Domain>NotFoundError
from infrastructure.delivery.controllers import Controller
from infrastructure.fastapi.auth import AuthenticatedRequest, JWTAuth, JWTAuthFactory


# Response Schemas
class <Model>Schema(BaseModel):
    id: int
    # ... other fields

    model_config = {"from_attributes": True}


class <Model>ListSchema(BaseModel):
    items: list[<Model>Schema]
    count: int


# Request Schemas
class Create<Model>Request(BaseModel):
    # ... required fields for creation


class Update<Model>Request(BaseModel):
    # ... optional fields for update (all fields optional)


@dataclass
class <Domain>Controller(Controller):
    _jwt_auth_factory: JWTAuthFactory
    _<domain>_service: <Domain>Service
    _jwt_auth: JWTAuth = field(init=False)

    def __post_init__(self) -> None:
        self._jwt_auth = self._jwt_auth_factory()

    def register(self, registry: APIRouter) -> None:
        # List endpoint
        registry.add_api_route(
            path="/v1/<domain>s/",
            endpoint=self.list_items,
            methods=["GET"],
            response_model=<Model>ListSchema,
            dependencies=[Depends(self._jwt_auth)],
        )

        # Create endpoint
        registry.add_api_route(
            path="/v1/<domain>s/",
            endpoint=self.create_item,
            methods=["POST"],
            response_model=<Model>Schema,
            dependencies=[Depends(self._jwt_auth)],
        )

        # Get single item
        registry.add_api_route(
            path="/v1/<domain>s/{item_id}",
            endpoint=self.get_item,
            methods=["GET"],
            response_model=<Model>Schema,
            dependencies=[Depends(self._jwt_auth)],
        )

        # Update item
        registry.add_api_route(
            path="/v1/<domain>s/{item_id}",
            endpoint=self.update_item,
            methods=["PATCH"],
            response_model=<Model>Schema,
            dependencies=[Depends(self._jwt_auth)],
        )

        # Delete item
        registry.add_api_route(
            path="/v1/<domain>s/{item_id}",
            endpoint=self.delete_item,
            methods=["DELETE"],
            status_code=HTTPStatus.NO_CONTENT,
            dependencies=[Depends(self._jwt_auth)],
        )

    def list_items(
        self,
        request: AuthenticatedRequest,
    ) -> <Model>ListSchema:
        items = self._<domain>_service.list_all()
        return <Model>ListSchema(
            items=[<Model>Schema.model_validate(i, from_attributes=True) for i in items],
            count=len(items),
        )

    def create_item(
        self,
        request: AuthenticatedRequest,
        body: Create<Model>Request,
    ) -> <Model>Schema:
        item = self._<domain>_service.create(**body.model_dump())
        return <Model>Schema.model_validate(item, from_attributes=True)

    def get_item(
        self,
        request: AuthenticatedRequest,
        item_id: int,
    ) -> <Model>Schema:
        item = self._<domain>_service.get_by_id(item_id)
        return <Model>Schema.model_validate(item, from_attributes=True)

    def update_item(
        self,
        request: AuthenticatedRequest,
        item_id: int,
        body: Update<Model>Request,
    ) -> <Model>Schema:
        item = self._<domain>_service.update(
            item_id=item_id,
            **body.model_dump(exclude_unset=True),
        )
        return <Model>Schema.model_validate(item, from_attributes=True)

    def delete_item(
        self,
        request: AuthenticatedRequest,
        item_id: int,
    ) -> None:
        self._<domain>_service.delete(item_id)

    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, <Domain>NotFoundError):
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=str(exception),
            ) from exception
        return super().handle_exception(exception)
```

### User-Scoped Resources

When resources belong to a specific user:

```python
def list_items(
    self,
    request: AuthenticatedRequest,
) -> list[<Model>Schema]:
    # Pass the authenticated user to scope the query
    items = self._<domain>_service.list_for_user(user_id=request.state.user.id)
    return [<Model>Schema.model_validate(i, from_attributes=True) for i in items]

def create_item(
    self,
    request: AuthenticatedRequest,
    body: Create<Model>Request,
) -> <Model>Schema:
    # Associate the resource with the authenticated user
    item = self._<domain>_service.create(
        user_id=request.state.user.id,
        **body.model_dump(),
    )
    return <Model>Schema.model_validate(item, from_attributes=True)
```

### Async Handlers (Advanced)

In rare cases where you need async handlers (e.g., calling external async APIs), use `asgiref.sync_to_async` to call services:

```python
from asgiref.sync import sync_to_async

@dataclass
class <Domain>Controller(Controller):
    _<domain>_service: <Domain>Service

    async def list_items_async(
        self,
        request: AuthenticatedRequest,
    ) -> <Model>ListSchema:
        # For READ-ONLY operations: thread_sensitive=False
        # This allows parallel execution in any thread
        items = await sync_to_async(
            self._<domain>_service.list_all,
            thread_sensitive=False,
        )()
        return <Model>ListSchema(items=items)

    async def create_item_async(
        self,
        request: AuthenticatedRequest,
        body: Create<Model>Request,
    ) -> <Model>Schema:
        # For WRITE operations: thread_sensitive=True (default)
        # This ensures database transactions are handled correctly
        item = await sync_to_async(
            self._<domain>_service.create,
            thread_sensitive=True,
        )(**body.model_dump())
        return <Model>Schema.model_validate(item, from_attributes=True)
```

**Thread sensitivity rules:**

| Operation Type | `thread_sensitive` | Why |
|----------------|-------------------|-----|
| Read-only (SELECT) | `False` | Can run in any thread, enables parallelism |
| Write (INSERT/UPDATE/DELETE) | `True` | Must run in same thread for transaction safety |
| Mixed/Unknown | `True` | Default to safe behavior |

**When to use async handlers:**

- Calling external async HTTP clients (httpx, aiohttp)
- WebSocket handlers
- Streaming responses
- Orchestrating multiple async I/O operations

**Prefer sync handlers when:**

- Only calling Django services (99% of cases)
- No external async dependencies

## Celery Task Controller

### Basic Task

```python
# src/delivery/tasks/tasks/<task_name>.py
from pydantic import BaseModel

from core.<domain>.services import <Domain>Service
from delivery.tasks.registry import TaskName
from infrastructure.delivery.controllers import Controller


class <Task>Result(BaseModel):
    # ... result fields


class <Task>TaskController(Controller):
    def __init__(
        self,
        <domain>_service: <Domain>Service,
    ) -> None:
        self._<domain>_service = <domain>_service

    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.<TASK_NAME>)(self.<task_method>)

    def <task_method>(self) -> <Task>Result:
        # Task implementation
        result = self._<domain>_service.some_operation()
        return <Task>Result(...)
```

### Task with Arguments

```python
class SendNotificationController(Controller):
    def __init__(
        self,
        notification_service: NotificationService,
    ) -> None:
        self._notification_service = notification_service

    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.SEND_NOTIFICATION)(self.send_notification)

    def send_notification(
        self,
        user_id: int,
        message: str,
        channel: str = "email",
    ) -> dict[str, Any]:
        result = self._notification_service.send(
            user_id=user_id,
            message=message,
            channel=channel,
        )
        return {"status": "sent", "notification_id": result.id}
```

### Register Task Name

Add to `src/delivery/tasks/registry.py`:

```python
from enum import StrEnum


class TaskName(StrEnum):
    PING = "ping"
    # Add your new task
    <TASK_NAME> = "<task_name>"
```

### Register Task in IoC

```python
# src/ioc/registries/delivery.py
from delivery.tasks.tasks.<task_name> import <Task>TaskController


def _register_celery_controllers(container: Container) -> None:
    # ... existing registrations
    container.register(<Task>TaskController, scope=Scope.singleton)
```

### Update CeleryAppFactory

```python
# src/delivery/tasks/factories.py
class CeleryAppFactory:
    def __init__(
        self,
        # ... existing dependencies
        <task>_controller: <Task>TaskController,
    ) -> None:
        # ... existing assignments
        self._<task>_controller = <task>_controller

    def __call__(self) -> Celery:
        # ... existing code
        self._<task>_controller.register(app)
        return app
```

## Exception Handling Patterns

### HTTP Controller

```python
def handle_exception(self, exception: Exception) -> Any:
    match exception:
        case <Domain>NotFoundError():
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=str(exception),
            ) from exception
        case <Domain>ValidationError():
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=str(exception),
            ) from exception
        case <Domain>PermissionError():
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=str(exception),
            ) from exception
        case _:
            return super().handle_exception(exception)
```
