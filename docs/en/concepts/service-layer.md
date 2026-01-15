# Service Layer

The Service Layer is the most important architectural pattern in this template. It enforces a strict boundary between your delivery mechanisms (HTTP API, Telegram bot, Celery tasks) and your business logic.

## The Golden Rule

```
Controller --> Service --> Model

Controllers NEVER import or use Models directly.
```

This rule is non-negotiable. Every database operation must go through a service.

## Why This Matters

### 1. Testability

When controllers depend only on services, you can mock the entire data layer in tests:

```python
def test_user_creation(container: Container) -> None:
    mock_service = MagicMock()
    mock_service.create_user.return_value = User(id=1, username="test")

    container.register(UserService, instance=mock_service)
    # Now all controllers use the mock
```

### 2. Reusability

The same service works across all entry points:

```python
# HTTP API controller uses UserService
class UserController(Controller):
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

# Telegram bot controller uses the same UserService
class CommandsController(AsyncController):
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

# Celery task uses the same UserService
class UserCleanupController(Controller):
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service
```

### 3. Maintainability

Changes to database schema or ORM queries are isolated to services. Controllers don't need to change when you:

- Optimize a query
- Add caching
- Change the database structure
- Add validation logic

### 4. Clear Boundaries

The architecture makes responsibilities explicit:

| Layer | Responsibility |
|-------|----------------|
| Controller | HTTP/Bot/Task concerns, request validation, response formatting |
| Service | Business logic, database operations, domain rules |
| Model | Data structure, database schema |

## Correct Pattern

```python
# core/user/services.py
from core.user.models import User

class UserService:
    def get_user_by_username_and_password(
        self,
        username: str,
        password: str,
    ) -> User | None:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        if not user.check_password(password):
            return None

        return user

    def create_user(
        self,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
    ) -> User:
        return User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
```

```python
# delivery/http/user/controllers.py
from core.user.services import UserService  # Import service, NOT model

class UserController(Controller):
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    def create_user(
        self,
        request: HttpRequest,
        request_body: CreateUserRequestSchema,
    ) -> UserSchema:
        user = self._user_service.create_user(
            username=request_body.username,
            email=str(request_body.email),
            first_name=request_body.first_name,
            last_name=request_body.last_name,
            password=request_body.password,
        )
        return UserSchema.model_validate(user, from_attributes=True)
```

## Incorrect Pattern

!!! danger "Never Do This"
    Direct model imports in controllers violate the architecture.

```python
# WRONG - Direct model import in controller
from core.user.models import User  # NEVER import models in controllers

class UserController(Controller):
    def create_user(
        self,
        request: HttpRequest,
        request_body: CreateUserRequestSchema,
    ) -> UserSchema:
        # WRONG - Direct ORM access
        user = User.objects.create_user(
            username=request_body.username,
            email=str(request_body.email),
        )
        return UserSchema.model_validate(user, from_attributes=True)
```

## What Goes in a Service

Services should contain:

### Database Operations

All ORM queries, creates, updates, and deletes:

```python
class ItemService:
    def list_items(self) -> list[Item]:
        return list(Item.objects.all())

    def get_item_by_id(self, item_id: int) -> Item:
        try:
            return Item.objects.get(id=item_id)
        except Item.DoesNotExist as e:
            raise ItemNotFoundError(f"Item {item_id} not found") from e
```

### Business Logic

Domain rules and validations:

```python
class UserService:
    def is_valid_password(
        self,
        password: str,
        *,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
    ) -> bool:
        """Validate the strength of the given password."""
        try:
            validate_password(
                password=password,
                user=User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                ),
            )
        except ValidationError:
            return False
        return True
```

### Transactions

Atomic operations that span multiple database changes:

```python
from django.db import transaction

class RefreshSessionService:
    @transaction.atomic
    def rotate_refresh_token(self, refresh_token: str) -> RefreshSessionResult:
        session = self._get_refresh_session(refresh_token)

        new_refresh_token = self._issue_refresh_token()
        session.refresh_token_hash = self._hash_refresh_token(new_refresh_token)
        session.rotation_counter += 1
        session.last_used_at = timezone.now()
        session.save(
            update_fields=[
                "refresh_token_hash",
                "rotation_counter",
                "last_used_at",
            ],
        )

        return RefreshSessionResult(
            refresh_token=new_refresh_token,
            session=session,
        )
```

## What Stays Out of Services

Services should NOT contain:

| Concern | Where It Belongs |
|---------|------------------|
| HTTP status codes | Controller |
| Request/response schemas | Controller |
| Route definitions | Controller |
| Authentication decorators | Controller |
| Serialization to JSON | Controller |
| Rate limiting | Controller |

## Domain Exceptions

Services communicate errors through domain-specific exceptions that inherit from `ApplicationError`:

```python
# core/exceptions.py
class ApplicationError(Exception):
    """Base class for all application-specific exceptions."""

# core/health/services.py
from core.exceptions import ApplicationError

class HealthCheckError(ApplicationError):
    pass

class HealthService:
    def check_system_health(self) -> None:
        """Check the health of the system components.

        Raises:
            HealthCheckError: If any component is not healthy.
        """
        try:
            Session.objects.first()
        except Exception as e:
            logger.exception("Health check failed: database is not reachable")
            raise HealthCheckError from e
```

!!! tip "Document Exceptions"
    Always include a `Raises:` section in docstrings when a method can raise domain exceptions. This helps controllers know what errors to handle.

### Exception Hierarchy

```
ApplicationError (base)
    |
    +-- HealthCheckError
    |
    +-- RefreshTokenError
    |       |
    |       +-- InvalidRefreshTokenError
    |       |
    |       +-- ExpiredRefreshTokenError
    |
    +-- ItemNotFoundError
```

Controllers then handle these exceptions and convert them to appropriate responses:

```python
class HealthController(Controller):
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

## Service Registration

Services are registered in the IoC container as singletons:

```python
# ioc/registries/core.py
from punq import Container, Scope
from core.user.services import UserService
from core.health.services import HealthService

def _register_services(container: Container) -> None:
    container.register(HealthService, scope=Scope.singleton)
    container.register(UserService, scope=Scope.singleton)
```

## Acceptable Exceptions

Direct model imports are acceptable ONLY in:

| Location | Reason |
|----------|--------|
| `admin.py` | Django Admin requires model registration |
| Migrations | Auto-generated by Django |
| Tests | Creating test data with factories |
| Services | Services encapsulate model access |

## Summary

The Service Layer pattern provides:

1. **Clear separation** between delivery and business logic
2. **Reusable business logic** across HTTP, Celery, and Telegram
3. **Testable architecture** through dependency injection
4. **Maintainable code** with isolated concerns
5. **Domain exceptions** for meaningful error handling

Follow the Golden Rule: `Controller --> Service --> Model`, and your codebase will remain clean, testable, and maintainable as it grows.
