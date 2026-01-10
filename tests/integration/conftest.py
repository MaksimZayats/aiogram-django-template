import uuid
from functools import partial

import pytest
from punq import Container

from api.user.models import User
from delivery.http.api import get_ninja_api
from ioc.container import get_container
from tests.integration.factories import TestClientFactory, UserFactory


@pytest.fixture(scope="function")
def container() -> Container:
    return get_container()


@pytest.fixture(scope="function")
def test_client_factory(container: Container) -> TestClientFactory:
    # NOTE FOR AI: we are creating new api + test client for each test function
    # to have a possibility to override some ioc registrations in specific tests
    return TestClientFactory(
        api_factory=partial(
            get_ninja_api,
            container=container,
            urls_namespace=str(uuid.uuid4()),
        ),
    )


@pytest.fixture(scope="function")
def user_factory(
    transactional_db: None,
    django_user_model: type[User],
) -> UserFactory:
    return UserFactory(user_model=django_user_model)
