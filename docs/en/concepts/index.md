# Architecture Concepts

This section explains the **why** behind the architectural patterns used in this template. Understanding these concepts will help you make informed decisions when extending the application.

!!! info "About This Section"
    These pages follow the [Diataxis framework](https://diataxis.fr/) **Explanation** quadrant. They are understanding-oriented and focus on providing context, background, and reasoning rather than step-by-step instructions.

## Core Concepts

The template is built around five interconnected architectural patterns:

### [Service Layer](service-layer.md)

The Service Layer enforces a strict separation between your delivery mechanisms (HTTP, Celery) and your business logic. This pattern ensures that:

- Controllers never access database models directly
- Business logic remains reusable across different entry points
- Domain exceptions provide meaningful error handling
- Testing becomes straightforward with clear boundaries

### [IoC Container](ioc-container.md)

Inversion of Control (IoC) using **punq** provides automatic dependency injection. The container:

- Resolves dependencies based on type annotations
- Manages component lifecycles (singleton vs transient)
- Enables test-time substitution of any component
- Organizes registrations by architectural layer

### [Controller Pattern](controller-pattern.md)

Controllers provide a unified interface for handling requests across all delivery mechanisms. The pattern includes:

- Automatic exception wrapping for consistent error handling
- Abstract `register()` method for framework integration
- Two variants: `Controller` (sync) and `AsyncController` (async)
- Clear separation of routing from business logic

### [Factory Pattern](factory-pattern.md)

Factories handle complex object construction, especially when:

- Objects require configuration-based initialization
- Caching is needed to avoid repeated construction
- Multiple dependencies must be composed together
- Different configurations are needed for production vs testing

### [Pydantic Settings](pydantic-settings.md)

Configuration management using Pydantic BaseSettings provides:

- Type-safe environment variable loading
- Automatic validation and conversion
- Computed properties for derived values
- Secure handling of sensitive values with `SecretStr`

## Architecture Overview

```
+-------------------+     +-------------------+     +-------------------+
|     Delivery      |     |       Core        |     |  Infrastructure   |
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
|  HTTP Controllers |---->|    Services       |<----|  JWT Service      |
|  Task Controllers |     |    Models         |     |  Auth Middleware  |
|                   |     |    Exceptions     |     |  Settings         |
|                   |     |                   |     |                   |
+-------------------+     +-------------------+     +-------------------+
         |                        ^                        |
         |                        |                        |
         v                        |                        v
+---------------------------------------------------------------+
|                         IoC Container                         |
|   - Registers all components                                  |
|   - Resolves dependencies automatically                       |
|   - Manages singleton/transient lifecycles                    |
+---------------------------------------------------------------+
```

## Data Flow

A typical request flows through the architecture as follows:

```
HTTP Request
     |
     v
+-------------+     +-------------+     +-------------+
| Controller  |---->|   Service   |---->|    Model    |
| (Delivery)  |     |   (Core)    |     |   (Core)    |
+-------------+     +-------------+     +-------------+
     |                    |                   |
     |                    |                   v
     |                    |              +----------+
     |                    +------------->| Database |
     |                                   +----------+
     v
+-------------+
|  Response   |
| (Pydantic)  |
+-------------+
```

## Benefits of This Architecture

| Benefit | How It's Achieved |
|---------|-------------------|
| **Testability** | IoC container allows mocking any dependency |
| **Maintainability** | Clear boundaries between layers |
| **Reusability** | Services work across HTTP and Celery |
| **Type Safety** | Pydantic validates all data flow |
| **Flexibility** | Factories enable environment-specific configuration |

## When to Use Each Pattern

| Scenario | Pattern |
|----------|---------|
| Adding business logic | Service Layer |
| Adding a new API endpoint | Controller Pattern |
| Complex object construction | Factory Pattern |
| Environment configuration | Pydantic Settings |
| Wiring components together | IoC Container |

## Next Steps

Start with [Service Layer](service-layer.md) to understand the most fundamental pattern, then proceed through the other concepts in order.
