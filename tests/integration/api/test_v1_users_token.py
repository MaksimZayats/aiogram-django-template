from http import HTTPStatus

import pytest
from punq import Container

from api.user.delivery.http.controllers import TokenResponseSchema, UserSchema
from api.user.models import User
from tests.integration.conftest import UserFactory
from tests.integration.factories import TestClientFactory

_TEST_PASSWORD = "test-password"  # noqa: S105


@pytest.fixture(scope="function")
def user(user_factory: UserFactory) -> User:
    return user_factory(username="test", password=_TEST_PASSWORD)


@pytest.mark.django_db(transaction=True)
def test_jwt_token_generation(
    test_client_factory: TestClientFactory,
    user: User,
) -> None:
    test_client = test_client_factory()

    response = test_client.post(
        "/v1/users/me/token",
        json={"username": user.username, "password": _TEST_PASSWORD},
    )

    response_data = TokenResponseSchema.model_validate(response.json())
    assert response.status_code == HTTPStatus.OK

    response = test_client.get(
        "/v1/users/me",
        headers={"Authorization": f"Bearer {response_data.access_token}"},
    )

    user_data = UserSchema.model_validate(response.json())
    assert response.status_code == HTTPStatus.OK

    assert user_data.id == user.pk
    assert user_data.username == user.username
    assert user_data.email == user.email


@pytest.mark.django_db(transaction=True)
def test_jwt_token_refresh_revoke_flow(
    test_client_factory: TestClientFactory,
    user: User,
    container: Container,
) -> None:
    test_client = test_client_factory()
    response = test_client.post(
        "/v1/users/me/token",
        json={"username": user.username, "password": _TEST_PASSWORD},
    )
    token_response = TokenResponseSchema.model_validate(response.json())

    response = test_client.post(
        "/v1/users/me/token/refresh",
        json={"refresh_token": token_response.refresh_token},
    )
    token_response = TokenResponseSchema.model_validate(response.json())

    response = test_client.post(
        "/v1/users/me/token/revoke",
        json={"refresh_token": token_response.refresh_token},
        headers={"Authorization": f"Bearer {token_response.access_token}"},
    )
    assert response.status_code == HTTPStatus.OK

    response = test_client.post(
        "/v1/users/me/token/refresh",
        json={"refresh_token": token_response.refresh_token},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
