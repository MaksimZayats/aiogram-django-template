# Concepts

This section explains the architectural patterns and design principles used in the Modern API Template.

## In This Section

| Concept | Description |
|---------|-------------|
| [Service Layer](service-layer.md) | The golden rule: Controller → Service → Model |
| [IoC Container](ioc-container.md) | Dependency injection with punq |
| [Controller Pattern](controller-pattern.md) | Sync and async controllers |
| [Factory Pattern](factory-pattern.md) | Creating complex objects |
| [Pydantic Settings](pydantic-settings.md) | Environment-based configuration |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Entry Points                              │
├───────────────┬───────────────────────┬─────────────────────────┤
│   HTTP API    │     Celery Worker     │     Telegram Bot        │
│ (Django Ninja)│                       │      (aiogram)          │
├───────────────┴───────────────────────┴─────────────────────────┤
│                     Controllers (delivery/)                      │
├─────────────────────────────────────────────────────────────────┤
│                      Services (core/)                            │
├─────────────────────────────────────────────────────────────────┤
│                      Models (core/)                              │
├─────────────────────────────────────────────────────────────────┤
│                   IoC Container (ioc/)                           │
└─────────────────────────────────────────────────────────────────┘
```

## Key Principles

### 1. Strict Layer Separation

Each layer has a clear responsibility:

- **Controllers** - Handle external requests, convert to/from domain objects
- **Services** - Contain business logic, orchestrate database operations
- **Models** - Define data structure and persistence

### 2. Dependency Injection

All dependencies are injected via constructor:

```python
class UserController:
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service
```

This enables:

- **Testability** - Replace dependencies with mocks
- **Flexibility** - Change implementations without modifying consumers
- **Clarity** - Dependencies are explicit

### 3. Single Responsibility

Each component does one thing well:

- A service handles one domain (User, Todo, Health)
- A controller handles one set of related endpoints
- A factory creates one type of object

### 4. Configuration via Environment

All configuration comes from environment variables:

```python
class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_")
    secret_key: SecretStr
```

This enables:

- **Security** - Secrets never in code
- **Flexibility** - Same code in all environments
- **12-Factor** - Industry best practices

## How Patterns Connect

```
Environment Variables
        │
        ▼
┌───────────────┐
│ Pydantic      │◄──── Configuration
│ Settings      │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ IoC Container │◄──── Dependency Resolution
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Factories     │◄──── Object Creation
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Controllers   │◄──── Request Handling
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Services      │◄──── Business Logic
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Models        │◄──── Data Persistence
└───────────────┘
```

## Reading Order

For the best understanding, read in this order:

1. [Service Layer](service-layer.md) - The most important pattern
2. [IoC Container](ioc-container.md) - How dependencies are resolved
3. [Controller Pattern](controller-pattern.md) - How requests are handled
4. [Factory Pattern](factory-pattern.md) - How complex objects are created
5. [Pydantic Settings](pydantic-settings.md) - How configuration works
