# HTTP API

Build REST APIs with Django-Ninja and the controller pattern.

## Overview

The HTTP API uses [Django-Ninja](https://django-ninja.dev/) for fast, type-safe REST endpoints with automatic OpenAPI documentation.

## Architecture

```
HTTP Request
     │
     ▼
┌─────────────┐
│  NinjaAPI   │
│  (Router)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Controller  │
│  (Handler)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Services   │
│ (via IoC)   │
└─────────────┘
```

## Topics

<div class="grid cards" markdown>

-   **Controllers**

    ---

    HTTP controller pattern with route registration and exception handling.

    [:octicons-arrow-right-24: Learn More](controllers.md)

-   **JWT Authentication**

    ---

    Token-based authentication with Bearer scheme.

    [:octicons-arrow-right-24: Learn More](jwt-authentication.md)

-   **Refresh Tokens**

    ---

    Secure token refresh flow with rotation.

    [:octicons-arrow-right-24: Learn More](refresh-tokens.md)

-   **Error Handling**

    ---

    Custom exception handling and HTTP error responses.

    [:octicons-arrow-right-24: Learn More](error-handling.md)

</div>

## Quick Start

### Access API Documentation

After starting the server, visit:

- **Interactive Docs** — `http://localhost:8000/docs`
- **OpenAPI Schema** — `http://localhost:8000/openapi.json`

### Available Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/health` | Health check |
| `POST` | `/v1/users/` | Create user |
| `GET` | `/v1/users/me` | Get current user (auth required) |
| `POST` | `/v1/users/me/token` | Issue tokens |
| `POST` | `/v1/users/me/token/refresh` | Refresh tokens |
| `POST` | `/v1/users/me/token/revoke` | Revoke refresh token (auth required) |

## Example: Making Requests

### Create a User

```bash
curl -X POST http://localhost:8000/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "first_name": "Test",
    "last_name": "User",
    "password": "SecurePassword123!"
  }'
```

### Get Access Token

```bash
curl -X POST http://localhost:8000/v1/users/me/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePassword123!"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "dG9rZW4tc2VjcmV0..."
}
```

### Access Protected Endpoint

```bash
curl http://localhost:8000/v1/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Related Topics

- [Your First API Endpoint](../tutorials/first-api-endpoint.md) — Tutorial
- [Controller Pattern](../concepts/controller-pattern.md) — Architecture
- [HTTP API Tests](../testing/http-tests.md) — Testing
