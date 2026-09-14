
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def valid_credentials():
    return {"username": "test_user", "password": "test_password"}

def test_authenticate_valid_credentials(valid_credentials):
    response = client.post("/auth/authenticate", json=valid_credentials)
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_authenticate_invalid_credentials():
    invalid_credentials = {"username": "invalid_user", "password": "invalid_password"}
    response = client.post("/auth/authenticate", json=invalid_credentials)
    assert response.status_code == 401