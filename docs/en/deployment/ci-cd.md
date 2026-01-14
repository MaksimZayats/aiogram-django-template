# CI/CD

Continuous integration and deployment workflows.

## Overview

The project includes GitHub Actions workflows for:

- Code quality checks (lint)
- Automated testing
- Docker image building

## Workflow Files

Located in `.github/workflows/`:

| File | Purpose |
|------|---------|
| `lint_test.yaml` | Lint and test on pull requests |

## Lint and Test Workflow

```yaml
name: Lint and Test

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install

      - name: Install dependencies
        run: uv sync --locked --all-extras --dev

      - name: Run ruff
        run: uv run ruff check .

      - name: Run ruff format
        run: uv run ruff format --check .

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:18-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
      redis:
        image: redis:latest
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install

      - name: Install dependencies
        run: uv sync --locked --all-extras --dev

      - name: Run tests
        env:
          DATABASE_URL: postgres://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
        run: uv run pytest tests/
```

## Local Testing Before Push

Run the same checks locally:

```bash
# Format check
make format

# Lint
make lint

# Tests
make test
```

## Adding Deployment Workflow

Example deployment workflow:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker compose build

      - name: Push to registry
        run: |
          docker login -u ${{ secrets.REGISTRY_USER }} -p ${{ secrets.REGISTRY_PASS }}
          docker push your-registry/your-app:latest

      - name: Deploy
        run: |
          ssh user@server "cd /app && docker compose pull && docker compose up -d"
```

## Environment Variables in CI

### GitHub Secrets

Add secrets in repository settings:

- `DJANGO_SECRET_KEY`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `REGISTRY_USER`
- `REGISTRY_PASS`

### Using Secrets

```yaml
steps:
  - name: Run with secrets
    env:
      DJANGO_SECRET_KEY: ${{ secrets.DJANGO_SECRET_KEY }}
    run: pytest tests/
```

## Docker Build in CI

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: your-registry/app:${{ github.sha }}
```

## Database Migrations in CI

```yaml
- name: Check migrations
  run: |
    docker compose run --rm api python manage.py migrate --check

- name: Run migrations
  run: |
    docker compose run --rm api python manage.py migrate
```

## Branch Protection

Recommended branch protection rules for `main`:

- Require pull request before merging
- Require status checks to pass:
  - `lint`
  - `test`
- Require branches to be up to date
- Restrict who can push

## Deployment Strategies

### Rolling Update

```yaml
deploy:
  runs-on: ubuntu-latest
  steps:
    - name: Deploy with rolling update
      run: |
        docker compose up -d --no-deps api
        docker compose exec api python manage.py migrate
```

### Blue-Green Deployment

```yaml
deploy:
  runs-on: ubuntu-latest
  steps:
    - name: Deploy to blue
      run: docker compose -p blue up -d

    - name: Health check
      run: curl -f http://localhost:8009/api/v1/health

    - name: Switch traffic
      run: ./switch-traffic.sh blue

    - name: Stop green
      run: docker compose -p green down
```

## Notifications

### Slack Notification

```yaml
- name: Notify Slack
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    fields: repo,message,commit,author
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## Best Practices

### 1. Fast Feedback

Run quick checks first:

```yaml
jobs:
  lint:
    # Fast - run first
  test:
    needs: lint  # Only run if lint passes
  deploy:
    needs: test  # Only run if tests pass
```

### 2. Cache Dependencies

```yaml
- name: Cache uv
  uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: uv-${{ hashFiles('uv.lock') }}
```

### 3. Parallel Jobs

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
  test:
    runs-on: ubuntu-latest
  type-check:
    runs-on: ubuntu-latest
```

### 4. Environment-Specific Deployment

```yaml
deploy-staging:
  if: github.ref == 'refs/heads/develop'
  environment: staging

deploy-production:
  if: github.ref == 'refs/heads/main'
  environment: production
```

## Related Topics

- [Development Environment](../getting-started/development-environment.md) — Local setup
- [Production Checklist](production-checklist.md) — Deployment checklist
- [Docker Compose](docker-compose.md) — Container configuration
