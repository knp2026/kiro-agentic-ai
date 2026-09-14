
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_successful_authentication():
    response = client.post(
        "/auth/authenticate",
        json={"username": "test_user", "password": "test_password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_failed_authentication():
    response = client.post(
        "/auth/authenticate",
        json={"username": "test_user", "password": "wrong_password"}
    )
    assert response.status_code == 401