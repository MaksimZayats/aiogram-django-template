# Controller Patterns Reference

This reference provides complete examples for controller types: HTTP API and Celery tasks.

## Contents

- [HTTP Controller (Django Ninja)](#http-controller-django-ninja)
  - [Basic CRUD Controller](#basic-crud-controller)
  - [User-Scoped Resources](#user-scoped-resources)
- [Celery Task Controller](#celery-task-controller)
  - [Basic Task](#basic-task)
  - [Task with Arguments](#task-with-arguments)
  - [Register Task Name](#register-task-name)
  - [Register Task in IoC](#register-task-in-ioc)
  - [Update CeleryAppFactory](#update-celeryappfactory)
- [Exception Handling Patterns](#exception-handling-patterns)

## HTTP Controller (Django Ninja)

### Basic CRUD Controller

```python
# src/delivery/http/<domain>/controllers.py
from http import HTTPStatus
from typing import Any

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import paginate, PageNumberPagination
from ninja.throttling import AuthRateThrottle
from pydantic import BaseModel

from core.<domain>.services import <Domain>Service, <Domain>NotFoundError
from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import AuthenticatedHttpRequest, JWTAuthFactory


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


class <Domain>Controller(Controller):
    def __init__(
        self,
        jwt_auth_factory: JWTAuthFactory,
        <domain>_service: <Domain>Service,
    ) -> None:
        self._jwt_auth = jwt_auth_factory()
        self._<domain>_service = <domain>_service

    def register(self, registry: Router) -> None:
        # List endpoint with pagination
        registry.add_api_operation(
            path="/v1/<domain>s/",
            methods=["GET"],
            view_func=self.list_items,
            response=<Model>ListSchema,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="60/min"),
        )

        # Create endpoint
        registry.add_api_operation(
            path="/v1/<domain>s/",
            methods=["POST"],
            view_func=self.create_item,
            response=<Model>Schema,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )

        # Get single item
        registry.add_api_operation(
            path="/v1/<domain>s/{item_id}",
            methods=["GET"],
            view_func=self.get_item,
            response=<Model>Schema,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="60/min"),
        )

        # Update item
        registry.add_api_operation(
            path="/v1/<domain>s/{item_id}",
            methods=["PATCH"],
            view_func=self.update_item,
            response=<Model>Schema,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )

        # Delete item
        registry.add_api_operation(
            path="/v1/<domain>s/{item_id}",
            methods=["DELETE"],
            view_func=self.delete_item,
            response={HTTPStatus.NO_CONTENT: None},
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )

    def list_items(
        self,
        request: AuthenticatedHttpRequest,
    ) -> <Model>ListSchema:
        items = self._<domain>_service.list_all()
        return <Model>ListSchema(
            items=[<Model>Schema.model_validate(i, from_attributes=True) for i in items],
            count=len(items),
        )

    def create_item(
        self,
        request: AuthenticatedHttpRequest,
        body: Create<Model>Request,
    ) -> <Model>Schema:
        item = self._<domain>_service.create(**body.model_dump())
        return <Model>Schema.model_validate(item, from_attributes=True)

    def get_item(
        self,
        request: AuthenticatedHttpRequest,
        item_id: int,
    ) -> <Model>Schema:
        item = self._<domain>_service.get_by_id(item_id)
        return <Model>Schema.model_validate(item, from_attributes=True)

    def update_item(
        self,
        request: AuthenticatedHttpRequest,
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
        request: AuthenticatedHttpRequest,
        item_id: int,
    ) -> None:
        self._<domain>_service.delete(item_id)

    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, <Domain>NotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message=str(exception),
            ) from exception
        return super().handle_exception(exception)
```

### User-Scoped Resources

When resources belong to a specific user:

```python
def list_items(
    self,
    request: AuthenticatedHttpRequest,
) -> list[<Model>Schema]:
    # Pass the authenticated user to scope the query
    items = self._<domain>_service.list_for_user(user_id=request.user.pk)
    return [<Model>Schema.model_validate(i, from_attributes=True) for i in items]

def create_item(
    self,
    request: AuthenticatedHttpRequest,
    body: Create<Model>Request,
) -> <Model>Schema:
    # Associate the resource with the authenticated user
    item = self._<domain>_service.create(
        user_id=request.user.pk,
        **body.model_dump(),
    )
    return <Model>Schema.model_validate(item, from_attributes=True)
```

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
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message=str(exception),
            ) from exception
        case <Domain>ValidationError():
            raise HttpError(
                status_code=HTTPStatus.BAD_REQUEST,
                message=str(exception),
            ) from exception
        case <Domain>PermissionError():
            raise HttpError(
                status_code=HTTPStatus.FORBIDDEN,
                message=str(exception),
            ) from exception
        case _:
            return super().handle_exception(exception)
```
