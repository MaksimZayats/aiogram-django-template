---
name: feature-developer
description: This skill should be used when the user asks to "add a new feature", "create an endpoint", "implement CRUD", "add a new domain", "create a service", "add API endpoint", "build a new module", "implement functionality", or mentions adding new business logic, creating controllers, or extending the application.
version: 1.0.0
---

# Feature Developer Skill

This skill guides you through adding new features to the aiogram-django-template codebase following established architectural patterns.

## The Golden Rule

**NEVER violate this architecture:**

```
Controller -> Service -> Model

Controllers NEVER import models directly.
```

Before writing any code, understand this data flow:

```
HTTP Request -> Controller -> Service -> Model -> Database
                    |             |
               Pydantic      Domain
               Schemas     Exceptions
```

## Quick Reference: File Locations

| Component | Location | Registration |
|-----------|----------|--------------|
| Model | `src/core/<domain>/models.py` | Django app in settings |
| Service | `src/core/<domain>/services.py` | `src/ioc/registries/core.py` |
| HTTP Controller | `src/delivery/http/<domain>/controllers.py` | `src/ioc/registries/delivery.py` |
| Celery Task | `src/delivery/tasks/tasks/<task>.py` | `src/ioc/registries/delivery.py` |
| Bot Handler | `src/delivery/bot/controllers/<handler>.py` | `src/ioc/registries/delivery.py` |

## Workflow: Adding a New Domain

Follow this 12-step checklist. Each step is detailed in `references/domain-checklist.md`.

### Phase 1: Core Layer (Business Logic)

1. **Create domain directory**: `mkdir -p src/core/<domain>`
2. **Create Django app config**: `src/core/<domain>/apps.py`
3. **Register in installed_apps**: Edit `src/core/configs/core.py`
4. **Create model**: `src/core/<domain>/models.py`
5. **Create service with exceptions**: `src/core/<domain>/services.py`
6. **Register service in IoC**: Edit `src/ioc/registries/core.py`

### Phase 2: Delivery Layer (External Interface)

7. **Create controller directory**: `mkdir -p src/delivery/http/<domain>`
8. **Create controller with schemas**: `src/delivery/http/<domain>/controllers.py`
9. **Register controller in IoC**: Edit `src/ioc/registries/delivery.py`
10. **Update API factory**: Edit `src/delivery/http/factories.py`

### Phase 3: Finalization

11. **Create and run migrations**: `make makemigrations && make migrate`
12. **Write tests**: `tests/integration/http/<domain>/`

## Service Layer Pattern

Services encapsulate ALL database operations. Controllers ONLY call service methods.

```python
# src/core/<domain>/services.py
from django.db import transaction
from core.<domain>.models import <Model>


class <Domain>NotFoundError(Exception):
    """Domain-specific exception."""


class <Domain>Service:
    def get_by_id(self, id: int) -> <Model>:
        try:
            return <Model>.objects.get(id=id)
        except <Model>.DoesNotExist as e:
            raise <Domain>NotFoundError(f"<Domain> {id} not found") from e

    def list_all(self) -> list[<Model>]:
        return list(<Model>.objects.all())

    @transaction.atomic
    def create(self, **kwargs) -> <Model>:
        return <Model>.objects.create(**kwargs)
```

## Controller Pattern

Controllers handle HTTP, convert exceptions, and delegate to services.

```python
# src/delivery/http/<domain>/controllers.py
from http import HTTPStatus
from typing import Any

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from core.<domain>.services import <Domain>Service, <Domain>NotFoundError
from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import AuthenticatedHttpRequest, JWTAuth


class <Model>Schema(BaseModel):
    id: int
    # ... fields matching model


class <Domain>Controller(Controller):
    def __init__(
        self,
        jwt_auth: JWTAuth,
        <domain>_service: <Domain>Service,
    ) -> None:
        self._jwt_auth = jwt_auth
        self._<domain>_service = <domain>_service

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/<domain>s/",
            methods=["GET"],
            view_func=self.list_<domain>s,
            auth=self._jwt_auth,
        )

    def list_<domain>s(
        self,
        request: AuthenticatedHttpRequest,
    ) -> list[<Model>Schema]:
        items = self._<domain>_service.list_all()
        return [<Model>Schema.model_validate(i, from_attributes=True) for i in items]

    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, <Domain>NotFoundError):
            raise HttpError(
                status_code=HTTPStatus.NOT_FOUND,
                message=str(exception),
            ) from exception
        return super().handle_exception(exception)
```

## IoC Registration Patterns

### Registering a Service

```python
# src/ioc/registries/core.py
from punq import Container, Scope
from core.<domain>.services import <Domain>Service

def _register_services(container: Container) -> None:
    # ... existing registrations
    container.register(<Domain>Service, scope=Scope.singleton)
```

### Registering a Controller

```python
# src/ioc/registries/delivery.py
from punq import Container, Scope
from delivery.http.<domain>.controllers import <Domain>Controller

def _register_http_controllers(container: Container) -> None:
    # ... existing registrations
    container.register(<Domain>Controller, scope=Scope.singleton)
```

### Updating NinjaAPIFactory

```python
# src/delivery/http/factories.py
from delivery.http.<domain>.controllers import <Domain>Controller

class NinjaAPIFactory:
    def __init__(
        self,
        # ... existing dependencies
        <domain>_controller: <Domain>Controller,  # Add this
    ) -> None:
        # ... existing assignments
        self._<domain>_controller = <domain>_controller

    def __call__(self, urls_namespace: str | None = None) -> NinjaAPI:
        # ... existing code

        # Add router for new domain
        <domain>_router = Router(tags=["<domain>s"])
        ninja_api.add_router("/", <domain>_router)
        self._<domain>_controller.register(registry=<domain>_router)

        return ninja_api
```

## Validation: After Implementation

Run these commands to verify your implementation:

```bash
# 1. Format and lint
make format
make lint

# 2. Run tests with coverage
make test

# 3. Start dev server and test manually
make dev
```

## Common Mistakes to Avoid

| Mistake | Why It's Wrong | Correct Approach |
|---------|---------------|------------------|
| Importing models in controllers | Violates architecture | Import and use services only |
| Skipping IoC registration | Dependencies won't resolve | Always register services and controllers |
| Using generic exceptions | Hard to handle specifically | Create domain-specific exceptions |
| Forgetting `@transaction.atomic` | Multi-step operations can fail partially | Wrap create/update/delete in transactions |
| Hardcoding in controllers | Reduces testability | Inject via IoC constructor |

## Reference Documentation

For detailed examples and edge cases, read:
- `references/domain-checklist.md` - Complete step-by-step checklist
- `references/controller-patterns.md` - HTTP, Celery, and Bot controller examples
- `references/testing-new-features.md` - How to test your new domain

## Project Documentation

Always consult the project's documentation:
- Complete checklist: `docs/en/how-to/add-new-domain.md`
- Service layer concept: `docs/en/concepts/service-layer.md`
- Controller pattern: `docs/en/concepts/controller-pattern.md`
- IoC container: `docs/en/concepts/ioc-container.md`
- Tutorial example: `docs/en/tutorial/` (Todo List feature)
