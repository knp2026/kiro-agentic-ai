
import pytest
from app.integration import external_data_source

def test_integration_with_external_data_source():
    data = external_data_source.fetch_patient_data(patient_id=1)
    assert data is not None
    assert "FirstName" in data
    assert "LastName" in data