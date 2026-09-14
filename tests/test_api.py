import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

def test_authenticate(client):
    response = client.post(
        "/auth/authenticate",
        json={"username": "test_user", "password": "test_password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()