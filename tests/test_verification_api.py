
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_verify_success():
    response = client.post(
        "/auth/verify",
        json={"customer_id": "123456"},
        headers={"Authorization": "Bearer valid_access_token"}
    )
    assert response.status_code == 200

def test_verify_failure_unauthorized():
    response = client.post(
        "/auth/verify",
        json={"customer_id": "123456"},
        headers={"Authorization": "Bearer invalid_access_token"}
    )
    assert response.status_code == 401

def test_verify_failure_invalid_customer_id():
    response = client.post(
        "/auth/verify",
        json={"customer_id": "invalid_customer_id"},
        headers={"Authorization": "Bearer valid_access_token"}
    )
    assert response.status_code == 404