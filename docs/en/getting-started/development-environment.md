# Development Environment

Configure your development environment for the best experience with the Modern Django API Template.

## IDE Setup

### Visual Studio Code

VS Code provides excellent Python support with the right extensions.

#### Recommended Extensions

Install these extensions for the best experience:

- **Python** (`ms-python.python`) - Core Python support
- **Pylance** (`ms-python.vscode-pylance`) - Fast, feature-rich language server
- **Ruff** (`charliermarsh.ruff`) - Fast linting and formatting
- **Even Better TOML** (`tamasfe.even-better-toml`) - TOML file support

#### Workspace Settings

Create or update `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.analysis.typeCheckingMode": "strict",
  "python.analysis.extraPaths": ["src", "typings"],

  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },

  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".mypy_cache": true,
    ".pytest_cache": true,
    ".ruff_cache": true
  }
}
```

### PyCharm / IntelliJ IDEA

PyCharm provides built-in support for most features.

#### Project Configuration

1. **Set Python Interpreter**
   - Go to `Settings` > `Project` > `Python Interpreter`
   - Select the interpreter from `.venv/bin/python`

2. **Configure Source Roots**
   - Right-click `src/` directory
   - Select `Mark Directory as` > `Sources Root`
   - Right-click `typings/` directory
   - Select `Mark Directory as` > `Sources Root`

3. **Enable Django Support**
   - Go to `Settings` > `Languages & Frameworks` > `Django`
   - Enable Django support
   - Set Django project root to the repository root
   - Set Settings to `core.configs.django`

4. **Configure Ruff**
   - Go to `Settings` > `Tools` > `Ruff`
   - Enable Ruff as external tool
   - Configure format on save

## Type Checking

The project uses multiple type checkers for comprehensive coverage.

### mypy

mypy is the primary type checker, configured in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.14"
strict = true
mypy_path = "typings"
plugins = ["mypy_django_plugin.main"]
```

Run mypy manually:

```bash
uv run mypy src/ tests/
```

### ty

ty is a fast type checker that complements mypy:

```bash
uv run ty check .
```

### pyrefly

pyrefly provides additional static analysis:

```bash
uv run pyrefly check src/
```

### Running All Type Checkers

Use the lint command to run all checks:

```bash
make lint
```

This runs:

1. `ruff check .` - Linting
2. `ty check .` - Type checking (ty)
3. `pyrefly check src/` - Static analysis
4. `mypy src/ tests/` - Type checking (mypy)

## Linting with Ruff

[Ruff](https://docs.astral.sh/ruff/) is an extremely fast Python linter and formatter.

### Format Code

```bash
make format
```

This runs:

```bash
uv run ruff format .
uv run ruff check --fix-only .
```

### Check Without Fixing

```bash
uv run ruff check .
```

!!! tip "Editor Integration"
    With the Ruff VS Code extension, formatting happens automatically on save. This is the recommended workflow.

## Pre-commit Hooks

The project includes pre-commit hooks for automated quality checks.

### Installation

```bash
uv run pre-commit install
```

### Configuration

The hooks are defined in `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: builtin
    hooks:
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: end-of-file-fixer
      - id: check-added-large-files

  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.9.24
    hooks:
      - id: uv-lock
```

### What the Hooks Do

| Hook | Purpose |
|------|---------|
| `check-yaml` | Validates YAML syntax |
| `check-json` | Validates JSON syntax |
| `check-toml` | Validates TOML syntax |
| `end-of-file-fixer` | Ensures files end with newline |
| `check-added-large-files` | Prevents committing large files |
| `uv-lock` | Ensures `uv.lock` is up to date |

### Running Manually

Run hooks on all files:

```bash
uv run pre-commit run --all-files
```

## Testing

### Running Tests

```bash
make test
```

This runs pytest with coverage:

```bash
uv run pytest tests/
```

### Test Configuration

Tests are configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "9.0"
DJANGO_SETTINGS_MODULE = "core.configs.django"
addopts = "--exitfirst -vv --cov=src --cov-report=html --cov-fail-under=80"
testpaths = ["tests"]
```

Key settings:

- **`--exitfirst`** - Stop on first failure for faster feedback
- **`--cov=src`** - Measure coverage for `src/` directory
- **`--cov-fail-under=80`** - Require 80% minimum coverage

### Coverage Report

After running tests, open the HTML coverage report:

```bash
open htmlcov/index.html
```

## Environment Variables

### Local Development

Copy the example file and customize:

```bash
cp .env.example .env
```

### Test Environment

Tests use `.env.test` which is loaded automatically by `tests/conftest.py`.

!!! warning "Secrets"
    Never commit `.env` files with real secrets. The `.gitignore` excludes `.env` but not `.env.example`.

## Useful Commands

| Command | Description |
|---------|-------------|
| `make dev` | Run development server |
| `make celery-dev` | Run Celery worker |
| `make celery-beat-dev` | Run Celery beat scheduler |
| `make bot-dev` | Run Telegram bot |
| `make format` | Format code with Ruff |
| `make lint` | Run all linters and type checkers |
| `make test` | Run tests with coverage |
| `make makemigrations` | Create new migrations |
| `make migrate` | Apply migrations |
| `make docs` | Serve documentation locally |

## Debugging

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Django: Runserver",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/manage.py",
      "args": ["runserver"],
      "django": true,
      "env": {
        "DJANGO_DEBUG": "true"
      }
    },
    {
      "name": "Pytest: Current File",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-vv"],
      "env": {
        "DJANGO_SETTINGS_MODULE": "core.configs.django"
      }
    }
  ]
}
```

### PyCharm Debugging

1. Create a Django Server run configuration
2. Set the script to `manage.py`
3. Set parameters to `runserver`
4. Enable Django support in the configuration

## Next Steps

With your environment configured, you are ready to:

- **[Tutorial: Build a Todo List](../tutorial/index.md)** - Learn by building
- **[Add a New Domain](../how-to/add-new-domain.md)** - Create your first feature
- **[Service Layer](../concepts/service-layer.md)** - Understand the architecture
