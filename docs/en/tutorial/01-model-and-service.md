# Step 1: Model & Service

In this step, you'll create the Django model for storing todos and a service to encapsulate all database operations.

> **See also:** [Service Layer concept](../concepts/service-layer.md)

## Files to Create/Modify

| Action | File Path |
|--------|-----------|
| Create | `src/core/todo/__init__.py` |
| Create | `src/core/todo/apps.py` |
| Create | `src/core/todo/models.py` |
| Create | `src/core/todo/services.py` |
| Modify | `src/core/configs/django.py` |

## 1. Create the Django App Config

First, create the Django app configuration:

```python
# src/core/todo/apps.py
from django.apps import AppConfig


class TodoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.todo"
```

Create an empty `__init__.py`:

```python
# src/core/todo/__init__.py
```

## 2. Register the App

Add the app to `INSTALLED_APPS` in `src/core/configs/django.py`:

```python
# src/core/configs/django.py
# Find the installed_apps tuple and add "core.todo.apps.TodoConfig"

application_settings = ApplicationSettings(
    installed_apps=(
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "core.user.apps.UserConfig",
        "core.todo.apps.TodoConfig",  # Add this line
    ),
)
```

## 3. Create the Todo Model

Create the model with a foreign key to the User model:

```python
# src/core/todo/models.py
from django.db import models

from core.user.models import User


class Todo(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="todos",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
```

**Key points:**

- `user` is a foreign key to the existing `User` model
- `related_name="todos"` allows `user.todos.all()` queries
- `ordering = ["-created_at"]` shows newest todos first

## 4. Create Domain Exceptions

Domain exceptions provide meaningful error types that controllers can catch and convert to HTTP responses:

```python
# src/core/todo/services.py
from core.exceptions import ApplicationError


class TodoNotFoundError(ApplicationError):
    """Raised when a todo item cannot be found."""


class TodoAccessDeniedError(ApplicationError):
    """Raised when user tries to access another user's todo."""
```

## 5. Create the TodoService

The service encapsulates all database operations:

```python
# src/core/todo/services.py
from datetime import UTC, datetime, timedelta

from django.db import transaction

from core.exceptions import ApplicationError
from core.todo.models import Todo
from core.user.models import User


class TodoNotFoundError(ApplicationError):
    """Raised when a todo item cannot be found."""


class TodoAccessDeniedError(ApplicationError):
    """Raised when user tries to access another user's todo."""


class TodoService:
    def get_todo_by_id(self, todo_id: int, user: User) -> Todo:
        """Get a todo by ID, ensuring it belongs to the user."""
        try:
            todo = Todo.objects.get(id=todo_id)
        except Todo.DoesNotExist as e:
            raise TodoNotFoundError(f"Todo {todo_id} not found") from e

        if todo.user_id != user.id:
            raise TodoAccessDeniedError("Cannot access another user's todo")

        return todo

    def list_todos(self, user: User) -> list[Todo]:
        """List all todos for a user."""
        return list(Todo.objects.filter(user=user))

    def list_incomplete_todos(self, user: User) -> list[Todo]:
        """List incomplete todos for a user."""
        return list(Todo.objects.filter(user=user, is_completed=False))

    @transaction.atomic
    def create_todo(
        self,
        user: User,
        title: str,
        description: str = "",
    ) -> Todo:
        """Create a new todo for a user."""
        return Todo.objects.create(
            user=user,
            title=title,
            description=description,
        )

    @transaction.atomic
    def complete_todo(self, todo_id: int, user: User) -> Todo:
        """Mark a todo as completed."""
        todo = self.get_todo_by_id(todo_id, user)
        todo.is_completed = True
        todo.completed_at = datetime.now(tz=UTC)
        todo.save()
        return todo

    @transaction.atomic
    def delete_todo(self, todo_id: int, user: User) -> None:
        """Delete a todo."""
        todo = self.get_todo_by_id(todo_id, user)
        todo.delete()

    @transaction.atomic
    def delete_completed_todos_older_than(self, days: int) -> int:
        """Delete completed todos older than N days. Returns count deleted."""
        cutoff = datetime.now(tz=UTC) - timedelta(days=days)
        deleted, _ = Todo.objects.filter(
            is_completed=True,
            completed_at__lt=cutoff,
        ).delete()
        return deleted
```

**Key patterns:**

- **Domain exceptions** - `TodoNotFoundError`, `TodoAccessDeniedError` instead of generic errors
- **User scoping** - Every operation verifies the user owns the todo
- **Transaction safety** - `@transaction.atomic` for write operations
- **Return types** - Clear return types for each method

## 6. Run Migrations

Generate and apply the database migration:

```bash
# Generate migration
make makemigrations

# Apply migration
make migrate
```

You should see output like:

```
Migrations for 'todo':
  src/core/todo/migrations/0001_initial.py
    - Create model Todo
```

## Verify Your Work

You can verify the model works using the Django shell:

```bash
uv run python src/manage.py shell
```

```python
from core.todo.models import Todo
from core.user.models import User

# Create a test user (if you haven't already)
user = User.objects.create_user(
    username="testuser",
    email="test@example.com",
    password="testpass123"
)

# Create a todo
todo = Todo.objects.create(
    user=user,
    title="Learn the service layer pattern",
    description="Follow the tutorial step by step"
)

print(todo)  # "Learn the service layer pattern"
print(todo.user.username)  # "testuser"
```

## What You've Learned

In this step, you:

1. Created a Django app with proper configuration
2. Defined a model with relationships and constraints
3. Built a service that encapsulates all database operations
4. Defined domain-specific exceptions for error handling

## Next Step

In [Step 2: IoC Registration](02-ioc-registration.md), you'll register the TodoService in the IoC container so it can be injected into controllers.
