from functools import partial

import pytest
from punq import Container

from api.delivery.http.api import get_ninja_api
from api.user.models import User
from ioc.container import get_container
from tests.integration.factories import TestClientFactory, UserFactory


@pytest.fixture(scope="function")
def container() -> Container:
    return get_container()


@pytest.fixture(scope="function")
def test_client_factory(container: Container) -> TestClientFactory:
    return TestClientFactory(api_factory=partial(get_ninja_api, container=container))


@pytest.fixture(scope="function")
def user_factory(
    transactional_db: None,
    django_user_model: type[User],
) -> UserFactory:
    return UserFactory(user_model=django_user_model)
