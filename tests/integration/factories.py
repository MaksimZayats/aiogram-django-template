import uuid
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Any, cast

from celery.contrib.testing import worker
from celery.worker import WorkController
from django.contrib.auth.models import AbstractUser
from ninja.testing import TestClient
from punq import Container

from core.user.models import User
from delivery.http.factories import NinjaAPIFactory
from delivery.tasks.factories import CeleryAppFactory, TasksRegistryFactory
from delivery.tasks.registry import TasksRegistry
from infrastructure.jwt.services import JWTService


class BaseFactory(ABC):
    __test__ = False

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass


class ContainerBasedFactory(BaseFactory, ABC):
    def __init__(
        self,
        container: Container,
    ) -> None:
        self._container = container


class TestClientFactory(ContainerBasedFactory):
    def __call__(
        self,
        auth_for_user: User | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> TestClient:
        api_factory = self._container.resolve(NinjaAPIFactory)
        jwt_service = self._container.resolve(JWTService)

        headers = headers or {}

        if auth_for_user is not None:
            token = jwt_service.issue_access_token(user_id=auth_for_user.pk)
            headers["Authorization"] = f"Bearer {token}"

        return TestClient(
            api_factory(urls_namespace=str(uuid.uuid7())),
            headers=headers,
            **kwargs,
        )


class TestUserFactory(ContainerBasedFactory):
    def __call__(
        self,
        username: str = "test_user",
        password: str = "password123",  # noqa: S107
        email: str = "user@test.com",
    ) -> User:
        user_model = cast(
            type[User],
            self._container.resolve(type[AbstractUser]),  # type: ignore[arg-type, invalid-argument-type]
        )

        return user_model.objects.create_user(
            username=username,
            email=email,
            password=password,
        )


class TestCeleryWorkerFactory(ContainerBasedFactory):
    def __call__(self) -> AbstractContextManager[WorkController]:
        celery_app_factory = self._container.resolve(CeleryAppFactory)

        return worker.start_worker(
            app=celery_app_factory(),
            perform_ping_check=False,
        )


class TestTasksRegistryFactory(ContainerBasedFactory):
    def __call__(self) -> TasksRegistry:
        factory = self._container.resolve(TasksRegistryFactory)
        return factory()
