---
title: Architecture
summary: System architecture and design patterns
order: 3
sidebar_title: Architecture
---

# Architecture

## Overview

This application follows a layered architecture with dependency injection using **punq**.

```
┌─────────────────────────────────────────┐
│              Delivery Layer             │
│    (HTTP API, Telegram Bot, CLI)        │
├─────────────────────────────────────────┤
│            Infrastructure               │
│   (JWT, Auth, Settings, Controllers)    │
├─────────────────────────────────────────┤
│              Core Layer                 │
│    (Business Logic, Domain Models)      │
├─────────────────────────────────────────┤
│           IoC Container                 │
│     (Dependency Injection)              │
└─────────────────────────────────────────┘
```

## IoC Container

The container is configured in `src/ioc/container.py`:

```python
def get_container() -> Container:
    container = Container()
    _register_services(container)      # JWTService, RefreshSessionService
    _register_auth(container)          # JWTAuth
    _register_controllers(container)   # HTTP controllers
    _register_celery(container)        # Task controllers
    return container
```

### Registration Patterns

```python
# Type-based (auto-resolves dependencies)
container.register(UserController, scope=Scope.singleton)

# Factory-based (for settings)
container.register(JWTServiceSettings, factory=lambda: JWTServiceSettings())

# Instance (for abstract types)
container.register(type[BaseRefreshSession], instance=RefreshSession)
```

### Resolution

```python
controller = container.resolve(UserController)
```

## Controller Pattern

All controllers extend `Controller` from `infrastructure/delivery/controllers.py`:

```python
class Controller(ABC):
    @abstractmethod
    def register(self, registry: Any) -> None: ...

    def handle_exception(self, exception: Exception) -> NoReturn:
        raise exception
```

Controllers auto-wrap public methods with exception handling.

### HTTP Controller

```python
class UserController(Controller):
    def __init__(self, jwt_auth: JWTAuth) -> None:
        self._jwt_auth = jwt_auth

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            "/v1/users/me", ["GET"],
            self.get_me,
            auth=self._jwt_auth
        )
```

### Celery Task Controller

```python
class PingTaskController(Controller):
    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.PING)(self.ping)
```
