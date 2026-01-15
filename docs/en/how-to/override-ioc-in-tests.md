# Override IoC in Tests

This guide shows how to mock dependencies in tests using IoC container overrides.

## The Pattern

1. Get a fresh container from the fixture
2. Register mock/stub instead of real implementation
3. Resolve factories that will use the mock

## Basic Example

```python
from unittest.mock import MagicMock

import pytest
from punq import Container

from core.user.services import UserService
from tests.integration.factories import TestClientFactory


@pytest.mark.django_db(transaction=True)
def test_with_mock_service(container: Container) -> None:
    # 1. Create mock
    mock_service = MagicMock(spec=UserService)
    mock_service.get_user_by_id.return_value = None

    # 2. Override in container
    container.register(UserService, instance=mock_service)

    # 3. Resolve factory (will use mock)
    test_client = container.resolve(TestClientFactory)()

    # 4. Make request
    response = test_client.get("/v1/users/me")

    # 5. Assert mock was called
    mock_service.get_user_by_id.assert_not_called()  # Example assertion
```

## Why This Works

The container fixture is function-scoped, so each test gets a fresh container:

```python
@pytest.fixture(scope="function")
def container() -> Container:
    return get_container()
```

When you register a mock after `get_container()`, it overrides the original registration for that test only.

## Mocking Services

### Return Value

```python
def test_user_found(container: Container) -> None:
    mock_service = MagicMock(spec=UserService)
    mock_user = User(id=1, username="test", email="test@example.com")
    mock_service.get_user_by_id.return_value = mock_user

    container.register(UserService, instance=mock_service)

    test_client = container.resolve(TestClientFactory)()
    response = test_client.get("/v1/users/1")

    assert response.status_code == 200
    assert response.json()["username"] == "test"
```

### Raise Exception

```python
from core.user.services import UserNotFoundError


def test_user_not_found(container: Container) -> None:
    mock_service = MagicMock(spec=UserService)
    mock_service.get_user_by_id.side_effect = UserNotFoundError("User 1 not found")

    container.register(UserService, instance=mock_service)

    test_client = container.resolve(TestClientFactory)()
    response = test_client.get("/v1/users/1")

    assert response.status_code == 404
```

### Multiple Return Values

```python
def test_multiple_calls(container: Container) -> None:
    mock_service = MagicMock(spec=UserService)
    mock_service.get_user_by_id.side_effect = [
        User(id=1, username="first"),
        User(id=2, username="second"),
        UserNotFoundError("Not found"),
    ]

    container.register(UserService, instance=mock_service)
    # First call returns first user, second returns second, third raises
```

## Mocking External Services

```python
from infrastructure.email.services import EmailService


def test_email_sent_on_registration(container: Container) -> None:
    mock_email = MagicMock(spec=EmailService)

    container.register(EmailService, instance=mock_email)

    test_client = container.resolve(TestClientFactory)()
    response = test_client.post(
        "/v1/users/",
        json={"email": "new@example.com", "password": "secure123"},
    )

    assert response.status_code == 200
    mock_email.send_welcome_email.assert_called_once_with("new@example.com")
```

## Mocking Settings

```python
from core.configs.core import ApplicationSettings
from infrastructure.settings.types import Environment


def test_production_behavior(container: Container) -> None:
    mock_settings = MagicMock(spec=ApplicationSettings)
    mock_settings.environment = Environment.PRODUCTION
    mock_settings.debug = False

    container.register(ApplicationSettings, instance=mock_settings)

    # Now code that checks settings.environment will see PRODUCTION
```

## Verifying Calls

### Assert Called

```python
mock_service.create_user.assert_called_once()
mock_service.create_user.assert_called_with(email="test@example.com", password="secret")
```

### Assert Not Called

```python
mock_service.delete_user.assert_not_called()
```

### Assert Call Count

```python
assert mock_service.get_user_by_id.call_count == 3
```

### Inspect Call Arguments

```python
# Get the arguments from the last call
args, kwargs = mock_service.create_user.call_args
assert kwargs["email"] == "test@example.com"

# Get all calls
all_calls = mock_service.create_user.call_args_list
```

## Using Fixtures for Common Mocks

```python
# tests/integration/conftest.py
import pytest
from unittest.mock import MagicMock

from core.user.services import UserService


@pytest.fixture
def mock_user_service() -> MagicMock:
    return MagicMock(spec=UserService)


# tests/integration/http/test_users.py
def test_with_mock(
    container: Container,
    mock_user_service: MagicMock,
) -> None:
    mock_user_service.get_user_by_id.return_value = User(id=1, username="test")
    container.register(UserService, instance=mock_user_service)

    # ...
```

## Partial Mocking (Spy)

To keep real behavior but track calls:

```python
from unittest.mock import create_autospec


def test_with_spy(container: Container) -> None:
    # Get real service
    real_service = container.resolve(UserService)

    # Create spy that wraps real service
    spy_service = create_autospec(real_service, instance=True)
    spy_service.get_user_by_id.side_effect = real_service.get_user_by_id

    container.register(UserService, instance=spy_service)

    # Real method is called, but we can verify
    test_client = container.resolve(TestClientFactory)()
    response = test_client.get("/v1/users/1")

    spy_service.get_user_by_id.assert_called_once_with(1)
```

## Important: Order Matters

Override **before** resolving factories:

```python
# ✅ CORRECT
def test_correct_order(container: Container) -> None:
    # 1. Override first
    container.register(UserService, instance=mock_service)

    # 2. Then resolve
    test_client = container.resolve(TestClientFactory)()


# ❌ WRONG
def test_wrong_order(container: Container) -> None:
    # 1. Resolve first - uses real service!
    test_client = container.resolve(TestClientFactory)()

    # 2. Override too late - factory already has real service
    container.register(UserService, instance=mock_service)
```

## Related

- [IoC Container](../concepts/ioc-container.md) - How the container works
- [Tutorial: Testing](../tutorial/06-testing.md) - Testing with factories
