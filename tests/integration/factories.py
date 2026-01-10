from collections.abc import Callable
from typing import Any

from ninja import NinjaAPI
from ninja.testing import TestClient

from core.user.models import User


class TestClientFactory:
    __test__ = False

    def __init__(self, api_factory: Callable[[], NinjaAPI]) -> None:
        self._api_factory = api_factory

    def __call__(self, **kwargs: Any) -> TestClient:
        return TestClient(self._api_factory(), **kwargs)


class UserFactory:
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
