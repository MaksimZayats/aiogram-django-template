# Test Factories

Creating test clients with IoC container isolation.

## Overview

Test factories extend production factories to enable per-test isolation:

```python
# tests/integration/factories.py

class TestNinjaAPIFactory(NinjaAPIFactory):
    __test__ = False  # Tell pytest this isn't a test

    def __call__(self, urls_namespace: str | None = None) -> NinjaAPI:
        # Always use unique namespace to avoid URL conflicts
        return super().__call__(urls_namespace=str(uuid.uuid7()))
```

## Available Factories

### TestNinjaAPIFactory

Creates NinjaAPI instances with unique namespaces:

```python
class TestNinjaAPIFactory(NinjaAPIFactory):
    __test__ = False

    def __call__(self, urls_namespace: str | None = None) -> NinjaAPI:
        return super().__call__(urls_namespace=str(uuid.uuid7()))
```

Each test gets a unique URL namespace, preventing conflicts.

### TestClientFactory

Creates Django-Ninja test clients:

```python
class TestClientFactory:
    __test__ = False

    def __init__(self, api_factory: TestNinjaAPIFactory) -> None:
        self._api_factory = api_factory

    def __call__(self, **kwargs: Any) -> TestClient:
        return TestClient(self._api_factory(), **kwargs)
```

### TestUserFactory

Creates test users:

```python
class TestUserFactory:
    __test__ = False

    def __init__(self, user_model: type[User]) -> None:
        self._user_model = user_model

    def __call__(
        self,
        username: str = "test_user",
        password: str = "password123",
        email: str = "user@test.com",
    ) -> User:
        return self._user_model.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
```

### TestCeleryWorkerFactory

Creates in-process Celery workers:

```python
class TestCeleryWorkerFactory:
    __test__ = False

    def __init__(self, celery_app_factory: CeleryAppFactory) -> None:
        self._celery_app_factory = celery_app_factory

    def __call__(self) -> AbstractContextManager[WorkController]:
        return worker.start_worker(
            app=self._celery_app_factory(),
            perform_ping_check=False,
        )
```

## IoC Registration

Factories are registered in the test container fixture:

```python
# tests/integration/conftest.py

@pytest.fixture(scope="function")
def container(django_user_model: type[User]) -> Container:
    container = get_container()

    # Register test factories
    container.register(TestNinjaAPIFactory, scope=Scope.singleton)
    container.register(TestClientFactory, scope=Scope.singleton)
    container.register(TestCeleryWorkerFactory, scope=Scope.singleton)
    container.register(type[User], instance=django_user_model)
    container.register(TestUserFactory, scope=Scope.singleton)

    return container
```

## Using Factories in Tests

### Test Client

```python
@pytest.mark.django_db(transaction=True)
def test_create_user(test_client_factory: TestClientFactory) -> None:
    client = test_client_factory()

    response = client.post(
        "/v1/users/",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 200
```

### User Factory

```python
@pytest.mark.django_db(transaction=True)
def test_get_current_user(
    test_client_factory: TestClientFactory,
    user_factory: TestUserFactory,
) -> None:
    user = user_factory(username="testuser", password="password123")
    client = test_client_factory()

    # Get token
    token_response = client.post(
        "/v1/users/me/token",
        json={"username": "testuser", "password": "password123"},
    )
    access_token = token_response.json()["access_token"]

    # Use token
    response = client.get(
        "/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
```

### Celery Worker

```python
def test_ping_task(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
) -> None:
    with celery_worker_factory():
        result = tasks_registry.ping.delay().get(timeout=10)

    assert result == {"result": "pong"}
```

## Function-Scoped Isolation

Fixtures are function-scoped for isolation:

```python
@pytest.fixture(scope="function")
def container() -> Container:
    # Fresh container per test
    return get_container()


@pytest.fixture(scope="function")
def test_client_factory(container: Container) -> TestClientFactory:
    # New factory per test
    return container.resolve(TestClientFactory)
```

This ensures each test can override IoC registrations without affecting other tests.

## Custom Factory Arguments

Pass arguments when creating test objects:

```python
def test_multiple_users(user_factory: TestUserFactory) -> None:
    user1 = user_factory(username="user1", email="user1@test.com")
    user2 = user_factory(username="user2", email="user2@test.com")

    assert user1.pk != user2.pk
```

## `__test__ = False`

Mark factory classes with `__test__ = False` to prevent pytest from treating them as test classes:

```python
class TestUserFactory:
    __test__ = False  # Required!

    # ... factory implementation
```

## Related Topics

- [HTTP API Tests](http-tests.md) — Testing endpoints
- [Celery Task Tests](celery-tests.md) — Testing tasks
- [Mocking IoC Dependencies](mocking-ioc.md) — Dependency overrides
