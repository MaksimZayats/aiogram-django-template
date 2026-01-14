# Rate Limiting

Protect your API from abuse with built-in request throttling.

## Overview

Rate limiting prevents abuse by restricting the number of requests a client can make within a time period. The system uses Django-Ninja's built-in throttling with Redis as the cache backend.

```
HTTP Request
     │
     ▼
┌─────────────┐
│  Throttle   │──── 429 Too Many Requests
│   Check     │
└──────┬──────┘
       │ OK
       ▼
┌─────────────┐
│  Endpoint   │
│  Handler    │
└─────────────┘
```

## How It Works

1. **Request arrives** at a throttled endpoint
2. **Client identification** — IP address (anonymous) or user ID (authenticated)
3. **Counter check** — Redis stores request counts per client
4. **Decision** — Allow request or return HTTP 429

## Throttle Types

### AnonRateThrottle

For unauthenticated endpoints. Identifies clients by IP address.

```python
from ninja.throttling import AnonRateThrottle

registry.add_api_operation(
    path="/v1/users/",
    methods=["POST"],
    view_func=self.create_user,
    auth=None,
    throttle=AnonRateThrottle(rate="30/min"),
)
```

### AuthRateThrottle

For authenticated endpoints. Identifies clients by user ID.

```python
from ninja.throttling import AuthRateThrottle

registry.add_api_operation(
    path="/v1/users/me",
    methods=["GET"],
    view_func=self.get_current_user,
    auth=self._auth,
    throttle=AuthRateThrottle(rate="30/min"),
)
```

## Default Rate Limits

Global defaults are configured in `NinjaSettings`:

| Throttle Scope | Default Rate | Description |
|----------------|--------------|-------------|
| `anon` | 1000/day | Anonymous (unauthenticated) users |
| `auth` | 10000/day | Authenticated users |
| `user` | 10000/day | Per-user operations |

## Per-Endpoint Throttling

Each endpoint can override the default with a specific rate:

### Token Endpoints

```python
# src/delivery/http/user/controllers.py

# Issue tokens - strict limit to prevent brute force
registry.add_api_operation(
    path="/v1/users/me/token",
    methods=["POST"],
    view_func=self.issue_user_token,
    auth=None,
    throttle=AnonRateThrottle(rate="5/min"),
)

# Refresh tokens
registry.add_api_operation(
    path="/v1/users/me/token/refresh",
    methods=["POST"],
    view_func=self.refresh_user_token,
    auth=None,
    throttle=AnonRateThrottle(rate="5/min"),
)

# Revoke tokens
registry.add_api_operation(
    path="/v1/users/me/token/revoke",
    methods=["POST"],
    view_func=self.revoke_refresh_token,
    auth=self._jwt_auth,
    throttle=AuthRateThrottle(rate="5/min"),
)
```

### User Endpoints

```python
# User creation - moderate limit
registry.add_api_operation(
    path="/v1/users/",
    methods=["POST"],
    view_func=self.create_user,
    auth=None,
    throttle=AnonRateThrottle(rate="30/min"),
)

# Get current user - higher limit for authenticated users
registry.add_api_operation(
    path="/v1/users/me",
    methods=["GET"],
    view_func=self.get_current_user,
    auth=self._auth,
    throttle=AuthRateThrottle(rate="30/min"),
)
```

## Rate Format

Rates use the format `"N/period"`:

| Format | Meaning |
|--------|---------|
| `"5/min"` or `"5/m"` | 5 requests per minute |
| `"100/hour"` or `"100/h"` | 100 requests per hour |
| `"1000/day"` or `"1000/d"` | 1000 requests per day |
| `"10/sec"` or `"10/s"` | 10 requests per second |

Valid periods:

| Period | Aliases |
|--------|---------|
| Second | `s`, `sec` |
| Minute | `m`, `min` |
| Hour | `h`, `hour` |
| Day | `d`, `day` |

## IP Address Extraction

For anonymous throttling, accurate client IP detection is critical.

### The Problem with Proxies

When your application is behind a reverse proxy or load balancer:

```
Client (192.168.1.100)
       │
       ▼
┌─────────────┐
│   Nginx     │ ─── Adds X-Forwarded-For: 192.168.1.100
│   Proxy     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    App      │ ─── REMOTE_ADDR = proxy IP (not client!)
└─────────────┘
```

Without proper configuration, all requests appear to come from the proxy IP, breaking rate limiting.

### How num_proxies Works

The `NINJA_NUM_PROXIES` setting tells the application how many proxies to trust:

```python
# src/infrastructure/django/refresh_sessions/services.py

def _get_ip_address(self, request: HttpRequest) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR", None)
    remote_address = request.META.get("REMOTE_ADDR", None)

    # No proxies configured - use direct connection IP
    if self._settings.ninja_num_proxies == 0 or xff is None:
        return remote_address

    # Parse X-Forwarded-For and count from the end
    addresses = xff.split(",")
    client_address = addresses[-min(self._settings.ninja_num_proxies, len(addresses))]
    return client_address.strip()
```

### Configuration Examples

| Deployment | num_proxies | Explanation |
|------------|-------------|-------------|
| Direct (no proxy) | `0` | Use `REMOTE_ADDR` |
| Single proxy (Nginx) | `1` | Trust last entry in X-Forwarded-For |
| Load balancer + proxy | `2` | Trust second-to-last entry |

### X-Forwarded-For Parsing

Given header: `X-Forwarded-For: client, proxy1, proxy2`

| num_proxies | Selected IP | Reason |
|-------------|-------------|--------|
| `0` | REMOTE_ADDR | Header ignored |
| `1` | `proxy2` | Last 1 entry |
| `2` | `proxy1` | Last 2 entries, pick first |
| `3` | `client` | Last 3 entries, pick first |

!!! warning "Security Consideration"
    Setting `num_proxies` too high allows clients to spoof their IP by adding fake entries to `X-Forwarded-For`. Only count proxies you trust and control.

## Cache Backend

Rate limiting requires a cache backend to store request counters. This application uses Redis:

```python
# src/core/configs/core.py

class CacheSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CACHE_")

    default_timeout: int = 300
    redis_settings: RedisSettings = Field(default_factory=RedisSettings)

    @computed_field()
    def caches(self) -> dict[str, Any]:
        return {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": self.redis_settings.redis_url.get_secret_value(),
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                },
                "TIMEOUT": self.default_timeout,
            },
        }
```

!!! note "Why Redis?"
    Redis enables distributed rate limiting across multiple application instances. All instances share the same counter storage, ensuring consistent limits.

## Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `NINJA_NUM_PROXIES` | `int` | `0` | Number of trusted proxies for IP extraction |
| `NINJA_DEFAULT_THROTTLE_RATES` | `dict` | See below | Global throttle rate defaults |
| `REDIS_URL` | `SecretStr` | — | Redis connection URL (required for throttling) |
| `CACHE_DEFAULT_TIMEOUT` | `int` | `300` | Cache timeout in seconds |

### Default Throttle Rates

```python
{
    "auth": "10000/day",
    "user": "10000/day",
    "anon": "1000/day",
}
```

### Example Configuration

```bash
# .env

# Proxy configuration (if behind Nginx, etc.)
NINJA_NUM_PROXIES=1

# Custom throttle rates (optional)
NINJA_DEFAULT_THROTTLE_RATES='{"auth": "5000/day", "user": "5000/day", "anon": "500/day"}'

# Redis for cache backend
REDIS_URL="redis://default:password@localhost:6379/0"
```

## Error Responses

When rate limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: application/json

{
    "detail": "Request was throttled. Expected available in 60 seconds."
}
```

| Header | Description |
|--------|-------------|
| `Retry-After` | Seconds until the client can retry |

## Disabling Throttling

To disable throttling for a specific endpoint:

```python
registry.add_api_operation(
    path="/v1/health",
    methods=["GET"],
    view_func=self.health_check,
    auth=None,
    throttle=None,  # No rate limiting
)
```

## Testing with Rate Limits

When testing throttled endpoints, you may need to account for rate limits:

```python
import pytest
from django.test import Client

def test_rate_limiting(client: Client) -> None:
    # Make requests up to the limit
    for _ in range(5):
        response = client.post("/v1/users/me/token", ...)
        assert response.status_code == 200

    # Next request should be throttled
    response = client.post("/v1/users/me/token", ...)
    assert response.status_code == 429
```

!!! tip "Test Isolation"
    Use a fresh Redis database for tests to avoid rate limit state from previous test runs affecting results.

## Best Practices

### 1. Strict Limits on Sensitive Endpoints

Authentication endpoints should have strict limits to prevent brute force attacks:

```python
throttle=AnonRateThrottle(rate="5/min")  # Login, token issuance
```

### 2. Higher Limits for Authenticated Users

Authenticated users are more trusted:

```python
throttle=AuthRateThrottle(rate="100/min")  # vs 10/min for anon
```

### 3. Configure Proxies Correctly

Incorrect `num_proxies` can either:
- **Too low**: All users share one IP (proxy IP) — everyone gets rate limited together
- **Too high**: Attackers can spoof IPs by manipulating X-Forwarded-For

### 4. Monitor Rate Limit Hits

Track 429 responses in your observability stack to detect abuse patterns.

## Related Topics

- [JWT Authentication](jwt-authentication.md) — Token-based authentication
- [Refresh Tokens](refresh-tokens.md) — Token refresh and IP tracking
- [Production Configuration](../configuration/production.md) — Production security settings
- [Environment Variables](../configuration/environment-variables.md) — All configuration options
