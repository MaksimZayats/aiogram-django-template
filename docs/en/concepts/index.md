# Core Concepts

Understand the architectural patterns used in this template.

## Overview

This template uses several design patterns to achieve clean, testable, and maintainable code:

<div class="grid cards" markdown>

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
┌─────────────┐ ┌─────────┐ ┌─────────────┐
│  Factories  │ │Services │ │ Controllers │
│ (Create API,│ │ (JWT,   │ │  (HTTP,     │
│  Bot, etc.) │ │ Refresh)│ │  Bot, Task) │
└─────────────┘ └─────────┘ └─────────────┘
```

## Key Principles

### 1. Dependency Inversion

High-level modules don't depend on low-level modules. Both depend on abstractions (interfaces).

```python
# Controller depends on abstract JWTAuth, not concrete implementation
class UserController(Controller):
    def __init__(self, auth: JWTAuth) -> None:
        self._auth = auth
```

### 2. Single Responsibility

Each class has one reason to change:

- **Settings** — Configuration
- **Services** — Business logic
- **Controllers** — HTTP/Bot/Task handling
- **Factories** — Object creation

### 3. Explicit Dependencies

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

### 4. Interface Segregation

Controllers implement only what they need:

```python
class Controller(ABC):
    @abstractmethod
    def register(self, registry: Any) -> None: ...

    def handle_exception(self, exception: Exception) -> NoReturn:
        raise exception
```
