# Step 1: Model & Service

In this step, you will create the foundation for the Todo List feature: the Django model and the service layer that encapsulates all database operations.

## Files Overview

| Action | File Path |
|--------|-----------|
| Create | `src/core/todo/__init__.py` |
| Create | `src/core/todo/apps.py` |
| Create | `src/core/todo/models.py` |
| Create | `src/core/todo/services.py` |
| Modify | `src/core/configs/django.py` |

## Step 1.1: Create the Django App Structure

First, create the directory structure for the new `todo` domain:

```bash
mkdir -p src/core/todo
touch src/core/todo/__init__.py
```

## Step 1.2: Create the App Configuration

Create the Django app configuration in `src/core/todo/apps.py`:

```python title="src/core/todo/apps.py"
from django.apps import AppConfig


class TodoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.todo"
    label = "todo"
```

!!! info "App Label"
    The `label` attribute provides a short name for the app, used in migrations and database tables. This keeps table names concise (e.g., `todo_todo` instead of `core_todo_todo`).

## Step 1.3: Register the App

Add the new app to Django's `INSTALLED_APPS`. Open `src/core/configs/django.py` and add `"core.todo"` to the list of installed apps.

The exact location depends on your configuration, but you need to ensure the app is registered. You can verify by checking that no import errors occur when running:

```bash
python src/manage.py check
```

!!! note "Settings Adapter"
    The template uses `PydanticSettingsAdapter` to configure Django from Pydantic settings classes. Add `"core.todo"` to the `INSTALLED_APPS` list that gets adapted to Django settings.

## Step 1.4: Create the Todo Model

Create the model in `src/core/todo/models.py`:

```python title="src/core/todo/models.py"
from django.db import models

from core.user.models import User


class Todo(models.Model):
    """A todo item belonging to a user."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
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
        return f"Todo(id={self.pk}, title={self.title!r})"
```

### Model Fields Explained

| Field | Type | Purpose |
|-------|------|---------|
| `title` | CharField | Short description of the task |
| `description` | TextField | Optional detailed description |
| `is_completed` | BooleanField | Completion status flag |
| `created_at` | DateTimeField | Auto-set on creation |
| `completed_at` | DateTimeField | Set when marked complete |
| `user` | ForeignKey | Owner of the todo item |

## Step 1.5: Create Domain Exceptions

Before creating the service, define domain-specific exceptions. These exceptions communicate business rule violations and are caught by controllers to return appropriate HTTP responses.

Add the exceptions to `src/core/todo/services.py` (we'll add the service class next):

```python title="src/core/todo/services.py" hl_lines="1-2 5-9 12-16"
from core.exceptions import ApplicationError


class TodoNotFoundError(ApplicationError):
    """Raised when a requested todo item does not exist."""

    def __init__(self, todo_id: int) -> None:
        self.todo_id = todo_id
        super().__init__(f"Todo with id {todo_id} not found")


class TodoAccessDeniedError(ApplicationError):
    """Raised when a user attempts to access a todo they don't own."""

    def __init__(self, todo_id: int, user_id: int) -> None:
        self.todo_id = todo_id
        self.user_id = user_id
        super().__init__(f"User {user_id} cannot access todo {todo_id}")
```

!!! tip "Domain Exceptions"
    Domain exceptions inherit from `ApplicationError`, the base class defined in `src/core/exceptions.py`. This allows controllers to catch all domain exceptions uniformly while providing specific error context.

## Step 1.6: Create the Todo Service

Now add the `TodoService` class that encapsulates all todo-related database operations:

```python title="src/core/todo/services.py"
from django.db import transaction
from django.utils import timezone

from core.exceptions import ApplicationError
from core.todo.models import Todo
from core.user.models import User


class TodoNotFoundError(ApplicationError):
    """Raised when a requested todo item does not exist."""

    def __init__(self, todo_id: int) -> None:
        self.todo_id = todo_id
        super().__init__(f"Todo with id {todo_id} not found")


class TodoAccessDeniedError(ApplicationError):
    """Raised when a user attempts to access a todo they don't own."""

    def __init__(self, todo_id: int, user_id: int) -> None:
        self.todo_id = todo_id
        self.user_id = user_id
        super().__init__(f"User {user_id} cannot access todo {todo_id}")


class TodoService:
    """Service for managing todo items.

    This service encapsulates all database operations for the Todo model.
    Controllers should use this service instead of accessing the model directly.
    """

    def get_todo_by_id(self, todo_id: int, user: User) -> Todo:
        """Get a todo item by its ID.

        Args:
            todo_id: The ID of the todo item.
            user: The user requesting the todo.

        Returns:
            The todo item.

        Raises:
            TodoNotFoundError: If the todo item does not exist.
            TodoAccessDeniedError: If the user does not own the todo.
        """
        try:
            todo = Todo.objects.get(id=todo_id)
        except Todo.DoesNotExist as e:
            raise TodoNotFoundError(todo_id) from e

        if todo.user_id != user.pk:
            raise TodoAccessDeniedError(todo_id, user.pk)

        return todo

    def list_todos_for_user(self, user: User) -> list[Todo]:
        """List all todos for a user.

        Args:
            user: The user whose todos to list.

        Returns:
            List of todo items ordered by creation date (newest first).
        """
        return list(Todo.objects.filter(user=user))

    @transaction.atomic
    def create_todo(
        self,
        title: str,
        user: User,
        description: str = "",
    ) -> Todo:
        """Create a new todo item.

        Args:
            title: The title of the todo.
            user: The owner of the todo.
            description: Optional detailed description.

        Returns:
            The created todo item.
        """
        return Todo.objects.create(
            title=title,
            description=description,
            user=user,
        )

    @transaction.atomic
    def complete_todo(self, todo_id: int, user: User) -> Todo:
        """Mark a todo item as completed.

        Args:
            todo_id: The ID of the todo to complete.
            user: The user completing the todo.

        Returns:
            The updated todo item.

        Raises:
            TodoNotFoundError: If the todo item does not exist.
            TodoAccessDeniedError: If the user does not own the todo.
        """
        todo = self.get_todo_by_id(todo_id, user)
        todo.is_completed = True
        todo.completed_at = timezone.now()
        todo.save(update_fields=["is_completed", "completed_at"])
        return todo

    @transaction.atomic
    def delete_todo(self, todo_id: int, user: User) -> None:
        """Delete a todo item.

        Args:
            todo_id: The ID of the todo to delete.
            user: The user deleting the todo.

        Raises:
            TodoNotFoundError: If the todo item does not exist.
            TodoAccessDeniedError: If the user does not own the todo.
        """
        todo = self.get_todo_by_id(todo_id, user)
        todo.delete()

    def delete_completed_todos_older_than(self, days: int) -> int:
        """Delete completed todos older than the specified number of days.

        This method is intended for use by background cleanup tasks.

        Args:
            days: Delete todos completed more than this many days ago.

        Returns:
            The number of deleted todos.
        """
        cutoff = timezone.now() - timezone.timedelta(days=days)
        deleted_count, _ = Todo.objects.filter(
            is_completed=True,
            completed_at__lt=cutoff,
        ).delete()
        return deleted_count
```

### Service Method Patterns

The service follows several important patterns:

1. **Transaction Boundaries**: Write operations use `@transaction.atomic` to ensure data consistency.

2. **Ownership Validation**: Methods that access specific todos verify the user owns the item.

3. **Domain Exceptions**: Methods raise domain-specific exceptions rather than returning `None` or generic errors.

4. **Type Hints**: All methods have complete type annotations for better IDE support and documentation.

5. **Docstrings with Raises**: Each method documents which exceptions it may raise, helping controller authors handle errors correctly.

!!! warning "Never Access Models from Controllers"
    The service layer is the **only** place where models should be imported. Controllers must use the service to interact with data. This is the template's most important architectural rule.

## Step 1.7: Create and Run Migrations

Generate and apply the database migration:

```bash
make makemigrations
make migrate
```

You should see output similar to:

```
Migrations for 'todo':
  src/core/todo/migrations/0001_initial.py
    - Create model Todo
```

## Verify Your Work

Test that everything is set up correctly:

```bash
# Check for any configuration errors
python src/manage.py check

# Verify the model is registered
python src/manage.py shell -c "from core.todo.models import Todo; print(Todo._meta.db_table)"
# Output: todo_todo
```

## What's Next

You have created the foundation of the Todo feature:

- [x] Django app configuration
- [x] Todo model with user ownership
- [x] Domain exceptions for error handling
- [x] TodoService with full CRUD operations

In the next step, you will register the service in the IoC container so it can be injected into controllers.

[Continue to Step 2: IoC Registration](02-ioc-registration.md){ .md-button .md-button--primary }

---

!!! abstract "See Also"
    - [Service Layer Pattern](../concepts/service-layer.md) - Deep dive into service layer architecture
