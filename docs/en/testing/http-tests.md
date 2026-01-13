# HTTP API Tests

Testing REST endpoints with Django-Ninja test client.

## Basic Test Structure

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

## Test Client

### GET Requests

```python
def test_get_users(test_client: TestClient) -> None:
    response = test_client.get("/v1/users/")
    assert response.status_code == 200
```

### POST Requests

```python
def test_create_user(test_client: TestClient) -> None:
    response = test_client.post(
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
    assert response.json()["username"] == "newuser"
```

### PUT/PATCH Requests

```python
def test_update_item(test_client: TestClient) -> None:
    response = test_client.put(
        "/v1/items/1",
        json={"name": "Updated Name"},
    )
    assert response.status_code == 200
```

### DELETE Requests

```python
def test_delete_item(test_client: TestClient) -> None:
    response = test_client.delete("/v1/items/1")
    assert response.status_code == 200
```

## Authentication

### Getting a Token

```python
@pytest.fixture
def auth_token(
    test_client: TestClient,
    user_factory: TestUserFactory,
) -> str:
    user_factory(username="testuser", password="password123")

    response = test_client.post(
        "/v1/users/me/token",
        json={"username": "testuser", "password": "password123"},
    )

    return response.json()["access_token"]
```

### Using the Token

```python
def test_protected_endpoint(
    test_client: TestClient,
    auth_token: str,
) -> None:
    response = test_client.get(
        "/v1/users/me",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
```

### Authenticated Client Fixture

```python
@pytest.fixture
def auth_client(
    test_client_factory: TestClientFactory,
    user_factory: TestUserFactory,
) -> TestClient:
    user = user_factory(username="authuser", password="password123")
    client = test_client_factory()

    # Get token
    response = client.post(
        "/v1/users/me/token",
        json={"username": "authuser", "password": "password123"},
    )
    token = response.json()["access_token"]

    # Return client with default auth header
    return test_client_factory(headers={"Authorization": f"Bearer {token}"})
```

## Testing Error Responses

### Validation Errors

```python
def test_create_user_invalid_email(test_client: TestClient) -> None:
    response = test_client.post(
        "/v1/users/",
        json={
            "email": "not-an-email",
            "username": "user",
            "first_name": "Test",
            "last_name": "User",
            "password": "password123",
        },
    )

    assert response.status_code == 422
    assert "email" in str(response.json())
```

### Authentication Errors

```python
def test_protected_endpoint_no_token(test_client: TestClient) -> None:
    response = test_client.get("/v1/users/me")

    assert response.status_code == 401


def test_protected_endpoint_invalid_token(test_client: TestClient) -> None:
    response = test_client.get(
        "/v1/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]
```

### Not Found Errors

```python
def test_get_nonexistent_item(test_client: TestClient) -> None:
    response = test_client.get("/v1/items/99999")

    assert response.status_code == 404
```

## Database Markers

### Transactional Tests

```python
@pytest.mark.django_db(transaction=True)
def test_create_and_get_user(test_client: TestClient) -> None:
    # Create
    create_response = test_client.post("/v1/users/", json={...})
    user_id = create_response.json()["id"]

    # Get (same transaction)
    get_response = test_client.get(f"/v1/users/{user_id}")
    assert get_response.status_code == 200
```

### Regular DB Access

```python
@pytest.mark.django_db
def test_read_only(test_client: TestClient) -> None:
    # Read operations only
    response = test_client.get("/v1/health")
    assert response.status_code == 200
```

## Complete Test Example

```python
import pytest
from ninja.testing import TestClient

from tests.integration.factories import TestClientFactory, TestUserFactory


class TestUserEndpoints:
    @pytest.mark.django_db(transaction=True)
    def test_create_user(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/v1/users/",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        assert "password" not in data

    @pytest.mark.django_db(transaction=True)
    def test_create_user_duplicate_username(
        self,
        test_client: TestClient,
        user_factory: TestUserFactory,
    ) -> None:
        user_factory(username="existing")

        response = test_client.post(
            "/v1/users/",
            json={
                "email": "new@example.com",
                "username": "existing",
                "first_name": "Test",
                "last_name": "User",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]

    @pytest.mark.django_db(transaction=True)
    def test_get_current_user(
        self,
        test_client: TestClient,
        user_factory: TestUserFactory,
    ) -> None:
        user = user_factory(username="me", password="password123")

        # Get token
        token_response = test_client.post(
            "/v1/users/me/token",
            json={"username": "me", "password": "password123"},
        )
        token = token_response.json()["access_token"]

        # Get user
        response = test_client.get(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["username"] == "me"
```

## Related Topics

- [Test Factories](test-factories.md) — Factory setup
- [Mocking IoC Dependencies](mocking-ioc.md) — Dependency overrides
- [Error Handling](../http/error-handling.md) — Error response formats
