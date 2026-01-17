import pytest

from infrastructure.punq.container import AutoRegisteringContainer
from ioc.container import ContainerFactory
from tests.integration.factories import (
    TestCeleryWorkerFactory,
    TestClientFactory,
    TestTasksRegistryFactory,
    TestUserFactory,
)


@pytest.fixture(scope="function")
def container() -> AutoRegisteringContainer:
    container_factory = ContainerFactory()
    return container_factory()


# region Factories


@pytest.fixture(scope="function")
def test_client_factory(container: AutoRegisteringContainer) -> TestClientFactory:
    return TestClientFactory(container=container)


@pytest.fixture(scope="function")
def user_factory(
    transactional_db: None,
    container: AutoRegisteringContainer,
) -> TestUserFactory:
    return TestUserFactory(container=container)


@pytest.fixture(scope="function")
def celery_worker_factory(container: AutoRegisteringContainer) -> TestCeleryWorkerFactory:
    return TestCeleryWorkerFactory(container=container)


@pytest.fixture(scope="function")
def tasks_registry_factory(container: AutoRegisteringContainer) -> TestTasksRegistryFactory:
    return TestTasksRegistryFactory(container=container)


# endregion Factories
