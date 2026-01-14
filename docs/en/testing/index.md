# Testing

Test patterns and factories for HTTP API and Celery tasks.

## Overview

The testing architecture provides:

- **Test Factories** — Per-test isolation with IoC override capability
- **HTTP API Tests** — Django-Ninja test client integration
- **Celery Tests** — In-process worker for task testing
- **IoC Mocking** — Dependency injection for test doubles
- **Django Settings** — Overriding Django settings for test isolation

## Test Stack

| Tool | Purpose |
|------|---------|
| pytest | Test runner |
| pytest-django | Django integration |
| ninja.testing | HTTP API client |
| celery.contrib.testing | Celery worker testing |
| punq | IoC container |

## Topics

<div class="grid cards" markdown>

-   **Test Factories**

    ---

    Creating test clients with IoC container isolation.

    [→ Learn More](test-factories.md)

-   **HTTP API Tests**

    ---

    Testing REST endpoints with test client.

    [→ Learn More](http-tests.md)

-   **Celery Task Tests**

    ---

    Testing background tasks with in-process worker.

    [→ Learn More](celery-tests.md)

-   **Mocking IoC Dependencies**

    ---

    Overriding dependencies for test isolation.

    [→ Learn More](mocking-ioc.md)

-   **Django Settings Overrides**

    ---

    Overriding Django settings for test isolation.

    [→ Learn More](django-settings.md)

</div>

## Running Tests

```bash
make test
```

This runs pytest with 80% coverage requirement.

### Test Configuration

Tests use `.env.test` for configuration:

```bash
# .env.test
DJANGO_SECRET_KEY=test-secret
JWT_SECRET_KEY=test-jwt-secret
DATABASE_URL=postgres://postgres:test@localhost:5432/test_db
REDIS_URL=redis://localhost:6379/1
```

## Test Structure

```
tests/
├── conftest.py              # Root pytest configuration
└── integration/
    ├── conftest.py          # Integration fixtures
    ├── factories.py         # Test factories
    └── http/
        └── test_user.py     # HTTP endpoint tests
```

## Quick Example

```python
import pytest
from ninja.testing import TestClient

from tests.integration.factories import TestClientFactory


@pytest.mark.django_db(transaction=True)
def test_health_endpoint(test_client_factory: TestClientFactory) -> None:
    client = test_client_factory()

    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

## Fixtures

### Core Fixtures

```python
@pytest.fixture(scope="function")
def container() -> Container:
    """Fresh IoC container per test."""
    return get_container()


@pytest.fixture(scope="function")
def test_client_factory(container: Container) -> TestClientFactory:
    """Test client factory with container isolation."""
    return container.resolve(TestClientFactory)


@pytest.fixture(scope="function")
def test_client(test_client_factory: TestClientFactory) -> TestClient:
    """Pre-created test client."""
    return test_client_factory()
```

### User Fixtures

```python
@pytest.fixture(scope="function")
def user_factory(transactional_db, container: Container) -> TestUserFactory:
    """Factory for creating test users."""
    return container.resolve(TestUserFactory)


@pytest.fixture
def user(user_factory: TestUserFactory) -> User:
    """Pre-created test user."""
    return user_factory()
```

## Coverage Requirements

The project requires 80% test coverage:

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=80"
```
