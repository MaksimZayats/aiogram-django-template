# Core Concepts

Understand the architectural patterns used in this template.

## Overview

This template uses several design patterns to achieve clean, testable, and maintainable code:

<div class="grid cards" markdown>

-   **Service Layer Architecture**

    ---

    Controllers use services for all database operations. Never access models directly.

    [→ Learn More](service-layer.md)

-   **IoC Container (punq)**

    ---

    Dependency injection for decoupled, testable components.

    [→ Learn More](ioc-container.md)

-   **Controller Pattern**

    ---

    Consistent interface for HTTP, bot, and task handlers.

    [→ Learn More](controller-pattern.md)

-   **Pydantic Settings**

    ---

    Type-safe configuration with environment variable support.

    [→ Learn More](pydantic-settings.md)

-   **Factory Pattern**

    ---

    Flexible object creation with IoC integration.

    [→ Learn More](factory-pattern.md)

</div>

## How They Work Together

```
┌────────────────────────────────────────────────┐
│              Environment Variables              │
└────────────────────┬───────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────┐
│          Pydantic Settings Classes             │
│  (Type-safe, validated configuration)          │
└────────────────────┬───────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────┐
│             IoC Container (punq)               │
│  (Registers settings, services, controllers)   │
└────────────────────┬───────────────────────────┘
                     │
          ┌──────────┼──────────┐
          │          │          │
          ▼          ▼          ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Factories  │ │ Controllers │ │   Services  │
│ (Create API,│ │  (HTTP,     │ │  (Business  │
│  Bot, etc.) │ │  Bot, Task) │ │   Logic)    │
└─────────────┘ └──────┬──────┘ └──────┬──────┘
                       │               │
                       └───────┬───────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Django Models     │
                    │  (Database Layer)   │
                    └─────────────────────┘

Controllers → Services → Models (NEVER Controllers → Models directly)
```

## Key Principles

### 1. Service Layer Separation

**Controllers must NEVER access Django models directly.** All database operations go through services.

```python
# ✅ Correct: Controller uses service
class UserController(Controller):
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    def get_user(self, request: HttpRequest, user_id: int) -> UserSchema:
        user = self._user_service.get_user_by_id(user_id)
        return UserSchema.model_validate(user, from_attributes=True)

# ❌ Wrong: Direct model access
class UserController(Controller):
    def get_user(self, request: HttpRequest, user_id: int) -> UserSchema:
        user = User.objects.get(id=user_id)  # Never do this!
```

### 2. Dependency Inversion

High-level modules don't depend on low-level modules. Both depend on abstractions (interfaces).

```python
# Controller depends on abstract JWTAuth, not concrete implementation
class UserController(Controller):
    def __init__(self, auth: JWTAuth) -> None:
        self._auth = auth
```

### 3. Single Responsibility

Each class has one reason to change:

- **Settings** — Configuration
- **Services** — Business logic and data access
- **Controllers** — HTTP/Bot/Task handling (no business logic)
- **Factories** — Object creation

### 4. Explicit Dependencies

All dependencies are declared in `__init__`, making them visible and testable:

```python
class RefreshSessionService:
    def __init__(
        self,
        settings: RefreshSessionServiceSettings,
        refresh_session_model: type[BaseRefreshSession],
    ) -> None:
        self._settings = settings
        self._refresh_session_model = refresh_session_model
```

### 5. Interface Segregation

Controllers implement only what they need:

```python
class Controller(ABC):
    @abstractmethod
    def register(self, registry: Any) -> None: ...

    def handle_exception(self, exception: Exception) -> NoReturn:
        raise exception
```
