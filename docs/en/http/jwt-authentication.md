# JWT Authentication

Token-based authentication using JSON Web Tokens (JWT).

## Overview

The authentication flow:

```
1. User submits credentials
2. Server validates and issues access + refresh tokens
3. Client includes access token in requests
4. Server validates token and identifies user
5. When access token expires, use refresh token to get new pair
```

## JWT Service

The `JWTService` handles token operations:

```python
# src/infrastructure/jwt/services.py

class JWTServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15

    @property
    def access_token_expire(self) -> timedelta:
        return timedelta(minutes=self.access_token_expire_minutes)


class JWTService:
    EXPIRED_SIGNATURE_ERROR = jwt.ExpiredSignatureError
    INVALID_TOKEN_ERROR = jwt.InvalidTokenError

    def __init__(self, settings: JWTServiceSettings) -> None:
        self._settings = settings

    def issue_access_token(
        self,
        user_id: Any,
        **payload_kwargs: Any,
    ) -> str:
        iat = datetime.now(tz=UTC)
        payload = {
            "sub": str(user_id),
            "exp": iat + self._settings.access_token_expire,
            "iat": iat,
            "typ": "at+jwt",
            **payload_kwargs,
        }

        return jwt.encode(
            payload=payload,
            key=self._settings.secret_key.get_secret_value(),
            algorithm=self._settings.algorithm,
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(
            jwt=token,
            key=self._settings.secret_key.get_secret_value(),
            algorithms=[self._settings.algorithm],
        )
```

## JWT Authentication Handler

The `JWTAuth` class integrates with Django-Ninja:

```python
# src/infrastructure/django/auth.py

class JWTAuth(HttpBearer):
    def __init__(self, jwt_service: JWTService) -> None:
        super().__init__()
        self._jwt_service = jwt_service
        self._user_model = get_user_model()

    def authenticate(
        self,
        request: HttpRequest,
        token: str,
    ) -> AbstractBaseUser | None:
        payload = self._get_token_payload(token=token)
        request.jwt_payload = payload

        user_id = payload.get("sub")
        if user_id is None:
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Token payload missing 'sub' field",
            )

        try:
            user = self._user_model.objects.get(id=user_id)
        except self._user_model.DoesNotExist as e:
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="User not found",
            ) from e

        request.user = user
        return user

    def _get_token_payload(self, token: str) -> dict[str, Any]:
        try:
            return self._jwt_service.decode_token(token=token)
        except self._jwt_service.EXPIRED_SIGNATURE_ERROR as e:
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Token has expired",
            ) from e
        except self._jwt_service.INVALID_TOKEN_ERROR as e:
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Invalid token",
            ) from e
```

## Using Authentication in Controllers

### Inject JWTAuth

```python
class UserController(Controller):
    def __init__(self, auth: JWTAuth) -> None:
        self._auth = auth
```

### Protect Routes

```python
def register(self, registry: Router) -> None:
    # Public endpoint
    registry.add_api_operation(
        path="/v1/users/",
        methods=["POST"],
        view_func=self.create_user,
        auth=None,
    )

    # Protected endpoint
    registry.add_api_operation(
        path="/v1/users/me",
        methods=["GET"],
        view_func=self.get_current_user,
        auth=self._auth,
    )
```

### Access Current User

```python
def get_current_user(self, request: HttpRequest) -> UserSchema:
    # request.user is set by JWTAuth.authenticate()
    return UserSchema.model_validate(request.user, from_attributes=True)
```

### Access JWT Payload

```python
def some_handler(self, request: HttpRequest) -> dict:
    # Access the decoded JWT payload
    payload = request.jwt_payload
    issued_at = payload["iat"]
    expires_at = payload["exp"]
    return {"user_id": payload["sub"]}
```

## Token Endpoint

The `UserTokenController` issues tokens:

```python
class UserTokenController(Controller):
    def __init__(
        self,
        jwt_service: JWTService,
        refresh_token_service: RefreshSessionService,
        jwt_auth: JWTAuth,
    ) -> None:
        self._jwt_service = jwt_service
        self._refresh_token_service = refresh_token_service
        self._jwt_auth = jwt_auth

    def issue_user_token(
        self,
        request: HttpRequest,
        body: IssueTokenRequestSchema,
    ) -> TokenResponseSchema:
        user = User.objects.filter(username=body.username).first()
        if user is None or not user.check_password(body.password):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Invalid username or password",
            )

        access_token = self._jwt_service.issue_access_token(user_id=user.pk)
        refresh_session = self._refresh_token_service.create_refresh_session(
            request=request,
            user=user,
        )

        return TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_session.refresh_token,
        )
```

## Configuration

### Environment Variables

```bash
JWT_SECRET_KEY=your-secret-key    # Required
JWT_ALGORITHM=HS256               # Default: HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15  # Default: 15
```

### Supported Algorithms

- `HS256` — HMAC with SHA-256 (symmetric)
- `HS384` — HMAC with SHA-384 (symmetric)
- `HS512` — HMAC with SHA-512 (symmetric)

!!! note "Asymmetric algorithms"
    For RS256/ES256, you'd need to modify the service to use public/private key pairs.

## Token Structure

Access tokens contain:

```json
{
  "sub": "123",                    // User ID
  "exp": 1700000000,               // Expiration timestamp
  "iat": 1699999100,               // Issued at timestamp
  "typ": "at+jwt"                  // Token type
}
```

## Client Usage

### Getting Tokens

```bash
curl -X POST http://localhost:8000/v1/users/me/token \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

### Using Access Token

```bash
curl http://localhost:8000/v1/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiI..."
```

## Error Responses

| Status | Message | Cause |
|--------|---------|-------|
| 401 | Token has expired | Access token TTL exceeded |
| 401 | Invalid token | Malformed or tampered token |
| 401 | User not found | User deleted after token issued |
| 401 | Invalid username or password | Wrong credentials |

## Security Considerations

1. **Short TTL** — Access tokens should expire quickly (15 minutes default)
2. **Secure Secret** — Use a strong, unique secret key
3. **HTTPS Only** — Always use TLS in production
4. **Token Storage** — Clients should store tokens securely

## Related Topics

- [Refresh Tokens](refresh-tokens.md) — Token refresh flow
- [Error Handling](error-handling.md) — Exception handling
- [Production Configuration](../configuration/production.md) — Security settings
