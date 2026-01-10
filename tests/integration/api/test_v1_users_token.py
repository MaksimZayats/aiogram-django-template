from http import HTTPStatus

import pytest
from punq import Container

from api.infrastructure.jwt.service import JWTService
from api.user.delivery.http.controllers import TokenResponseSchema
from tests.integration.conftest import UserFactory
from tests.integration.factories import TestClientFactory


@pytest.mark.django_db(transaction=True)
def test_jwt_token_generation(
    test_client_factory: TestClientFactory,
    user_factory: UserFactory,
    container: Container,
) -> None:
    user = user_factory(username="test", password="123")  # noqa: S106

    jwt_service = container.resolve(JWTService)
    test_client = test_client_factory()
    response = test_client.post(
        "/v1/users/me/token",
        json={"username": "test", "password": "123"},
    )

    assert response.status_code == HTTPStatus.OK

    response_data = TokenResponseSchema.model_validate(response.json())
    payload = jwt_service.decode_token(response_data.access_token)
    assert payload["sub"] == str(user.pk)
