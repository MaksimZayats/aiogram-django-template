# Add a New Domain

This guide walks through adding a complete new domain (feature area) to the application.

## Prerequisites

- Understanding of the [Service Layer](../concepts/service-layer.md) pattern
- Familiarity with [IoC Container](../concepts/ioc-container.md) registration

## Checklist

- [ ] Create Django app config
- [ ] Create model
- [ ] Create service with domain exceptions
- [ ] Register app in Django settings
- [ ] Register service in IoC
- [ ] Create HTTP controller
- [ ] Register controller in IoC
- [ ] Update API factory
- [ ] (Optional) Create admin
- [ ] (Optional) Create Celery task
- [ ] Create tests

## Step-by-Step

### 1. Create Django App Config

```python
# src/core/article/__init__.py
# (empty file)

# src/core/article/apps.py
from django.apps import AppConfig


class ArticleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.article"
```

### 2. Create Model

```python
# src/core/article/models.py
from django.db import models

from core.user.models import User


class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
```

### 3. Create Service

```python
# src/core/article/services.py
from django.db import transaction

from core.article.models import Article
from core.exceptions import ApplicationError
from core.user.models import User


class ArticleNotFoundError(ApplicationError):
    """Raised when article cannot be found."""


class ArticleAccessDeniedError(ApplicationError):
    """Raised when user cannot access the article."""


class ArticleService:
    def get_article_by_id(self, article_id: int) -> Article:
        try:
            return Article.objects.get(id=article_id)
        except Article.DoesNotExist as e:
            raise ArticleNotFoundError(f"Article {article_id} not found") from e

    def list_published_articles(self) -> list[Article]:
        return list(Article.objects.filter(is_published=True))

    def list_user_articles(self, user: User) -> list[Article]:
        return list(Article.objects.filter(author=user))

    @transaction.atomic
    def create_article(
        self,
        author: User,
        title: str,
        content: str,
    ) -> Article:
        return Article.objects.create(
            author=author,
            title=title,
            content=content,
        )

    @transaction.atomic
    def publish_article(self, article_id: int, user: User) -> Article:
        article = self.get_article_by_id(article_id)
        if article.author_id != user.id:
            raise ArticleAccessDeniedError("Cannot publish another user's article")
        article.is_published = True
        article.save()
        return article
```

### 4. Register App in Django Settings

```python
# src/core/configs/django.py
application_settings = ApplicationSettings(
    installed_apps=(
        # ... existing apps ...
        "core.article.apps.ArticleConfig",
    ),
)
```

### 5. Create and Apply Migration

```bash
make makemigrations
make migrate
```

### 6. Register Service in IoC

```python
# src/ioc/registries/core.py
from core.article.services import ArticleService


def _register_services(container: Container) -> None:
    # ... existing services ...
    container.register(ArticleService, scope=Scope.singleton)
```

### 7. Create HTTP Controller

```python
# src/delivery/http/article/__init__.py
# (empty file)

# src/delivery/http/article/controllers.py
from http import HTTPStatus
from typing import Any

from ninja import Router
from ninja.errors import HttpError
from ninja.throttling import AnonRateThrottle, AuthRateThrottle
from pydantic import BaseModel

from core.article.services import (
    ArticleAccessDeniedError,
    ArticleNotFoundError,
    ArticleService,
)
from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import AuthenticatedHttpRequest, JWTAuth


class CreateArticleRequestSchema(BaseModel):
    title: str
    content: str


class ArticleSchema(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    is_published: bool
    created_at: str


class ArticleListSchema(BaseModel):
    items: list[ArticleSchema]


class ArticleController(Controller):
    def __init__(
        self,
        jwt_auth: JWTAuth,
        article_service: ArticleService,
    ) -> None:
        self._jwt_auth = jwt_auth
        self._article_service = article_service

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/articles/",
            methods=["GET"],
            view_func=self.list_articles,
            auth=None,
            throttle=AnonRateThrottle(rate="60/min"),
        )
        registry.add_api_operation(
            path="/v1/articles/",
            methods=["POST"],
            view_func=self.create_article,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="10/min"),
        )
        registry.add_api_operation(
            path="/v1/articles/{article_id}/publish",
            methods=["POST"],
            view_func=self.publish_article,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="10/min"),
        )

    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, ArticleNotFoundError):
            raise HttpError(HTTPStatus.NOT_FOUND, "Article not found") from exception
        if isinstance(exception, ArticleAccessDeniedError):
            raise HttpError(HTTPStatus.FORBIDDEN, "Access denied") from exception
        return super().handle_exception(exception)

    def list_articles(self, request) -> ArticleListSchema:
        articles = self._article_service.list_published_articles()
        return ArticleListSchema(
            items=[
                ArticleSchema(
                    id=a.id,
                    title=a.title,
                    content=a.content,
                    author_id=a.author_id,
                    is_published=a.is_published,
                    created_at=a.created_at.isoformat(),
                )
                for a in articles
            ]
        )

    def create_article(
        self,
        request: AuthenticatedHttpRequest,
        request_body: CreateArticleRequestSchema,
    ) -> ArticleSchema:
        article = self._article_service.create_article(
            author=request.user,
            title=request_body.title,
            content=request_body.content,
        )
        return ArticleSchema(
            id=article.id,
            title=article.title,
            content=article.content,
            author_id=article.author_id,
            is_published=article.is_published,
            created_at=article.created_at.isoformat(),
        )

    def publish_article(
        self,
        request: AuthenticatedHttpRequest,
        article_id: int,
    ) -> ArticleSchema:
        article = self._article_service.publish_article(
            article_id=article_id,
            user=request.user,
        )
        return ArticleSchema(
            id=article.id,
            title=article.title,
            content=article.content,
            author_id=article.author_id,
            is_published=article.is_published,
            created_at=article.created_at.isoformat(),
        )
```

### 8. Register Controller in IoC

```python
# src/ioc/registries/delivery.py
from delivery.http.article.controllers import ArticleController


def _register_http_controllers(container: Container) -> None:
    # ... existing controllers ...
    container.register(ArticleController, scope=Scope.singleton)
```

### 9. Update API Factory

```python
# src/delivery/http/factories.py
from delivery.http.article.controllers import ArticleController


class NinjaAPIFactory:
    def __init__(
        self,
        # ... existing parameters ...
        article_controller: ArticleController,
    ) -> None:
        # ... existing assignments ...
        self._article_controller = article_controller

    def __call__(self, urls_namespace: str | None = None) -> NinjaAPI:
        # ... existing code ...

        article_router = Router(tags=["article"])
        ninja_api.add_router("/", article_router)
        self._article_controller.register(registry=article_router)

        return ninja_api
```

### 10. (Optional) Create Admin

```python
# src/delivery/http/article/admin.py
from django.contrib import admin

from core.article.models import Article


class ArticleAdmin(admin.ModelAdmin[Article]):
    list_display = ("id", "title", "author", "is_published", "created_at")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "content", "author__username")
```

Register in `AdminSiteFactory`:

```python
# src/delivery/http/factories.py
from core.article.models import Article
from delivery.http.article.admin import ArticleAdmin


class AdminSiteFactory:
    def __call__(self) -> AdminSite:
        # ... existing registrations ...
        default_site.register(Article, admin_class=ArticleAdmin)
        return default_site
```

## Verification

Start the server and test:

```bash
make dev

# List articles (public)
curl http://localhost:8000/v1/articles/

# Create article (authenticated)
TOKEN="your-jwt-token"
curl -X POST http://localhost:8000/v1/articles/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello World", "content": "This is my first article"}'
```

## Related

- [Service Layer](../concepts/service-layer.md) - Architecture pattern
- [Controller Pattern](../concepts/controller-pattern.md) - Request handling
- [Tutorial: Build a Todo List](../tutorial/index.md) - Full walkthrough
