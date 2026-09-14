
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_customer_authentication_api():
    # Test successful authentication
    response = client.post(
        "/auth/authenticate",
        json={"username": "test_user", "password": "test_password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

    # Test failed authentication
    response = client.post(
        "/auth/authenticate",
        json={"username": "test_user", "password": "wrong_password"}
    )
    assert response.status_code == 401