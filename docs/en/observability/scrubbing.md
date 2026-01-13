# Sensitive Data Scrubbing

Protecting secrets in traces and logs.

## Overview

Logfire automatically scrubs sensitive data from traces to prevent secrets from being exposed.

## Configuration

```python
# src/infrastructure/otel/logfire.py

logfire.configure(
    # ... other settings ...
    scrubbing=ScrubbingOptions(
        extra_patterns=[
            "access_token",
            "refresh_token",
        ],
    ),
)
```

## Default Scrubbed Patterns

Logfire scrubs these by default:

- `password`
- `secret`
- `token`
- `api_key`
- `apikey`
- `auth`
- `credential`
- `private_key`

## Custom Patterns

Add application-specific patterns:

```python
scrubbing=ScrubbingOptions(
    extra_patterns=[
        "access_token",
        "refresh_token",
        "credit_card",
        "ssn",
        "social_security",
    ],
)
```

## How Scrubbing Works

### Before (Raw Data)

```json
{
  "user": "john",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "dG9rZW4tc2VjcmV0LWhlcmU="
}
```

### After (Scrubbed)

```json
{
  "user": "john",
  "access_token": "[REDACTED]",
  "refresh_token": "[REDACTED]"
}
```

## Pattern Matching

Patterns are matched case-insensitively:

```python
extra_patterns=["api_key"]

# All matched:
# api_key
# API_KEY
# Api_Key
# apiKey
```

## HTTP Headers

Sensitive headers are scrubbed:

```
Authorization: Bearer [REDACTED]
X-API-Key: [REDACTED]
Cookie: session=[REDACTED]
```

## Database Queries

Query parameters are not logged by default:

```sql
-- Logged (safe)
SELECT * FROM users WHERE email = ?

-- Not logged (could contain PII)
-- SELECT * FROM users WHERE email = 'user@example.com'
```

## Request Bodies

Sensitive fields in request bodies are scrubbed:

```json
// Original
{
  "username": "john",
  "password": "secret123"
}

// Scrubbed
{
  "username": "john",
  "password": "[REDACTED]"
}
```

## Best Practices

### 1. Use SecretStr in Models

```python
from pydantic import SecretStr


class LoginRequest(BaseModel):
    username: str
    password: SecretStr  # Won't be logged
```

### 2. Add Custom Patterns

```python
extra_patterns=[
    "access_token",
    "refresh_token",
    "otp",
    "verification_code",
    "pin",
]
```

### 3. Review Trace Data

Periodically check traces for exposed secrets:

1. Open Logfire dashboard
2. Search for sensitive keywords
3. Add missing patterns

### 4. Never Log Secrets Manually

```python
# Good
logger.info("User authenticated: %s", username)

# Bad - Never do this!
logger.info("Token issued: %s", token)
```

## Testing Scrubbing

Verify scrubbing works:

```python
import logfire


def test_scrubbing():
    with logfire.span("test", password="secret123"):
        pass

    # Check Logfire dashboard - password should be [REDACTED]
```

## Environment-Specific Patterns

You might want different patterns per environment:

```python
extra_patterns = ["access_token", "refresh_token"]

if environment == Environment.PRODUCTION:
    extra_patterns.extend([
        "credit_card",
        "ssn",
        "bank_account",
    ])
```

## Compliance

Scrubbing helps with:

- **GDPR** — Protecting personal data
- **PCI DSS** — Protecting payment data
- **HIPAA** — Protecting health data
- **SOC 2** — Security controls

!!! warning "Not a Complete Solution"
    Scrubbing is a safety net, not a primary control. Always design systems to avoid logging sensitive data in the first place.

## Troubleshooting

### Pattern Not Working

1. Check case sensitivity (patterns are case-insensitive)
2. Verify pattern matches field name exactly
3. Check if data is in a nested structure

### Too Much Scrubbing

If legitimate data is being scrubbed:

```python
# Be more specific
extra_patterns=["access_token"]  # Not just "token"
```

### Missing Scrubbing

Add the pattern:

```python
extra_patterns=[
    "my_secret_field",
]
```

## Related Topics

- [Logfire](logfire.md) — Logfire setup
- [Instrumented Libraries](instrumented-libraries.md) — Auto-instrumentation
- [Production Configuration](../configuration/production.md) — Security settings
