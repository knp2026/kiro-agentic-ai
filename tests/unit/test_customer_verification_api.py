
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_successful_verification():
    response = client.post(
        "/auth/verify",
        json={"customer_id": "valid_customer_id"},
        headers={"Authorization": "Bearer valid_access_token"}
    )
    assert response.status_code == 200

def test_failed_verification():
    response = client.post(
        "/auth/verify",
        json={"customer_id": "invalid_customer_id"},
        headers={"Authorization": "Bearer valid_access_token"}
    )
    assert response.status_code == 403