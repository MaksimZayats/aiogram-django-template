import pytest
from punq import Container, Scope

from core.user.models import User
from ioc.container import get_container
from tasks.factories import CeleryAppFactory
from tests.integration.factories import (
    CeleryWorkerFactory,
    TestClientFactory,
    TestNinjaAPIFactory,
    UserFactory,
)


@pytest.fixture(scope="function")
def container() -> Container:
    return get_container()


# region Factories


@pytest.fixture(scope="function")
def api_factory(
    container: Container,
) -> TestNinjaAPIFactory:
    container.register(TestNinjaAPIFactory, scope=Scope.singleton)
    return container.resolve(TestNinjaAPIFactory)


@pytest.fixture(scope="function")
def test_client_factory(api_factory: TestNinjaAPIFactory) -> TestClientFactory:
    # NOTE FOR AI: we are creating new api + test client for each test function
    # to have a possibility to override some ioc registrations in specific tests
    return TestClientFactory(api_factory=api_factory)


@pytest.fixture(scope="function")
def user_factory(
    transactional_db: None,
    django_user_model: type[User],
) -> UserFactory:
    return UserFactory(user_model=django_user_model)


@pytest.fixture(scope="function")
def celery_app_factory(
    container: Container,
) -> CeleryAppFactory:
    return container.resolve(CeleryAppFactory)


@pytest.fixture(scope="function")
def celery_worker_factory(
    celery_app_factory: CeleryAppFactory,
) -> CeleryWorkerFactory:
    return CeleryWorkerFactory(celery_app_factory=celery_app_factory)


# endregion Factories
