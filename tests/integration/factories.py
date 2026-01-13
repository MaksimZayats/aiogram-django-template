import uuid
from contextlib import AbstractContextManager
from typing import Any

from celery.contrib.testing import worker
from celery.worker import WorkController
from ninja import NinjaAPI
from ninja.testing import TestClient

from core.user.models import User
from delivery.http.factories import NinjaAPIFactory
from delivery.tasks.factories import CeleryAppFactory


class TestNinjaAPIFactory(NinjaAPIFactory):
    __test__ = False

    def __call__(
        self,
        urls_namespace: str | None = None,  # noqa: ARG002
    ) -> NinjaAPI:
        return super().__call__(urls_namespace=str(uuid.uuid7()))


class TestClientFactory:
    __test__ = False

    def __init__(self, api_factory: TestNinjaAPIFactory) -> None:
        self._api_factory = api_factory

    def __call__(self, **kwargs: Any) -> TestClient:
        return TestClient(self._api_factory(), **kwargs)


class TestUserFactory:
    __test__ = False

    def __init__(self, user_model: type[User]) -> None:
        self._user_model = user_model

    def __call__(
        self,
        username: str = "test_user",
        password: str = "password123",  # noqa: S107
        email: str = "user@test.com",
    ) -> User:
        return self._user_model.objects.create_user(
            username=username,
            email=email,
            password=password,
        )


class TestCeleryWorkerFactory:
    def __init__(self, celery_app_factory: CeleryAppFactory) -> None:
        self._celery_app_factory = celery_app_factory

    def __call__(self) -> AbstractContextManager[WorkController]:
        return worker.start_worker(
            app=self._celery_app_factory(),
            perform_ping_check=False,
        )
