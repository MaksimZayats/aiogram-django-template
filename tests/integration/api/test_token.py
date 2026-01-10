from ninja.testing import TestClient


def test_token(test_client: TestClient) -> None:
    response = test_client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
