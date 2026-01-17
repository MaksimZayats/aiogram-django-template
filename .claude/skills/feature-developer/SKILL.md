---
name: feature-developer
description: Implements new features, domains, and API endpoints.
version: 1.0.0
---

# Feature Developer Skill

This skill guides you through adding new features to this codebase following established architectural patterns.

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
class <Domain>Service:
    def get_by_id(self, id: int) -> <Model>: ...
    def list_all(self) -> list[<Model>]: ...
    def create(self, **kwargs) -> <Model>: ...
```

Full template with CRUD operations: See `references/domain-checklist.md` (Step 5)

## Controller Pattern

Controllers handle HTTP, convert exceptions, and delegate to services. **Always use sync methods** - FastAPI runs them in a thread pool automatically.

```python
@dataclass
class <Domain>Controller(Controller):
    _jwt_auth_factory: JWTAuthFactory
    _<domain>_service: <Domain>Service

    def register(self, registry: APIRouter) -> None: ...

    # ✅ Sync handler - FastAPI runs in thread pool via anyio.to_thread
    def get_item(self, request: AuthenticatedRequest, item_id: int) -> <Model>Schema:
        item = self._<domain>_service.get_by_id(item_id)
        return <Model>Schema.model_validate(item, from_attributes=True)

    def handle_exception(self, exception: Exception) -> Any: ...
```

**Thread pool parallelism:** Configure via `ANYIO_THREAD_LIMITER_TOKENS` env var (default: 40).
See `src/infrastructure/anyio/configurator.py`.

Full template with schemas and routes: See `references/controller-patterns.md`

## IoC Registration

```python
# Service: src/ioc/registries/core.py
container.register(<Domain>Service, scope=Scope.singleton)

# Controller: src/ioc/registries/delivery.py
container.register(<Domain>Controller, scope=Scope.singleton)
```

Full FastAPIFactory update: See `references/domain-checklist.md` (Step 10)

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
| Using async handlers with sync services | Blocks the event loop | Use sync handlers (FastAPI runs in thread pool) |
| Skipping IoC registration | Dependencies won't resolve | Always register services and controllers |
| Using generic exceptions | Hard to handle specifically | Create domain-specific exceptions |
| Forgetting `@transaction.atomic` | Multi-step operations can fail partially | Wrap create/update/delete in transactions |
| Hardcoding in controllers | Reduces testability | Inject via IoC constructor |

## Reference Documentation

For detailed examples and edge cases, read:
- `references/domain-checklist.md` - Complete step-by-step checklist
- `references/controller-patterns.md` - HTTP and Celery controller examples
- `references/testing-new-features.md` - How to test your new domain

## Project Documentation

Always consult the project's documentation:
- Complete checklist: `docs/en/how-to/add-new-domain.md`
- Service layer concept: `docs/en/concepts/service-layer.md`
- Controller pattern: `docs/en/concepts/controller-pattern.md`
- IoC container: `docs/en/concepts/ioc-container.md`
- Tutorial example: `docs/en/tutorial/` (Todo List feature)
