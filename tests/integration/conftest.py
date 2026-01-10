import pytest
from ninja.testing import TestClient

from api.delivery.http.api import get_ninja_api


@pytest.fixture(scope="function")
def test_client() -> TestClient:
    api = get_ninja_api()
    return TestClient(api)
