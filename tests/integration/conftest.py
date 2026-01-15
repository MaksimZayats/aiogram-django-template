from uuid import uuid7

import pytest
from django.contrib.auth.models import AbstractUser
from punq import Container, Scope
from pytest_django.fixtures import SettingsWrapper

from core.user.models import User
from ioc.container import get_container
from tests.integration.factories import (
    TestCeleryWorkerFactory,
    TestClientFactory,
    TestTasksRegistryFactory,
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
    container.register(type[AbstractUser], instance=django_user_model, scope=Scope.singleton)

    return container


# region Factories


@pytest.fixture(scope="function")
def test_client_factory(container: Container) -> TestClientFactory:
    return TestClientFactory(container=container)


@pytest.fixture(scope="function")
def user_factory(
    transactional_db: None,
    container: Container,
) -> TestUserFactory:
    return TestUserFactory(container=container)


@pytest.fixture(scope="function")
def celery_worker_factory(container: Container) -> TestCeleryWorkerFactory:
    return TestCeleryWorkerFactory(container=container)


@pytest.fixture(scope="function")
def tasks_registry_factory(container: Container) -> TestTasksRegistryFactory:
    return TestTasksRegistryFactory(container=container)


# endregion Factories
