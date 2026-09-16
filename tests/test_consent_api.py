
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_consent():
    response = client.post(
        "/api/consents",
        json={
            "PatientID": 1,
            "ConsentType": "Medical Records Access",
            "ConsentStatus": "Active",
            "ConsentDate": "2022-01-01"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "ConsentID" in data

def test_get_consent():
    # Assuming a consent with ID 1 exists
    response = client.get("/api/consents/1")
    assert response.status_code == 200
    data = response.json()
    assert data["ConsentType"] == "Medical Records Access"