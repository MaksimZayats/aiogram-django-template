# Service Layer

The service layer is the most important architectural pattern in this template. It enforces a clean separation between request handling (controllers) and business logic (services).

## The Golden Rule

```
Controller → Service → Model

✅ Controller imports Service
✅ Service imports Model
❌ Controller imports Model (NEVER)
```

## Why This Matters

### Without Service Layer

```python
# ❌ BAD - Controller directly uses ORM
class UserController:
    def create_user(self, request, body):
        # Validation scattered in controller
        if User.objects.filter(email=body.email).exists():
            raise HttpError(409, "Email exists")

        # Business logic in controller
        user = User.objects.create(
            email=body.email,
            password=make_password(body.password),
        )

        # Direct model access
        return UserSchema.from_orm(user)
```

Problems:

- **Hard to test** - Must mock Django ORM
- **Duplication** - Same logic repeated across HTTP/Celery/Bot
- **Tight coupling** - Controller knows about database details

### With Service Layer

```python
# ✅ GOOD - Controller uses service
class UserController:
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    def create_user(self, request, body):
        # Service handles all business logic
        user = self._user_service.create_user(
            email=body.email,
            password=body.password,
        )
        return UserSchema.model_validate(user, from_attributes=True)


# Service encapsulates business logic
class UserService:
    def create_user(self, email: str, password: str) -> User:
        if User.objects.filter(email=email).exists():
            raise UserAlreadyExistsError(email)

        return User.objects.create(
            email=email,
            password=make_password(password),
        )
```

Benefits:

- **Easy to test** - Mock the service, not the ORM
- **Reusable** - Same service used by HTTP, Celery, Bot
- **Maintainable** - Business logic in one place

## Service Structure

Services live in `core/<domain>/services.py`:

```python
# src/core/user/services.py
from django.db import transaction
from core.exceptions import ApplicationError
from core.user.models import User


class UserNotFoundError(ApplicationError):
    """Raised when user cannot be found."""


class UserAlreadyExistsError(ApplicationError):
    """Raised when user with email already exists."""


class UserService:
    def get_user_by_id(self, user_id: int) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist as e:
            raise UserNotFoundError(f"User {user_id} not found") from e

    def get_user_by_email(self, email: str) -> User | None:
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    @transaction.atomic
    def create_user(self, email: str, password: str) -> User:
        if self.get_user_by_email(email) is not None:
            raise UserAlreadyExistsError(email)

        return User.objects.create_user(email=email, password=password)
```

## Domain Exceptions

Services define domain-specific exceptions that inherit from `ApplicationError`:

```python
from core.exceptions import ApplicationError


class TodoNotFoundError(ApplicationError):
    """Raised when a todo item cannot be found."""


class TodoAccessDeniedError(ApplicationError):
    """Raised when user tries to access another user's todo."""
```

Controllers convert these to HTTP errors:

```python
class TodoController(Controller):
    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, TodoNotFoundError):
            raise HttpError(HTTPStatus.NOT_FOUND, "Todo not found") from exception
        if isinstance(exception, TodoAccessDeniedError):
            raise HttpError(HTTPStatus.FORBIDDEN, "Access denied") from exception
        return super().handle_exception(exception)
```

## Best Practices

### 1. One Service Per Domain

```python
# ✅ GOOD - Focused service
class UserService:
    def get_user_by_id(self, user_id: int) -> User: ...
    def create_user(self, email: str, password: str) -> User: ...

# ❌ BAD - Service doing too much
class AppService:
    def get_user(self, user_id: int) -> User: ...
    def create_todo(self, user: User, title: str) -> Todo: ...
    def send_email(self, to: str, subject: str) -> None: ...
```

### 2. Return Domain Objects

```python
# ✅ GOOD - Returns domain object
def get_user(self, user_id: int) -> User:
    return User.objects.get(id=user_id)

# ❌ BAD - Returns dictionary
def get_user(self, user_id: int) -> dict:
    user = User.objects.get(id=user_id)
    return {"id": user.id, "email": user.email}
```

### 3. Use Transactions for Writes

```python
from django.db import transaction

class OrderService:
    @transaction.atomic
    def create_order(self, user: User, items: list[Item]) -> Order:
        order = Order.objects.create(user=user)
        for item in items:
            OrderItem.objects.create(order=order, item=item)
        return order
```

### 4. Keep Services Stateless

```python
# ✅ GOOD - Stateless service
class UserService:
    def get_user(self, user_id: int) -> User:
        return User.objects.get(id=user_id)

# ❌ BAD - Stateful service
class UserService:
    def __init__(self):
        self._current_user = None  # Don't store state!

    def set_user(self, user: User) -> None:
        self._current_user = user
```

## Acceptable Exceptions

Direct model imports are acceptable only in:

| Location | Reason |
|----------|--------|
| Django Admin | Admin requires model registration |
| Migrations | Auto-generated by Django |
| Tests | Creating test data with factories |
| Services | Services are the ORM interface |

## Data Flow

```
HTTP Request
     │
     ▼
┌────────────────┐
│   Controller   │  Validates input, calls service
└───────┬────────┘
        │
        ▼
┌────────────────┐
│    Service     │  Business logic, ORM queries
└───────┬────────┘
        │
        ▼
┌────────────────┐
│     Model      │  Data persistence
└───────┬────────┘
        │
        ▼
    Database
```

## Testing Benefits

With the service layer, testing is straightforward:

```python
def test_create_user(container: Container) -> None:
    # Mock the service
    mock_service = MagicMock(spec=UserService)
    mock_service.create_user.return_value = User(id=1, email="test@example.com")

    # Override in container
    container.register(UserService, instance=mock_service)

    # Test controller without touching database
    test_client = container.resolve(TestClientFactory)()
    response = test_client.post("/v1/users/", json={"email": "test@example.com"})

    assert response.status_code == 200
    mock_service.create_user.assert_called_once()
```

## Related Concepts

- [IoC Container](ioc-container.md) - How services are injected
- [Controller Pattern](controller-pattern.md) - How controllers use services
