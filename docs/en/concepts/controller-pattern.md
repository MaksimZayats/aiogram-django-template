# Controller Pattern

Controllers are the entry points for handling requests in this template. They provide a unified interface for HTTP endpoints and Celery tasks while automatically handling exceptions.

## Two Base Classes

The template provides two abstract base classes depending on whether your handlers are synchronous or asynchronous:

### Controller (Synchronous)

Used for HTTP endpoints and Celery tasks:

```python
from dataclasses import dataclass
from fastapi import APIRouter, Request
from infrastructure.delivery.controllers import Controller

@dataclass
class HealthController(Controller):
    _health_service: HealthService

    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/v1/health",
            endpoint=self.health_check,
            methods=["GET"],
            response_model=HealthCheckResponseSchema,
        )

    def health_check(self) -> HealthCheckResponseSchema:
        self._health_service.check_system_health()
        return HealthCheckResponseSchema(status="ok")
```

## Automatic Exception Wrapping

Both base classes use `__new__` to automatically wrap all public methods with exception handling:

```python
class Controller(ABC):
    def __new__(cls, *_args: Any, **_kwargs: Any) -> Self:
        self = super().__new__(cls)
        _wrap_methods(self)  # Wraps all public methods
        return self
```

This means every handler method is automatically wrapped in a try-except block that calls `handle_exception()`:

```python
# What you write:
def health_check(self) -> HealthCheckResponseSchema:
    self._health_service.check_system_health()
    return HealthCheckResponseSchema(status="ok")

# What actually executes:
def health_check(self) -> HealthCheckResponseSchema:
    try:
        self._health_service.check_system_health()
        return HealthCheckResponseSchema(status="ok")
    except Exception as e:
        return self.handle_exception(e)
```

## The register() Method

Every controller must implement `register()`. This method connects the controller's handlers to the appropriate framework registry:

```
+----------------+     +----------------+     +----------------+
|   Controller   |---->|    register()  |---->|    Registry    |
+----------------+     +----------------+     +----------------+
                              |
                              v
                       Connects handlers
                       to framework
```

### HTTP Controllers

Register handlers with a FastAPI APIRouter:

```python
from dataclasses import dataclass, field
from fastapi import APIRouter, Depends
from delivery.http.auth.jwt import JWTAuth, JWTAuthFactory

@dataclass
class UserController(Controller):
    _jwt_auth_factory: JWTAuthFactory
    _jwt_auth: JWTAuth = field(init=False)

    def __post_init__(self) -> None:
        self._jwt_auth = self._jwt_auth_factory()

    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/v1/users/",
            endpoint=self.create_user,
            methods=["POST"],
            response_model=UserSchema,
        )

        registry.add_api_route(
            path="/v1/users/me",
            endpoint=self.get_current_user,
            methods=["GET"],
            response_model=UserSchema,
            dependencies=[Depends(self._jwt_auth)],
        )
```

### Celery Task Controllers

Register handlers with a Celery app:

```python
from delivery.tasks.registry import TaskName

class PingTaskController(Controller):
    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.PING)(self.ping)

    def ping(self) -> PingResult:
        return PingResult(result="pong")
```

## Custom Exception Handling

Override `handle_exception()` to convert domain exceptions into appropriate responses:

```python
from fastapi import HTTPException
from http import HTTPStatus

class UserTokenController(Controller):
    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, InvalidRefreshTokenError):
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from exception

        if isinstance(exception, ExpiredRefreshTokenError):
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Refresh token expired or revoked",
            ) from exception

        # Re-raise unknown exceptions
        return super().handle_exception(exception)
```

!!! tip "Always Call Super"
    End your `handle_exception()` method by calling `super().handle_exception(exception)` to re-raise unhandled exceptions.

## Controller Structure

A typical controller follows this structure:

```python
from dataclasses import dataclass, field
from fastapi import APIRouter, Depends, HTTPException
from http import HTTPStatus
from delivery.http.auth.jwt import AuthenticatedRequest, JWTAuth, JWTAuthFactory

@dataclass
class ItemController(Controller):
    # 1. Dependencies injected via dataclass fields
    _jwt_auth_factory: JWTAuthFactory
    _item_service: ItemService
    _jwt_auth: JWTAuth = field(init=False)

    def __post_init__(self) -> None:
        self._jwt_auth = self._jwt_auth_factory()

    # 2. Registration connects handlers to framework
    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/v1/items",
            endpoint=self.list_items,
            methods=["GET"],
            response_model=list[ItemSchema],
            dependencies=[Depends(self._jwt_auth)],
        )
        registry.add_api_route(
            path="/v1/items/{item_id}",
            endpoint=self.get_item,
            methods=["GET"],
            response_model=ItemSchema,
            dependencies=[Depends(self._jwt_auth)],
        )

    # 3. Handler methods implement business logic calls
    def list_items(self, request: AuthenticatedRequest) -> list[ItemSchema]:
        items = self._item_service.list_items()
        return [ItemSchema.model_validate(item, from_attributes=True) for item in items]

    def get_item(
        self,
        request: AuthenticatedRequest,
        item_id: int,
    ) -> ItemSchema:
        item = self._item_service.get_item_by_id(item_id)
        return ItemSchema.model_validate(item, from_attributes=True)

    # 4. Exception handling converts domain errors to responses
    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, ItemNotFoundError):
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=str(exception),
            ) from exception

        return super().handle_exception(exception)
```

## Method Wrapping Details

The wrapping logic excludes certain methods:

```python
_CONTROLLER_METHODS_EXCLUDE = ("register", "handle_exception")
```

Only public methods (not starting with `_`) that are not in the exclusion list get wrapped:

| Method | Wrapped? |
|--------|----------|
| `health_check` | Yes |
| `create_user` | Yes |
| `register` | No (excluded) |
| `handle_exception` | No (excluded) |
| `_private_method` | No (private) |

## Real-World Examples

### HTTP Health Check Controller

```python
from dataclasses import dataclass
from fastapi import APIRouter, HTTPException, Request
from http import HTTPStatus

@dataclass
class HealthController(Controller):
    _health_service: HealthService

    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/v1/health",
            endpoint=self.health_check,
            methods=["GET"],
            response_model=HealthCheckResponseSchema,
        )

    def health_check(self) -> HealthCheckResponseSchema:
        try:
            self._health_service.check_system_health()
        except HealthCheckError as e:
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="Service is unavailable",
            ) from e

        return HealthCheckResponseSchema(status="ok")
```

### Celery Ping Task Controller

```python
class PingTaskController(Controller):
    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.PING)(self.ping)

    def ping(self) -> PingResult:
        return PingResult(result="pong")
```

## Controller Registration in IoC

Controllers are registered as singletons:

```python
# ioc/registries/delivery.py
def _register_http_controllers(container: Container) -> None:
    container.register(HealthController, scope=Scope.singleton)
    container.register(UserController, scope=Scope.singleton)
    container.register(UserTokenController, scope=Scope.singleton)

def _register_celery_controllers(container: Container) -> None:
    container.register(PingTaskController, scope=Scope.singleton)
```

## Summary

The Controller pattern provides:

| Feature | Benefit |
|---------|---------|
| Automatic exception wrapping | Consistent error handling without boilerplate |
| Abstract `register()` | Unified interface across frameworks |
| Sync and async variants | Support for all entry points |
| Dependency injection | Loose coupling, testability |
| `handle_exception()` override | Customizable error responses |

Controllers serve as the bridge between external frameworks and your application's services. They handle framework-specific concerns while delegating business logic to the service layer.
