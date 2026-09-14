
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_customer_verification_api():
    # Authenticate to get access token
    auth_response = client.post(
        "/auth/authenticate",
        json={"username": "test_user", "password": "test_password"}
    )
    access_token = auth_response.json()["access_token"]

    # Test successful verification
    response = client.post(
        "/auth/verify",
        json={"customer_id": "test_customer_id"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

    # Test failed verification
    response = client.post(
        "/auth/verify",
        json={"customer_id": "invalid_customer_id"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 403