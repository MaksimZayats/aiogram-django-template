# Controller Pattern

Controllers are the entry points for handling requests in this template. They provide a unified interface for HTTP endpoints, Celery tasks, and Telegram bot handlers while automatically handling exceptions.

## Two Base Classes

The template provides two abstract base classes depending on whether your handlers are synchronous or asynchronous:

### Controller (Synchronous)

Used for HTTP endpoints and Celery tasks:

```python
from infrastructure.delivery.controllers import Controller

class HealthController(Controller):
    def __init__(self, health_service: HealthService) -> None:
        self._health_service = health_service

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/health",
            methods=["GET"],
            view_func=self.health_check,
            response=HealthCheckResponseSchema,
            auth=None,
        )

    def health_check(self, request: HttpRequest) -> HealthCheckResponseSchema:
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
def health_check(self, request: HttpRequest) -> HealthCheckResponseSchema:
    self._health_service.check_system_health()
    return HealthCheckResponseSchema(status="ok")

# What actually executes:
def health_check(self, request: HttpRequest) -> HealthCheckResponseSchema:
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

Register handlers with a Django-Ninja Router:

```python
class UserController(Controller):
    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/users/",
            methods=["POST"],
            view_func=self.create_user,
            response=UserSchema,
            auth=None,
            throttle=AnonRateThrottle(rate="30/min"),
        )

        registry.add_api_operation(
            path="/v1/users/me",
            methods=["GET"],
            view_func=self.get_current_user,
            response=UserSchema,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
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
class UserTokenController(Controller):
    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, InvalidRefreshTokenError):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Invalid refresh token",
            ) from exception

        if isinstance(exception, ExpiredRefreshTokenError):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Refresh token expired or revoked",
            ) from exception

        # Re-raise unknown exceptions
        return super().handle_exception(exception)
```

!!! tip "Always Call Super"
    End your `handle_exception()` method by calling `super().handle_exception(exception)` to re-raise unhandled exceptions.

## Controller Structure

A typical controller follows this structure:

```python
class ItemController(Controller):
    # 1. Dependencies injected via __init__
    def __init__(
        self,
        jwt_auth_factory: JWTAuthFactory,
        item_service: ItemService,
    ) -> None:
        self._jwt_auth = jwt_auth_factory()
        self._item_service = item_service

    # 2. Registration connects handlers to framework
    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/items",
            methods=["GET"],
            view_func=self.list_items,
            response=list[ItemSchema],
            auth=self._jwt_auth,
        )
        registry.add_api_operation(
            path="/v1/items/{item_id}",
            methods=["GET"],
            view_func=self.get_item,
            response=ItemSchema,
            auth=self._jwt_auth,
        )

    # 3. Handler methods implement business logic calls
    def list_items(self, request: AuthenticatedHttpRequest) -> list[ItemSchema]:
        items = self._item_service.list_items()
        return [ItemSchema.model_validate(item, from_attributes=True) for item in items]

    def get_item(
        self,
        request: AuthenticatedHttpRequest,
        item_id: int,
    ) -> ItemSchema:
        item = self._item_service.get_item_by_id(item_id)
        return ItemSchema.model_validate(item, from_attributes=True)

    # 4. Exception handling converts domain errors to responses
    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, ItemNotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message=str(exception),
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
class HealthController(Controller):
    def __init__(self, health_service: HealthService) -> None:
        self._health_service = health_service

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/health",
            methods=["GET"],
            view_func=self.health_check,
            response=HealthCheckResponseSchema,
            auth=None,
        )

    def health_check(self, request: HttpRequest) -> HealthCheckResponseSchema:
        try:
            self._health_service.check_system_health()
        except HealthCheckError as e:
            raise HttpError(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                message="Service is unavailable",
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
