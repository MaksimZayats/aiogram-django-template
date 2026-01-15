# Secure Endpoints

This guide covers JWT authentication and rate limiting for HTTP endpoints.

## JWT Authentication

### Using JWTAuth

The template provides `JWTAuth` for securing endpoints:

```python
from infrastructure.django.auth import AuthenticatedHttpRequest, JWTAuth


class UserController(Controller):
    def __init__(self, jwt_auth: JWTAuth) -> None:
        self._jwt_auth = jwt_auth

    def register(self, registry: Router) -> None:
        # Protected endpoint
        registry.add_api_operation(
            path="/v1/users/me",
            methods=["GET"],
            view_func=self.get_current_user,
            auth=self._jwt_auth,  # Requires valid JWT
        )

        # Public endpoint
        registry.add_api_operation(
            path="/v1/users/",
            methods=["POST"],
            view_func=self.create_user,
            auth=None,  # No authentication required
        )
```

### AuthenticatedHttpRequest

Use `AuthenticatedHttpRequest` type hint for protected endpoints:

```python
from infrastructure.django.auth import AuthenticatedHttpRequest


def get_current_user(self, request: AuthenticatedHttpRequest) -> UserSchema:
    # request.user is guaranteed to exist and be authenticated
    return UserSchema.model_validate(request.user, from_attributes=True)
```

### Accessing JWT Payload

The JWT payload is available on the request:

```python
def get_current_user(self, request: AuthenticatedHttpRequest) -> UserSchema:
    # Access custom claims from JWT
    payload = request.jwt_payload
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")

    return UserSchema.model_validate(request.user, from_attributes=True)
```

## Generating Tokens

### Issue Access Token

```python
from infrastructure.jwt.services import JWTService


class UserTokenController(Controller):
    def __init__(self, jwt_service: JWTService, user_service: UserService) -> None:
        self._jwt_service = jwt_service
        self._user_service = user_service

    def login(self, request, body: LoginRequestSchema) -> TokenResponseSchema:
        user = self._user_service.get_user_by_username_and_password(
            username=body.username,
            password=body.password,
        )

        if user is None:
            raise HttpError(HTTPStatus.UNAUTHORIZED, "Invalid credentials")

        access_token = self._jwt_service.issue_access_token(user_id=user.id)

        return TokenResponseSchema(access_token=access_token)
```

### Custom Claims

Add custom data to tokens:

```python
access_token = self._jwt_service.issue_access_token(
    user_id=user.id,
    role=user.role,
    permissions=["read", "write"],
)
```

## Rate Limiting

### Built-in Throttles

Django Ninja provides throttling classes:

```python
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

# For anonymous users (rate limited by IP)
registry.add_api_operation(
    path="/v1/public/data",
    methods=["GET"],
    view_func=self.get_public_data,
    auth=None,
    throttle=AnonRateThrottle(rate="60/min"),
)

# For authenticated users (rate limited by user ID)
registry.add_api_operation(
    path="/v1/users/me",
    methods=["GET"],
    view_func=self.get_current_user,
    auth=self._jwt_auth,
    throttle=AuthRateThrottle(rate="30/min"),
)
```

### Rate Format

| Format | Description |
|--------|-------------|
| `"30/min"` | 30 requests per minute |
| `"5/sec"` | 5 requests per second |
| `"1000/hour"` | 1000 requests per hour |
| `"10000/day"` | 10000 requests per day |

### Endpoint-Specific Rates

Different endpoints can have different limits:

```python
def register(self, registry: Router) -> None:
    # High-frequency endpoint
    registry.add_api_operation(
        path="/v1/health",
        methods=["GET"],
        view_func=self.health_check,
        auth=None,
        throttle=AnonRateThrottle(rate="120/min"),
    )

    # Resource-intensive endpoint
    registry.add_api_operation(
        path="/v1/reports/generate",
        methods=["POST"],
        view_func=self.generate_report,
        auth=self._jwt_auth,
        throttle=AuthRateThrottle(rate="5/min"),
    )

    # Login endpoint (prevent brute force)
    registry.add_api_operation(
        path="/v1/users/me/token",
        methods=["POST"],
        view_func=self.login,
        auth=None,
        throttle=AnonRateThrottle(rate="5/min"),
    )
```

### Cache Backend

Rate limiting uses Django's cache backend. In production, this is Redis:

```python
# src/core/configs/core.py
class CacheSettings(BaseSettings):
    @computed_field()
    def caches(self) -> dict[str, Any]:
        return {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": self.redis_settings.redis_url.get_secret_value(),
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                },
            },
        }
```

## Combining Auth and Throttle

Most endpoints use both:

```python
registry.add_api_operation(
    path="/v1/todos/",
    methods=["POST"],
    view_func=self.create_todo,
    auth=self._jwt_auth,
    throttle=AuthRateThrottle(rate="30/min"),
)
```

## Error Responses

### Authentication Errors

| Status | Scenario |
|--------|----------|
| 401 | Missing token, expired token, invalid token |
| 403 | Valid token but insufficient permissions |

### Rate Limit Errors

| Status | Scenario |
|--------|----------|
| 429 | Too many requests |

The response includes a `Retry-After` header indicating when the client can retry.

## Best Practices

### 1. Always Protect Sensitive Endpoints

```python
# ✅ GOOD - User data is protected
registry.add_api_operation(
    path="/v1/users/me",
    methods=["GET"],
    view_func=self.get_current_user,
    auth=self._jwt_auth,
)

# ❌ BAD - User data exposed publicly
registry.add_api_operation(
    path="/v1/users/me",
    methods=["GET"],
    view_func=self.get_current_user,
    auth=None,  # Anyone can access!
)
```

### 2. Rate Limit All Endpoints

```python
# ✅ GOOD - Rate limited
registry.add_api_operation(
    path="/v1/health",
    methods=["GET"],
    view_func=self.health_check,
    auth=None,
    throttle=AnonRateThrottle(rate="120/min"),
)

# ❌ BAD - No rate limit
registry.add_api_operation(
    path="/v1/health",
    methods=["GET"],
    view_func=self.health_check,
    auth=None,
    # No throttle - vulnerable to DoS
)
```

### 3. Lower Limits for Sensitive Operations

```python
# Login - prevent brute force
throttle=AnonRateThrottle(rate="5/min")

# Password reset - prevent abuse
throttle=AnonRateThrottle(rate="3/min")

# Resource creation - prevent spam
throttle=AuthRateThrottle(rate="10/min")
```

### 4. Use Stricter Limits for Anonymous Users

```python
# Anonymous - lower limit
registry.add_api_operation(
    path="/v1/public/search",
    methods=["GET"],
    view_func=self.search,
    auth=None,
    throttle=AnonRateThrottle(rate="30/min"),
)

# Authenticated - higher limit
registry.add_api_operation(
    path="/v1/search",
    methods=["GET"],
    view_func=self.authenticated_search,
    auth=self._jwt_auth,
    throttle=AuthRateThrottle(rate="100/min"),
)
```

## Testing Protected Endpoints

```python
# tests/integration/http/test_auth.py
from http import HTTPStatus

import pytest


@pytest.mark.django_db(transaction=True)
def test_protected_endpoint_requires_auth(
    test_client_factory: TestClientFactory,
) -> None:
    test_client = test_client_factory()  # No auth

    response = test_client.get("/v1/users/me")

    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db(transaction=True)
def test_protected_endpoint_with_valid_token(
    test_client_factory: TestClientFactory,
    user,
) -> None:
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.get("/v1/users/me")

    assert response.status_code == HTTPStatus.OK
```

## Related

- [Controller Pattern](../concepts/controller-pattern.md) - Controller registration
- [Tutorial: HTTP API](../tutorial/03-http-api.md) - Full example
