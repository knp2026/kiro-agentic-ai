
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_schedule_appointment():
    response = client.post(
        "/api/appointments",
        json={
            "PatientID": 1,
            "ProviderID": 1,
            "AppointmentDate": "2022-01-02",
            "AppointmentTime": "10:00"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "AppointmentID" in data

def test_get_appointment():
    # Assuming an appointment with ID 1 exists
    response = client.get("/api/appointments/1")
    assert response.status_code == 200
    data = response.json()
    assert data["AppointmentDate"] == "2022-01-02"