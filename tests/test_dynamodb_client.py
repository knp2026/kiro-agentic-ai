"""Unit tests for DynamoDBClient."""

import os
from decimal import Decimal

import boto3
import pytest
from moto import mock_aws

from dynamodb_client import DynamoDBClient
from exceptions import DynamoDBError
from models import ContractRecord


@pytest.fixture(autouse=True)
def aws_credentials():
    """Mock AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


def _create_contracts_table():
    """Helper to create a mock DynamoDB Contracts table with test data."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(
        TableName="Contracts",
        KeySchema=[{"AttributeName": "contract_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "contract_id", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.put_item(
        Item={
            "contract_id": "C123",
            "amount": Decimal("50000"),
            "interest_rate": Decimal("0.05"),
            "duration": "5 years",
        }
    )
    return table


@mock_aws
def test_get_contract_found():
    """Test retrieving an existing contract returns ContractRecord."""
    _create_contracts_table()
    client = DynamoDBClient(table_name="Contracts")
    result = client.get_contract("C123")

    assert result is not None
    assert isinstance(result, ContractRecord)
    assert result.contract_id == "C123"
    assert result.amount == 50000.0
    assert result.interest_rate == 0.05
    assert result.duration == "5 years"


@mock_aws
def test_get_contract_not_found():
    """Test retrieving a non-existent contract returns None."""
    _create_contracts_table()
    client = DynamoDBClient(table_name="Contracts")
    result = client.get_contract("NONEXISTENT")

    assert result is None


def test_get_contract_empty_id_raises_error():
    """Test empty contract_id raises DynamoDBError."""
    client = DynamoDBClient.__new__(DynamoDBClient)
    client.table_name = "Contracts"

    with pytest.raises(DynamoDBError) as exc_info:
        client.get_contract("")

    assert "valid contract_id is required" in str(exc_info.value)
    assert exc_info.value.contract_id == ""


def test_get_contract_none_id_raises_error():
    """Test None contract_id raises DynamoDBError."""
    client = DynamoDBClient.__new__(DynamoDBClient)
    client.table_name = "Contracts"

    with pytest.raises(DynamoDBError) as exc_info:
        client.get_contract(None)

    assert "valid contract_id is required" in str(exc_info.value)
    assert exc_info.value.contract_id == ""
    assert exc_info.value.reason == "A valid contract_id is required"


@mock_aws
def test_get_contract_client_error_raises_dynamodb_error():
    """Test that ClientError from DynamoDB raises DynamoDBError."""
    # Don't create the table - this will cause a ResourceNotFoundException
    client = DynamoDBClient(table_name="NonExistentTable")

    with pytest.raises(DynamoDBError) as exc_info:
        client.get_contract("C123")

    assert exc_info.value.contract_id == "C123"
    assert exc_info.value.reason != ""
