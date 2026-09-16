
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def valid_access_token():
    # Assume a valid access token is obtained from the authentication API
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImV4cCI6MTYwMjMsImF1dGhvcml0aWVzIjpbInN1YiI6InNlY3JldAoibGlua190b3JhZ2UiLCJuYmYiOjE2MDE2NTYsImV4cCI6MTYwMjYzMiwiaWF0IjoxNjAxNjU2LCJqdGkiOiIxMjM0MjcifQ.S9c54q-pJR_q8dU10LyhKuHG9z8Khqy3Ljt6FfDjQgU"

def test_successful_verification(valid_access_token):
    customer_id = "123"
    headers = {"Authorization": f"Bearer {valid_access_token}"}
    response = client.post(f"/verify/{customer_id}", headers=headers)
    assert response.status_code == 200

def test_failed_verification(valid_access_token):
    invalid_customer_id = "456"
    headers = {"Authorization": f"Bearer {valid_access_token}"}
    response = client.post(f"/verify/{invalid_customer_id}", headers=headers)
    assert response.status_code == 403