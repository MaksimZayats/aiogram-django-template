# Refresh Tokens

Secure token refresh flow with rotation and revocation.

## Overview

Refresh tokens provide a way to get new access tokens without re-authenticating:

```
┌─────────┐                      ┌─────────┐
│ Client  │                      │ Server  │
└────┬────┘                      └────┬────┘
     │                                │
     │  POST /token (credentials)     │
     │───────────────────────────────>│
     │  access_token + refresh_token  │
     │<───────────────────────────────│
     │                                │
     │  ... access token expires ...  │
     │                                │
     │  POST /token/refresh           │
     │───────────────────────────────>│
     │  new access_token + new        │
     │  refresh_token (rotated)       │
     │<───────────────────────────────│
```

## Refresh Session Service

The `RefreshSessionService` manages refresh tokens:

```python
# src/infrastructure/django/refresh_sessions/services.py

class RefreshSessionServiceSettings(BaseSettings):
    refresh_token_nbytes: int = 32
    refresh_token_ttl_days: int = 30
    ninja_num_proxies: int = 0


class RefreshSessionService:
    def __init__(
        self,
        settings: RefreshSessionServiceSettings,
        refresh_session_model: type[BaseRefreshSession],
    ) -> None:
        self._settings = settings
        self._refresh_session_model = refresh_session_model

    def create_refresh_session(
        self,
        request: HttpRequest,
        user: AbstractBaseUser,
    ) -> RefreshSessionResult:
        refresh_token = self._issue_refresh_token()
        refresh_token_hash = self._hash_refresh_token(refresh_token)

        session = self._refresh_session_model.objects.create(
            user=user,
            refresh_token_hash=refresh_token_hash,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            ip_address=self._get_ip_address(request),
            expires_at=timezone.now() + self._settings.refresh_token_ttl,
        )

        return RefreshSessionResult(
            refresh_token=refresh_token,
            session=session,
        )

    @transaction.atomic
    def rotate_refresh_token(self, refresh_token: str) -> RefreshSessionResult:
        session = self._get_refresh_session(refresh_token)

        new_refresh_token = self._issue_refresh_token()
        session.refresh_token_hash = self._hash_refresh_token(new_refresh_token)
        session.rotation_counter += 1
        session.last_used_at = timezone.now()
        session.save()

        return RefreshSessionResult(
            refresh_token=new_refresh_token,
            session=session,
        )

    @transaction.atomic
    def revoke_refresh_token(
        self,
        refresh_token: str,
        user: AbstractBaseUser,
    ) -> None:
        session = self._get_refresh_session(refresh_token)
        if session.user.pk != user.pk:
            raise InvalidRefreshTokenError
        session.revoked_at = timezone.now()
        session.save()
```

## Token Storage

Refresh tokens are stored as hashed values:

```python
def _hash_refresh_token(self, refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode()).hexdigest()
```

This ensures that even if the database is compromised, tokens cannot be used.

## Session Model

```python
# src/infrastructure/django/refresh_sessions/models.py

class BaseRefreshSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    refresh_token_hash = models.CharField(max_length=64, unique=True)
    user_agent = models.CharField(max_length=256, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_used_at = models.DateTimeField(null=True)
    rotation_counter = models.PositiveIntegerField(default=0)
    revoked_at = models.DateTimeField(null=True)

    @property
    def is_active(self) -> bool:
        return (
            self.revoked_at is None
            and self.expires_at > timezone.now()
        )

    class Meta:
        abstract = True
```

## API Endpoints

### Issue Tokens

```bash
POST /api/v1/users/me/token
Content-Type: application/json

{
  "username": "user",
  "password": "password"
}
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiI...",
  "refresh_token": "dG9rZW4tc2VjcmV0..."
}
```

### Refresh Tokens

```bash
POST /api/v1/users/me/token/refresh
Content-Type: application/json

{
  "refresh_token": "dG9rZW4tc2VjcmV0..."
}
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiI...",
  "refresh_token": "bmV3LXRva2VuLXNlY3JldC4uLg=="
}
```

!!! warning "Token Rotation"
    Each refresh returns a **new** refresh token. The old token is invalidated.

### Revoke Token

```bash
POST /api/v1/users/me/token/revoke
Authorization: Bearer eyJhbGciOiJIUzI1NiI...
Content-Type: application/json

{
  "refresh_token": "dG9rZW4tc2VjcmV0..."
}
```

## Token Rotation

Each time a refresh token is used:

1. Old token is invalidated
2. New token is issued
3. Rotation counter is incremented
4. Last used timestamp is updated

This provides:

- **Theft Detection** — If a token is used after rotation, it's likely stolen
- **Limited Window** — Stolen tokens have limited lifetime
- **Audit Trail** — Track usage patterns

## Error Handling

The controller handles refresh token errors:

```python
class UserTokenController(Controller):
    def handle_exception(self, exception: Exception) -> NoReturn:
        if isinstance(exception, InvalidRefreshTokenError):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Invalid refresh token",
            ) from exception

        if isinstance(exception, ExpiredRefreshTokenError):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Refresh token expired or revoked",
            ) from exception

        raise exception
```

## Configuration

```bash
# Refresh token settings
REFRESH_TOKEN_NBYTES=32       # Token entropy (bytes)
REFRESH_TOKEN_TTL_DAYS=30     # Token lifetime
NINJA_NUM_PROXIES=0           # Number of trusted proxies (for IP extraction)
```

!!! note "IP Address Extraction"
    The `NINJA_NUM_PROXIES` setting controls how client IPs are extracted from the `X-Forwarded-For` header. See [Rate Limiting](rate-limiting.md#ip-address-extraction) for detailed configuration.

## Security Features

### Hash Storage

Tokens are hashed before storage:

```python
# Stored in database
refresh_token_hash = sha256("actual-token").hexdigest()
```

### IP Tracking

Client IP is recorded for each session using proxy-aware extraction:

```python
ip_address=self._get_ip_address(request)
```

The IP extraction respects the `NINJA_NUM_PROXIES` setting to correctly parse the `X-Forwarded-For` header when behind reverse proxies. See [Rate Limiting - IP Address Extraction](rate-limiting.md#ip-address-extraction) for details.

### User Agent Tracking

User agent is recorded for session identification:

```python
user_agent=request.META.get("HTTP_USER_AGENT", "")
```

### Atomic Operations

Token rotation uses database transactions:

```python
@transaction.atomic
def rotate_refresh_token(self, refresh_token: str) -> RefreshSessionResult:
    # Prevents race conditions
```

## Client Implementation

### Token Storage

```javascript
// Store tokens securely
localStorage.setItem('access_token', response.access_token);
localStorage.setItem('refresh_token', response.refresh_token);
```

### Auto-Refresh

```javascript
async function fetchWithRefresh(url, options) {
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  });

  if (response.status === 401) {
    // Try to refresh
    const refreshResponse = await fetch('/api/v1/users/me/token/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        refresh_token: localStorage.getItem('refresh_token')
      })
    });

    if (refreshResponse.ok) {
      const tokens = await refreshResponse.json();
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);

      // Retry original request
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${tokens.access_token}`
        }
      });
    }
  }

  return response;
}
```

## Related Topics

- [JWT Authentication](jwt-authentication.md) — Access token details
- [Rate Limiting](rate-limiting.md) — Request throttling and IP extraction
- [Error Handling](error-handling.md) — Exception handling
- [Production Configuration](../configuration/production.md) — Security settings
