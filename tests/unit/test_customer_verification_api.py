
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def valid_access_token():
    # Assuming a valid access token is obtained from the authentication API
    return "valid_access_token"

def test_verify_valid_customer_id(valid_access_token):
    headers = {"Authorization": f"Bearer {valid_access_token}"}
    response = client.post("/verify", json={"customer_id": "valid_customer_id"}, headers=headers)
    assert response.status_code == 200

def test_verify_invalid_customer_id(valid_access_token):
    headers = {"Authorization": f"Bearer {valid_access_token}"}
    response = client.post("/verify", json={"customer_id": "invalid_customer_id"}, headers=headers)
    assert response.status_code == 404