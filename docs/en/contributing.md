# Contributing

Guidelines for contributing to this project.

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/modern-django-template.git
cd modern-django-template
```

### 2. Set Up Development Environment

```bash
# Install dependencies
uv sync --locked --all-extras --dev

# Configure environment (includes COMPOSE_FILE for local development)
cp .env.example .env

# Start infrastructure (PostgreSQL, Redis, MinIO)
docker compose up -d postgres redis minio

# Create MinIO buckets, run migrations, and collect static files
docker compose up minio-create-buckets migrations collectstatic
```

!!! note "Manual Migrations"
    You can also run migrations manually using `make makemigrations` and `make migrate`.

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

## Code Standards

### Formatting

All code must be formatted with Ruff:

```bash
make format
```

### Linting

All code must pass linting:

```bash
make lint
```

This runs:

- `ruff check` — Python linter
- `ty check` — Type checking
- `pyrefly check` — Type checking
- `mypy` — Type checking

We use multiple type checkers because each might catch different issues. See [Development Environment](getting-started/development-environment.md#linting) for details.

### Testing

All tests must pass with 80% coverage:

```bash
make test
```

## Pull Request Process

### 1. Create Your Changes

- Write code following existing patterns
- Add tests for new functionality
- Update documentation if needed

### 2. Run Quality Checks

```bash
make format
make lint
make test
```

### 3. Commit Your Changes

Write clear commit messages:

```bash
git commit -m "Add feature X

- Implement Y
- Add tests for Z
- Update documentation"
```

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

### 5. Address Review Feedback

- Respond to comments
- Make requested changes
- Push updates

## Code Style

### Python

- Follow PEP 8 (enforced by Ruff)
- Use type hints for all functions
- Write docstrings for public APIs

### Controllers

Follow the controller pattern:

```python
class MyController(Controller):
    def __init__(self, dependency: Dependency) -> None:
        self._dependency = dependency

    def register(self, registry: Router) -> None:
        registry.add_api_operation(...)

    def handle_exception(self, exception: Exception) -> NoReturn:
        ...
```

### Settings

Use Pydantic Settings:

```python
class MySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MY_")

    setting_name: str = "default"
```

## Testing Guidelines

### Test Structure

```python
@pytest.mark.django_db(transaction=True)
def test_feature_name(test_client: TestClient) -> None:
    # Arrange
    ...

    # Act
    response = test_client.post("/endpoint", json={...})

    # Assert
    assert response.status_code == 200
```

### Test Isolation

Use fixtures for isolation:

```python
def test_with_mock(container: Container) -> None:
    mock = MagicMock()
    container.register(Service, instance=mock)
    ...
```

## Documentation

### Adding Documentation

1. Add new files to `docs/en/`
2. Update navigation in `docs/mkdocs.yml`
3. Follow existing formatting patterns

### Building Documentation

```bash
# Serve locally
make docs

# Build static site
make docs-build
```

## Issue Reporting

### Bug Reports

Include:

- Python version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages

### Feature Requests

Include:

- Use case description
- Proposed solution
- Alternatives considered

## Questions?

- Open a [GitHub Discussion](https://github.com/MaksimZayats/modern-django-template/discussions)
- Check existing issues and discussions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
