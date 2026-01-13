# Mocking IoC Dependencies

Overriding dependencies for test isolation.

## Overview

The function-scoped container fixture enables per-test dependency overrides:

```python
@pytest.fixture(scope="function")
def container() -> Container:
    return get_container()
```

Each test gets a fresh container, allowing overrides without affecting other tests.

## Basic Override Pattern

```python
from unittest.mock import MagicMock


def test_with_mocked_service(container: Container) -> None:
    # Create mock
    mock_service = MagicMock()
    mock_service.process.return_value = {"status": "success"}

    # Override registration
    container.register(ExternalService, instance=mock_service)

    # Resolve dependent components
    controller = container.resolve(MyController)

    # Test - controller now uses mock
    result = controller.do_something()

    assert result["status"] == "success"
    mock_service.process.assert_called_once()
```

## Override Before Factory Resolution

Override dependencies **before** resolving factories:

```python
def test_http_with_mock(
    container: Container,
    test_client_factory: TestClientFactory,
) -> None:
    # 1. Override in container
    mock_service = MagicMock()
    container.register(JWTService, instance=mock_service)

    # 2. Create client (uses overridden container)
    client = test_client_factory()

    # 3. Test endpoint
    response = client.get("/v1/protected")
```

## Common Override Patterns

### Mock a Service

```python
from unittest.mock import MagicMock
from infrastructure.jwt.services import JWTService


def test_with_mock_jwt(container: Container) -> None:
    mock_jwt = MagicMock(spec=JWTService)
    mock_jwt.decode_token.return_value = {"sub": "123"}

    container.register(JWTService, instance=mock_jwt)

    auth = container.resolve(JWTAuth)
    # auth now uses mock_jwt
```

### Replace Settings

```python
from infrastructure.jwt.services import JWTServiceSettings


def test_with_custom_settings(container: Container) -> None:
    custom_settings = JWTServiceSettings(
        secret_key="test-secret",
        algorithm="HS256",
        access_token_expire_minutes=1,
    )

    container.register(JWTServiceSettings, instance=custom_settings)

    service = container.resolve(JWTService)
    # service now uses custom_settings
```

### Provide Stub Implementation

```python
class StubEmailService:
    def __init__(self) -> None:
        self.sent_emails: list[dict] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({
            "to": to,
            "subject": subject,
            "body": body,
        })


def test_email_sending(container: Container) -> None:
    stub_email = StubEmailService()
    container.register(EmailService, instance=stub_email)

    controller = container.resolve(NotificationController)
    controller.notify_user(user_id=1, message="Hello")

    assert len(stub_email.sent_emails) == 1
    assert stub_email.sent_emails[0]["to"] == "user@example.com"
```

## Override with Factory

For complex construction:

```python
def test_with_factory_override(container: Container) -> None:
    def create_mock_service() -> MockService:
        mock = MagicMock()
        mock.configure(special_value=42)
        return mock

    container.register(ExternalService, factory=create_mock_service)

    service = container.resolve(ExternalService)
    assert service.special_value == 42
```

## Testing HTTP Endpoints with Mocks

```python
@pytest.mark.django_db(transaction=True)
def test_endpoint_with_mock_service(
    container: Container,
) -> None:
    # Setup mock
    mock_user_service = MagicMock()
    mock_user_service.get_user.return_value = User(
        id=1,
        username="mocked_user",
    )
    container.register(UserService, instance=mock_user_service)

    # Create factories with overridden container
    api_factory = container.resolve(TestNinjaAPIFactory)
    client = TestClient(api_factory())

    # Test
    response = client.get("/v1/users/1")

    assert response.status_code == 200
    assert response.json()["username"] == "mocked_user"
```

## Testing Celery Tasks with Mocks

```python
def test_task_with_mock_dependency(
    container: Container,
    celery_worker_factory: TestCeleryWorkerFactory,
) -> None:
    # Mock external API
    mock_api = MagicMock()
    mock_api.fetch_data.return_value = {"data": "mocked"}
    container.register(ExternalAPI, instance=mock_api)

    # Get registry with mocked dependencies
    tasks_registry = container.resolve(TasksRegistry)

    with celery_worker_factory():
        result = tasks_registry.sync_data.delay().get(timeout=10)

    assert result["synced"] is True
    mock_api.fetch_data.assert_called_once()
```

## Fixture for Common Mocks

```python
@pytest.fixture
def mock_email_service(container: Container) -> MagicMock:
    mock = MagicMock(spec=EmailService)
    container.register(EmailService, instance=mock)
    return mock


def test_user_registration_sends_email(
    test_client: TestClient,
    mock_email_service: MagicMock,
) -> None:
    response = test_client.post(
        "/v1/users/",
        json={...},
    )

    assert response.status_code == 200
    mock_email_service.send_welcome_email.assert_called_once()
```

## Best Practices

### 1. Override Early

Override before resolving any dependent components:

```python
# Good
container.register(Service, instance=mock)
controller = container.resolve(Controller)

# Bad - controller already created with real service
controller = container.resolve(Controller)
container.register(Service, instance=mock)  # Too late!
```

### 2. Use Specific Mocks

```python
# Good: Specific mock with expected behavior
mock = MagicMock(spec=JWTService)
mock.decode_token.return_value = {"sub": "123"}

# Avoid: Generic mock that accepts anything
mock = MagicMock()
```

### 3. Verify Interactions

```python
# Verify the mock was used correctly
mock_service.process.assert_called_once_with(expected_data)
mock_service.notify.assert_not_called()
```

### 4. Clean Test Fixtures

```python
@pytest.fixture
def authenticated_client(
    container: Container,
    test_client_factory: TestClientFactory,
) -> TestClient:
    """Client with auth bypassed."""
    mock_auth = MagicMock(spec=JWTAuth)
    mock_auth.authenticate.return_value = User(id=1)
    container.register(JWTAuth, instance=mock_auth)

    return test_client_factory()
```

## Related Topics

- [Test Factories](test-factories.md) — Factory setup
- [HTTP API Tests](http-tests.md) — Testing endpoints
- [Celery Task Tests](celery-tests.md) — Testing tasks
- [IoC Container](../concepts/ioc-container.md) — Container details
