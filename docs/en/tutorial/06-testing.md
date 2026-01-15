# Step 6: Testing

In this final step, you'll write integration tests for your Todo API and Celery task using the template's test factories.

## Files to Create/Modify

| Action | File Path |
|--------|-----------|
| Modify | `tests/integration/factories.py` |
| Modify | `tests/integration/conftest.py` |
| Create | `tests/integration/http/test_v1_todos.py` |
| Create | `tests/integration/tasks/test_todo_cleanup_task.py` |

## Why Test Factories?

Test factories provide:

- **Isolation** - Each test gets fresh data via IoC-resolved factories
- **Defaults** - Sensible default values reduce boilerplate
- **Type safety** - Factory return types enable IDE completion
- **Flexibility** - Override defaults for specific test cases

## 1. Create TestTodoFactory

Add the todo factory to `tests/integration/factories.py`:

```python
# tests/integration/factories.py
# Add this import
from core.todo.models import Todo

# Add this class after TestUserFactory
class TestTodoFactory:
    __test__ = False  # Prevent pytest from collecting as test

    def __call__(
        self,
        user: User,
        title: str = "Test Todo",
        description: str = "",
        is_completed: bool = False,
    ) -> Todo:
        return Todo.objects.create(
            user=user,
            title=title,
            description=description,
            is_completed=is_completed,
        )
```

**Key points:**

- `__test__ = False` prevents pytest from treating this as a test class
- User is required (no default) - enforces explicit user association
- Other fields have sensible defaults

## 2. Register Factory in conftest.py

Add the factory registration and fixture:

```python
# tests/integration/conftest.py
# Add this import
from tests.integration.factories import TestTodoFactory

# Modify the container fixture to register TestTodoFactory
@pytest.fixture(scope="function")
def container(django_user_model: type[User]) -> Container:
    container = get_container()
    container.register(TestNinjaAPIFactory, scope=Scope.singleton)
    container.register(TestClientFactory, scope=Scope.singleton)
    container.register(TestCeleryWorkerFactory, scope=Scope.singleton)
    container.register(type[User], instance=django_user_model)
    container.register(TestUserFactory, scope=Scope.singleton)
    container.register(TestTodoFactory, scope=Scope.singleton)  # Add this
    return container

# Add this fixture
@pytest.fixture(scope="function")
def todo_factory(
    transactional_db: None,
    container: Container,
) -> TestTodoFactory:
    return container.resolve(TestTodoFactory)
```

## 3. Create HTTP API Tests

Create comprehensive tests for the Todo API:

```python
# tests/integration/http/test_v1_todos.py
from http import HTTPStatus

import pytest
from punq import Container

from core.todo.models import Todo
from core.user.models import User
from tests.integration.factories import (
    TestClientFactory,
    TestTodoFactory,
    TestUserFactory,
)


@pytest.fixture(scope="function")
def user(user_factory: TestUserFactory) -> User:
    return user_factory(username="todo_test_user", password="test123")


@pytest.fixture(scope="function")
def todo(todo_factory: TestTodoFactory, user: User) -> Todo:
    return todo_factory(user=user, title="Existing Todo")


@pytest.mark.django_db(transaction=True)
def test_list_todos_empty(
    test_client_factory: TestClientFactory,
    user: User,
) -> None:
    """Test listing todos when user has none."""
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.get("/v1/todos/")

    assert response.status_code == HTTPStatus.OK
    assert response.json()["items"] == []


@pytest.mark.django_db(transaction=True)
def test_list_todos_returns_user_todos(
    test_client_factory: TestClientFactory,
    user: User,
    todo: Todo,
) -> None:
    """Test listing todos returns user's todos."""
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.get("/v1/todos/")

    assert response.status_code == HTTPStatus.OK
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Existing Todo"
    assert items[0]["is_completed"] is False


@pytest.mark.django_db(transaction=True)
def test_list_todos_does_not_return_other_users_todos(
    test_client_factory: TestClientFactory,
    user_factory: TestUserFactory,
    todo_factory: TestTodoFactory,
) -> None:
    """Test that users can only see their own todos."""
    user1 = user_factory(username="user1", email="user1@test.com")
    user2 = user_factory(username="user2", email="user2@test.com")

    # Create todo for user1
    todo_factory(user=user1, title="User1 Todo")

    # Login as user2
    test_client = test_client_factory(auth_for_user=user2)

    response = test_client.get("/v1/todos/")

    assert response.status_code == HTTPStatus.OK
    assert response.json()["items"] == []


@pytest.mark.django_db(transaction=True)
def test_create_todo(
    test_client_factory: TestClientFactory,
    user: User,
) -> None:
    """Test creating a new todo."""
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.post(
        "/v1/todos/",
        json={
            "title": "New Todo",
            "description": "Test description",
        },
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["title"] == "New Todo"
    assert data["description"] == "Test description"
    assert data["is_completed"] is False


@pytest.mark.django_db(transaction=True)
def test_get_todo(
    test_client_factory: TestClientFactory,
    user: User,
    todo: Todo,
) -> None:
    """Test getting a specific todo."""
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.get(f"/v1/todos/{todo.id}")

    assert response.status_code == HTTPStatus.OK
    assert response.json()["title"] == "Existing Todo"


@pytest.mark.django_db(transaction=True)
def test_get_todo_not_found(
    test_client_factory: TestClientFactory,
    user: User,
) -> None:
    """Test getting a non-existent todo returns 404."""
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.get("/v1/todos/99999")

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db(transaction=True)
def test_get_other_users_todo_forbidden(
    test_client_factory: TestClientFactory,
    user_factory: TestUserFactory,
    todo_factory: TestTodoFactory,
) -> None:
    """Test accessing another user's todo returns 403."""
    user1 = user_factory(username="user1", email="user1@test.com")
    user2 = user_factory(username="user2", email="user2@test.com")

    todo = todo_factory(user=user1, title="User1 Todo")

    # Login as user2 and try to access user1's todo
    test_client = test_client_factory(auth_for_user=user2)

    response = test_client.get(f"/v1/todos/{todo.id}")

    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db(transaction=True)
def test_complete_todo(
    test_client_factory: TestClientFactory,
    user: User,
    todo: Todo,
) -> None:
    """Test marking a todo as completed."""
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.post(f"/v1/todos/{todo.id}/complete")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["is_completed"] is True
    assert data["completed_at"] is not None


@pytest.mark.django_db(transaction=True)
def test_delete_todo(
    test_client_factory: TestClientFactory,
    user: User,
    todo: Todo,
) -> None:
    """Test deleting a todo."""
    test_client = test_client_factory(auth_for_user=user)

    response = test_client.delete(f"/v1/todos/{todo.id}")

    assert response.status_code == HTTPStatus.OK
    assert response.json()["status"] == "deleted"

    # Verify todo is gone
    response = test_client.get(f"/v1/todos/{todo.id}")
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db(transaction=True)
def test_requires_authentication(
    test_client_factory: TestClientFactory,
) -> None:
    """Test that endpoints require authentication."""
    test_client = test_client_factory()  # No auth

    response = test_client.get("/v1/todos/")

    assert response.status_code == HTTPStatus.UNAUTHORIZED
```

## 4. Create Celery Task Tests

Create tests for the cleanup task:

```python
# tests/integration/tasks/test_todo_cleanup_task.py
from datetime import UTC, datetime, timedelta

import pytest
from punq import Container

from core.todo.models import Todo
from core.user.models import User
from delivery.tasks.registry import TasksRegistry
from tests.integration.factories import (
    TestCeleryWorkerFactory,
    TestTodoFactory,
    TestUserFactory,
)


@pytest.fixture(scope="function")
def user(user_factory: TestUserFactory) -> User:
    return user_factory(username="cleanup_test_user")


@pytest.fixture(scope="function")
def tasks_registry(container: Container) -> TasksRegistry:
    return container.resolve(TasksRegistry)


@pytest.mark.django_db(transaction=True)
def test_todo_cleanup_deletes_old_completed_todos(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
    todo_factory: TestTodoFactory,
    user: User,
) -> None:
    """Test that cleanup deletes old completed todos."""
    # Create an old completed todo
    old_todo = todo_factory(user=user, is_completed=True)
    # Manually set completed_at to 31 days ago
    old_todo.completed_at = datetime.now(tz=UTC) - timedelta(days=31)
    old_todo.save()

    # Create a recent completed todo (should not be deleted)
    recent_todo = todo_factory(
        user=user,
        title="Recent Todo",
        is_completed=True,
    )
    recent_todo.completed_at = datetime.now(tz=UTC)
    recent_todo.save()

    # Create an incomplete todo (should not be deleted)
    incomplete_todo = todo_factory(
        user=user,
        title="Incomplete Todo",
        is_completed=False,
    )

    with celery_worker_factory():
        result = tasks_registry.todo_cleanup.delay(days=30).get(timeout=10)

    assert result["status"] == "success"
    assert result["deleted_count"] == 1

    # Verify correct todos remain
    remaining = Todo.objects.filter(user=user)
    assert remaining.count() == 2
    assert remaining.filter(title="Recent Todo").exists()
    assert remaining.filter(title="Incomplete Todo").exists()


@pytest.mark.django_db(transaction=True)
def test_todo_cleanup_with_no_old_todos(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
    todo_factory: TestTodoFactory,
    user: User,
) -> None:
    """Test cleanup when there are no old todos."""
    # Create only recent todos
    todo_factory(user=user, is_completed=False)

    with celery_worker_factory():
        result = tasks_registry.todo_cleanup.delay(days=30).get(timeout=10)

    assert result["status"] == "success"
    assert result["deleted_count"] == 0


@pytest.mark.django_db(transaction=True)
def test_todo_cleanup_with_custom_days(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry: TasksRegistry,
    todo_factory: TestTodoFactory,
    user: User,
) -> None:
    """Test cleanup with custom days parameter."""
    # Create a todo completed 5 days ago
    todo = todo_factory(user=user, is_completed=True)
    todo.completed_at = datetime.now(tz=UTC) - timedelta(days=5)
    todo.save()

    with celery_worker_factory():
        # Should not delete with 7 days threshold
        result = tasks_registry.todo_cleanup.delay(days=7).get(timeout=10)
        assert result["deleted_count"] == 0

        # Should delete with 3 days threshold
        result = tasks_registry.todo_cleanup.delay(days=3).get(timeout=10)
        assert result["deleted_count"] == 1
```

## 5. Run the Tests

```bash
# Run all tests
make test

# Run only todo tests
uv run pytest tests/integration/http/test_v1_todos.py tests/integration/tasks/test_todo_cleanup_task.py -v

# Run with coverage
uv run pytest tests/integration/ --cov=src --cov-report=html
```

## IoC Override Pattern

For mocking dependencies in tests:

```python
from unittest.mock import MagicMock

def test_with_mock_service(container: Container) -> None:
    # Create mock
    mock_service = MagicMock(spec=TodoService)
    mock_service.list_todos.return_value = []

    # Override in container
    container.register(TodoService, instance=mock_service)

    # Now resolve factories - they'll use mock
    test_client = container.resolve(TestClientFactory)()
    response = test_client.get("/v1/todos/")

    # Verify mock was called
    mock_service.list_todos.assert_called_once()
```

## What You've Learned

In this step, you:

1. Created a test factory for Todo models
2. Registered the factory in the IoC container
3. Wrote comprehensive HTTP API tests
4. Wrote Celery task tests
5. Learned the IoC override pattern for mocking

## Congratulations!

You've completed the tutorial! You now have a fully-functional Todo List feature with:

- Django model with user association
- Service layer with business logic
- REST API with JWT authentication
- Django admin panel
- Background cleanup task
- Observability with Logfire
- Comprehensive tests

## Next Steps

- Explore the [Concepts](../concepts/index.md) section for deeper understanding
- Check [How-To Guides](../how-to/index.md) for specific tasks
- Read [Reference](../reference/index.md) for detailed configuration options
