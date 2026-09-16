
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_patient():
    response = client.post(
        "/api/patients",
        json={
            "FirstName": "John",
            "LastName": "Doe",
            "DateOfBirth": "1990-01-01",
            "Gender": "Male",
            "ContactInformation": {
                "Phone": "1234567890",
                "Email": "johndoe@example.com",
                "Address": "123 Main St, City, State, Zip"
            },
            "EmergencyContact": {
                "Name": "Jane Doe",
                "Phone": "0987654321",
                "Relationship": "Spouse"
            }
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "PatientID" in data

def test_get_patient():
    # Assuming a patient with ID 1 exists
    response = client.get("/api/patients/1")
    assert response.status_code == 200
    data = response.json()
    assert data["FirstName"] == "John"