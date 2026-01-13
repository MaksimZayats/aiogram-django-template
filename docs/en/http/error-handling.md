# Error Handling

Custom exception handling and HTTP error responses.

## Controller Exception Handling

The `Controller` base class provides automatic exception wrapping:

```python
class Controller(ABC):
    def __new__(cls, *_args: Any, **_kwargs: Any) -> Self:
        self = super().__new__(cls)
        _wrap_methods(self)  # Wraps all public methods
        return self

    def handle_exception(self, exception: Exception) -> NoReturn:
        raise exception  # Default: re-raise
```

All public methods are wrapped to catch exceptions and route them to `handle_exception()`.

## Overriding handle_exception

Override to convert domain exceptions to HTTP errors:

```python
from http import HTTPStatus
from typing import NoReturn

from ninja.errors import HttpError

from infrastructure.delivery.controllers import Controller


class ItemNotFoundError(Exception):
    pass


class ItemController(Controller):
    def get_item(self, request: HttpRequest, item_id: int) -> ItemSchema:
        item = Item.objects.filter(id=item_id).first()
        if item is None:
            raise ItemNotFoundError()
        return ItemSchema.model_validate(item, from_attributes=True)

    def handle_exception(self, exception: Exception) -> NoReturn:
        if isinstance(exception, ItemNotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message="Item not found",
            ) from exception

        # Re-raise unhandled exceptions
        raise exception
```

## Real Example: Token Controller

```python
class UserTokenController(Controller):
    def handle_exception(self, exception: Exception) -> NoReturn:
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

        if isinstance(exception, RefreshTokenError):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Refresh token error",
            ) from exception

        raise exception
```

## HttpError Class

Django-Ninja's `HttpError` for HTTP error responses:

```python
from http import HTTPStatus
from ninja.errors import HttpError

# Basic usage
raise HttpError(
    status_code=HTTPStatus.NOT_FOUND,
    message="Resource not found",
)

# With custom status code
raise HttpError(
    status_code=HTTPStatus.BAD_REQUEST,
    message="Invalid input",
)
```

Response format:

```json
{
  "detail": "Resource not found"
}
```

## Common HTTP Status Codes

| Code | Constant | Usage |
|------|----------|-------|
| 400 | `HTTPStatus.BAD_REQUEST` | Invalid request data |
| 401 | `HTTPStatus.UNAUTHORIZED` | Authentication required/failed |
| 403 | `HTTPStatus.FORBIDDEN` | Permission denied |
| 404 | `HTTPStatus.NOT_FOUND` | Resource not found |
| 409 | `HTTPStatus.CONFLICT` | Resource conflict |
| 422 | `HTTPStatus.UNPROCESSABLE_ENTITY` | Validation error |
| 500 | `HTTPStatus.INTERNAL_SERVER_ERROR` | Server error |

## Validation Errors

Pydantic validation errors are automatically handled by Django-Ninja:

```python
class CreateUserSchema(BaseModel):
    email: EmailStr
    username: Annotated[str, Len(min_length=3)]

# Invalid request:
# {"email": "invalid", "username": "ab"}

# Response (422):
# {
#   "detail": [
#     {"loc": ["body", "email"], "msg": "invalid email", "type": "value_error"},
#     {"loc": ["body", "username"], "msg": "min length 3", "type": "value_error"}
#   ]
# }
```

## Custom Validation

For business logic validation:

```python
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


def create_user(
    self,
    request: HttpRequest,
    body: CreateUserSchema,
) -> UserSchema:
    # Custom validation
    try:
        validate_password(body.password)
    except ValidationError as exc:
        raise HttpError(
            status_code=HTTPStatus.BAD_REQUEST,
            message=str(exc.message),
        ) from exc

    # Uniqueness check
    if User.objects.filter(username=body.username).exists():
        raise HttpError(
            status_code=HTTPStatus.BAD_REQUEST,
            message="Username already exists",
        )

    # Create user...
```

## Exception Hierarchy

Create domain-specific exception hierarchies:

```python
# Base exceptions
class ItemError(Exception):
    """Base exception for item operations."""
    pass


class ItemNotFoundError(ItemError):
    """Item does not exist."""
    pass


class ItemPermissionError(ItemError):
    """User lacks permission for this item."""
    pass


# Handler
def handle_exception(self, exception: Exception) -> NoReturn:
    if isinstance(exception, ItemNotFoundError):
        raise HttpError(HTTPStatus.NOT_FOUND, "Item not found")

    if isinstance(exception, ItemPermissionError):
        raise HttpError(HTTPStatus.FORBIDDEN, "Permission denied")

    if isinstance(exception, ItemError):
        raise HttpError(HTTPStatus.BAD_REQUEST, str(exception))

    raise exception
```

## Logging Errors

Log exceptions before converting to HTTP errors:

```python
import logging

logger = logging.getLogger(__name__)


class ItemController(Controller):
    def handle_exception(self, exception: Exception) -> NoReturn:
        if isinstance(exception, ItemNotFoundError):
            logger.warning("Item not found: %s", exception)
            raise HttpError(HTTPStatus.NOT_FOUND, "Item not found")

        # Log unexpected errors
        logger.exception("Unexpected error in ItemController")
        raise exception
```

## Best Practices

### 1. Be Specific

```python
# Good: Specific error messages
raise HttpError(HTTPStatus.NOT_FOUND, "User with ID 123 not found")

# Avoid: Generic messages
raise HttpError(HTTPStatus.NOT_FOUND, "Not found")
```

### 2. Use Appropriate Status Codes

```python
# Good: 401 for auth failures
raise HttpError(HTTPStatus.UNAUTHORIZED, "Invalid token")

# Avoid: 400 for auth failures
raise HttpError(HTTPStatus.BAD_REQUEST, "Invalid token")
```

### 3. Hide Internal Details

```python
# Good: User-friendly message
raise HttpError(HTTPStatus.INTERNAL_SERVER_ERROR, "An error occurred")

# Avoid: Exposing internal details
raise HttpError(HTTPStatus.INTERNAL_SERVER_ERROR, str(database_error))
```

### 4. Always Re-raise Unknown Exceptions

```python
def handle_exception(self, exception: Exception) -> NoReturn:
    if isinstance(exception, KnownError):
        raise HttpError(...)

    # Always re-raise unknown exceptions
    raise exception
```

## Testing Error Handling

```python
def test_item_not_found(test_client: TestClient) -> None:
    response = test_client.get("/v1/items/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


def test_validation_error(test_client: TestClient) -> None:
    response = test_client.post(
        "/v1/users/",
        json={"email": "invalid"},
    )

    assert response.status_code == 422
```

## Related Topics

- [Controller Pattern](../concepts/controller-pattern.md) — Base controller
- [Controllers](controllers.md) — HTTP controllers
- [HTTP API Tests](../testing/http-tests.md) — Testing error handling
