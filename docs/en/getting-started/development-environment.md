# Development Environment

Configure your IDE and development tools for an optimal workflow.

## IDE Setup

### VS Code

Install recommended extensions:

```bash
# Install extensions
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
```

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.analysis.typeCheckingMode": "strict",
    "python.analysis.extraPaths": ["src"],
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },
    "ruff.lint.args": ["--config=pyproject.toml"],
    "ruff.format.args": ["--config=pyproject.toml"]
}
```

### PyCharm

1. **Set Python interpreter**: Settings → Project → Python Interpreter → Select `.venv/bin/python`
2. **Mark `src` as Sources Root**: Right-click `src/` → Mark Directory as → Sources Root
3. **Enable Ruff**: Install the Ruff plugin from the marketplace
4. **Configure Django**: Settings → Languages & Frameworks → Django → Enable Django Support

## Code Quality Tools

The project uses several tools for code quality:

| Tool | Purpose | Command |
|------|---------|---------|
| **ruff** | Linting & formatting | `make format`, `make lint` |
| **mypy** | Static type checking | `make lint` |
| **ty** | Type checker | `make lint` |
| **pytest** | Testing | `make test` |

### Running Quality Checks

```bash
# Format code (auto-fix)
make format

# Run all linters
make lint

# Run tests with coverage
make test
```

### Pre-commit Hooks (Optional)

Install pre-commit to run checks automatically:

```bash
# Install pre-commit
uv pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
EOF

# Install hooks
pre-commit install
```

## Database Tools

### pgAdmin (Optional)

For visual database management:

```bash
# Add to docker-compose.yml
docker compose up -d pgadmin
```

Access at [http://localhost:5050](http://localhost:5050)

### Django Shell

Interactive Python shell with Django context:

```bash
uv run python src/manage.py shell
```

Example usage:

```python
from core.user.models import User
User.objects.all()
```

## Testing Workflow

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/integration/http/test_v1_users.py -v

# Run specific test
uv run pytest tests/integration/http/test_v1_users.py::test_create_user -v

# Run with coverage report
uv run pytest --cov=src --cov-report=html
```

### Debugging Tests

In VS Code, create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Tests",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["-v", "${file}"],
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        },
        {
            "name": "Debug Django Server",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/src/manage.py",
            "args": ["runserver", "--noreload"],
            "django": true,
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        }
    ]
}
```

## Environment Variables

### Local Development

The `.env` file is used for local development. Key variables:

```bash
# Django
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5432/app

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-jwt-secret

# Logfire (optional)
LOGFIRE_ENABLED=false
```

### Test Environment

Tests use `.env.test` which is loaded automatically:

```bash
# Minimal test configuration
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=test-secret-key
DATABASE_URL=postgres://postgres:postgres@localhost:5432/test_app
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=test-jwt-secret
```

## Common Development Tasks

### Database Operations

```bash
# Create migrations
make makemigrations

# Apply migrations
make migrate

# Create superuser
uv run python src/manage.py createsuperuser

# Reset database (dangerous!)
docker compose down -v postgres
docker compose up -d postgres
make migrate
```

### Celery Operations

```bash
# Start worker with auto-reload
make celery-dev

# Start beat scheduler
uv run celery -A delivery.tasks.app beat --loglevel=info

# Monitor tasks
uv run celery -A delivery.tasks.app flower
```

### API Development

```bash
# Start server with auto-reload
make dev

# Access API docs
open http://localhost:8000/docs

# Access admin
open http://localhost:8000/admin
```

## Next Steps

- [Quick Start](quick-start.md) - Run the application
- [Project Structure](project-structure.md) - Understand the codebase
- [Tutorial](../tutorial/index.md) - Build your first feature
