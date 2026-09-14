
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_successful_verification():
    # Assuming a valid access_token is obtained
    access_token = "valid_access_token"
    response = client.post(
        "/verify",
        json={"customer_id": "12345"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

def test_failed_verification():
    # Assuming a valid access_token is obtained
    access_token = "valid_access_token"
    response = client.post(
        "/verify",
        json={"customer_id": "invalid_customer_id"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401