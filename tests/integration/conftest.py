from uuid import uuid7

import pytest
from punq import Container, Scope
from pytest_django.fixtures import SettingsWrapper

from core.user.models import User
from delivery.tasks.factories import CeleryAppFactory
from delivery.tasks.registry import TasksRegistry
from ioc.container import get_container
from tests.integration.factories import (
    TestCeleryWorkerFactory,
    TestClientFactory,
    TestNinjaAPIFactory,
    TestUserFactory,
)


@pytest.fixture(scope="function", autouse=True)
def _configure_settings(settings: SettingsWrapper) -> None:
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": f"test-cache-{uuid7()}",
        },
    }


@pytest.fixture(scope="function")
def container(django_user_model: type[User]) -> Container:
    container = get_container()
    container.register(TestNinjaAPIFactory, scope=Scope.singleton)
    container.register(TestClientFactory, scope=Scope.singleton)
    container.register(TestCeleryWorkerFactory, scope=Scope.singleton)
    container.register(type[User], instance=django_user_model, scope=Scope.singleton)
    container.register(TestUserFactory, scope=Scope.singleton)

    return container


# region Factories


@pytest.fixture(scope="function")
def test_client_factory(container: Container) -> TestClientFactory:
    return container.resolve(TestClientFactory)


@pytest.fixture(scope="function")
def user_factory(
    transactional_db: None,
    container: Container,
) -> TestUserFactory:
    return container.resolve(TestUserFactory)


@pytest.fixture(scope="function")
def celery_app_factory(container: Container) -> CeleryAppFactory:
    return container.resolve(CeleryAppFactory)


@pytest.fixture(scope="function")
def celery_worker_factory(container: Container) -> TestCeleryWorkerFactory:
    return container.resolve(TestCeleryWorkerFactory)


@pytest.fixture(scope="function")
def tasks_registry(container: Container) -> TasksRegistry:
    return container.resolve(TasksRegistry)


# endregion Factories
