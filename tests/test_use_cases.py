"""Automated Test Script for Use Case 1 & Use Case 2.

Use Case 1: Account Balance Inquiry
  - Customer asks about account balance
  - Intent classifier routes to Account Balance Agent
  - Agent extracts account ID, queries DynamoDB, returns balance

Use Case 2: Contract Lookup & Summary
  - Customer provides contract_id
  - System skips intent classification
  - Contract Agent retrieves record, generates AI summary via Bedrock

Run with: pytest test_use_cases.py -v
"""

import json
import os
from decimal import Decimal
from unittest.mock import patch, MagicMock

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from exceptions import BedrockError, DynamoDBError
from models import ChatRequest, ChatResponse


# ===========================================================================
# FIXTURES
# ===========================================================================


@pytest.fixture(autouse=True)
def aws_credentials():
    """Mock AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


def _create_accounts_table():
    """Create mock Accounts DynamoDB table with seed data."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(
        TableName="Accounts",
        KeySchema=[{"AttributeName": "account_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "account_id", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.put_item(Item={
        "account_id": "ACC-1001",
        "balance": Decimal("5250.75"),
        "currency": "USD",
        "account_type": "savings",
    })
    table.put_item(Item={
        "account_id": "ACC-1002",
        "balance": Decimal("1200.00"),
        "currency": "USD",
        "account_type": "checking",
    })
    table.put_item(Item={
        "account_id": "ACC-1003",
        "balance": Decimal("48000.00"),
        "currency": "USD",
        "account_type": "investment",
    })
    return table


def _create_contracts_table():
    """Create mock Contracts DynamoDB table with seed data."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(
        TableName="Contracts",
        KeySchema=[{"AttributeName": "contract_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "contract_id", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.put_item(Item={
        "contract_id": "C123",
        "amount": Decimal("50000"),
        "interest_rate": Decimal("0.05"),
        "duration": "5 years",
    })
    table.put_item(Item={
        "contract_id": "C456",
        "amount": Decimal("120000"),
        "interest_rate": Decimal("0.035"),
        "duration": "10 years",
    })
    return table


def _mock_classify_response(intent: str):
    """Create a mock Bedrock response for intent classification."""
    body_content = json.dumps({"content": [{"text": intent}]}).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_content
    return {"body": mock_body}


def _mock_summary_response(summary: str):
    """Create a mock Bedrock response for contract summarization."""
    body_content = json.dumps({"content": [{"text": summary}]}).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_content
    return {"body": mock_body}


def _get_client():
    """Get a fresh FastAPI TestClient."""
    from main import app
    return TestClient(app)


# ===========================================================================
# USE CASE 1: ACCOUNT BALANCE INQUIRY
# ===========================================================================


class TestUseCase1_AccountBalanceInquiry:
    """
    Use Case 1: Account Balance Inquiry

    Actor:       Bank Customer
    Trigger:     Customer sends a message asking about their account balance
    Precondition: Customer has a valid account (ACC-XXXX format)

    Tests cover:
      - Happy path: valid account returns balance with AUTO status
      - All 3 test accounts (ACC-1001, ACC-1002, ACC-1003)
      - Alternative flow: no account ID in message -> prompt
      - Alternative flow: account not found -> ESCALATE
      - Alternative flow: DynamoDB unavailable -> HTTP 502
      - Response schema validation
    """

    # --- Happy Path Tests ---

    @mock_aws
    def test_uc1_step1_to_7_acc1001_balance_inquiry(self):
        """
        UC1 Full Flow: Customer asks 'What is the balance of ACC-1001?'
        Expected: Balance 5250.75 USD, savings, status AUTO
        """
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_classify_response(
                "balance_inquiry"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "What is the balance of ACC-1001?"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        assert "ACC-1001" in data["message"]
        assert "5250.75" in data["message"]
        assert "USD" in data["message"]
        assert "savings" in data["message"]

    @mock_aws
    def test_uc1_acc1002_checking_account(self):
        """
        UC1: Customer asks about ACC-1002 (checking, $1,200.00)
        Expected: Balance 1200.0 USD, checking, status AUTO
        """
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_classify_response(
                "balance_inquiry"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "Show me the balance for ACC-1002"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        assert "1200.0" in data["message"]
        assert "USD" in data["message"]
        assert "checking" in data["message"]

    @mock_aws
    def test_uc1_acc1003_investment_account(self):
        """
        UC1: Customer asks about ACC-1003 (investment, $48,000.00)
        Expected: Balance 48000.0 USD, investment, status AUTO
        """
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_classify_response(
                "balance_inquiry"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "I need the balance of ACC-1003"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        assert "48000.0" in data["message"]
        assert "USD" in data["message"]
        assert "investment" in data["message"]

    # --- Intent Classification Step ---

    @mock_aws
    def test_uc1_step3_intent_classified_as_balance_inquiry(self):
        """
        UC1 Step 3: Bedrock classifies message as 'balance_inquiry'
        Verify intent classifier is called and routes correctly.
        """
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_classify_response(
                "balance_inquiry"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "What is the balance of ACC-1001?"
            })

            # Verify Bedrock was called for classification
            mock_runtime.invoke_model.assert_called_once()

        assert response.status_code == 200
        assert response.json()["status"] == "AUTO"

    # --- Alternative Flow: No Account ID ---

    @mock_aws
    def test_uc1_alt_no_account_id_prompts_user(self):
        """
        UC1 Alternative: No account ID in message
        Expected: Agent prompts 'Please provide your account ID'
        """
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_classify_response(
                "balance_inquiry"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "What is my account balance?"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        # Agent should prompt for account ID
        assert "account ID" in data["message"] or "ACC-" in data["message"]

    # --- Alternative Flow: Account Not Found ---

    @mock_aws
    def test_uc1_alt_account_not_found_escalates(self):
        """
        UC1 Alternative: Account not found
        Expected: status ESCALATE, message mentions escalating
        """
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_classify_response(
                "balance_inquiry"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "Balance for ACC-9999"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ESCALATE"
        assert "ACC-9999" in data["message"]

    # --- Alternative Flow: DynamoDB Unavailable ---

    @mock_aws
    def test_uc1_alt_dynamodb_unavailable_returns_502(self):
        """
        UC1 Alternative: DynamoDB unavailable
        Expected: HTTP 502, status ESCALATE
        """
        # Do NOT create accounts table -> simulates DynamoDB error
        with patch("intent_classifier.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_classify_response(
                "balance_inquiry"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "Balance for ACC-1001"
            })

        assert response.status_code == 502
        data = response.json()
        assert data["status"] == "ESCALATE"

    # --- Response Schema ---

    @mock_aws
    def test_uc1_response_schema_conforms(self):
        """
        UC1: Response always has message (str), contract_summary (null/str), status (AUTO/ESCALATE)
        """
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_classify_response(
                "balance_inquiry"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "Balance for ACC-1001"
            })

        data = response.json()
        assert "message" in data
        assert "contract_summary" in data
        assert "status" in data
        assert isinstance(data["message"], str)
        assert data["contract_summary"] is None  # balance inquiry has no summary
        assert data["status"] in ("AUTO", "ESCALATE")


# ===========================================================================
# USE CASE 2: CONTRACT LOOKUP & SUMMARY
# ===========================================================================


class TestUseCase2_ContractLookupAndSummary:
    """
    Use Case 2: Contract Lookup & Summary

    Actor:       Bank Customer
    Trigger:     Customer provides a contract_id in the request
    Precondition: Contract exists in the Contracts DynamoDB table

    Tests cover:
      - Happy path: valid contract returns summary with AUTO status
      - contract_id skips intent classification (direct routing)
      - Bedrock generates summary (max 1024 chars)
      - Alternative flow: contract not found -> ESCALATE
      - Alternative flow: Bedrock fails -> ESCALATE
      - Alternative flow: DynamoDB unavailable -> HTTP 502
      - Response schema validation
    """

    # --- Happy Path Tests ---

    @mock_aws
    def test_uc2_step1_to_7_contract_lookup_with_summary(self):
        """
        UC2 Full Flow: Customer sends message with contract_id='C123'
        Expected: Contract found, AI summary generated, status AUTO
        """
        _create_contracts_table()

        with patch("bedrock_client.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_summary_response(
                "• Contract C123: Loan of $50,000\n"
                "• Interest rate: 5% per annum\n"
                "• Duration: 5 years with monthly payments"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "Tell me about my contract",
                "contract_id": "C123"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        assert "C123" in data["message"]
        assert data["contract_summary"] is not None
        assert len(data["contract_summary"]) > 0
        assert len(data["contract_summary"]) <= 1024

    @mock_aws
    def test_uc2_second_contract_c456(self):
        """
        UC2: Contract C456 ($120,000, 3.5%, 10 years) returns summary.
        """
        _create_contracts_table()

        with patch("bedrock_client.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_summary_response(
                "• Contract C456: Mortgage of $120,000\n"
                "• Interest rate: 3.5% fixed\n"
                "• Duration: 10 years"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "Show my contract details",
                "contract_id": "C456"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        assert data["contract_summary"] is not None

    # --- Step 2: Skips Intent Classification ---

    @mock_aws
    def test_uc2_step2_skips_intent_classification(self):
        """
        UC2 Step 2: When contract_id is present, intent classification is NOT called.
        Verify IntentClassifier.classify() is never invoked.
        """
        _create_contracts_table()

        with patch("bedrock_client.boto3.client") as mock_bedrock:
            mock_runtime = MagicMock()
            mock_bedrock.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_summary_response(
                "Summary text"
            )

            with patch("main.IntentClassifier.classify") as mock_classify:
                client = _get_client()
                response = client.post("/chat", json={
                    "message": "Show contract",
                    "contract_id": "C123"
                })

                # Intent classifier should NOT be called when contract_id present
                mock_classify.assert_not_called()

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        assert data["contract_summary"] is not None

    # --- Step 6: Summary Max 1024 Chars ---

    @mock_aws
    def test_uc2_step6_summary_truncated_to_1024_chars(self):
        """
        UC2 Step 6: Bedrock summary is truncated to max 1024 characters.
        """
        _create_contracts_table()

        # Generate a very long summary (2000 chars)
        long_summary = "A" * 2000

        with patch("bedrock_client.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_summary_response(
                long_summary
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "Contract details",
                "contract_id": "C123"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["contract_summary"] is not None
        assert len(data["contract_summary"]) <= 1024

    # --- Alternative Flow: Contract Not Found ---

    @mock_aws
    def test_uc2_alt_contract_not_found_escalates(self):
        """
        UC2 Alternative: Contract not found in DynamoDB
        Expected: status ESCALATE, no summary
        """
        _create_contracts_table()

        client = _get_client()
        response = client.post("/chat", json={
            "message": "Show my contract",
            "contract_id": "NONEXISTENT"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ESCALATE"
        assert data["contract_summary"] is None

    # --- Alternative Flow: Bedrock Fails ---

    @mock_aws
    def test_uc2_alt_bedrock_fails_returns_escalate(self):
        """
        UC2 Alternative: Bedrock summarization fails
        Expected: status ESCALATE, summary generation failed
        """
        _create_contracts_table()

        with patch("bedrock_client.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            from botocore.exceptions import ClientError
            mock_runtime.invoke_model.side_effect = ClientError(
                {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
                "InvokeModel"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "Contract info",
                "contract_id": "C123"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ESCALATE"
        assert data["contract_summary"] is None

    # --- Alternative Flow: DynamoDB Unavailable ---

    @mock_aws
    def test_uc2_alt_dynamodb_unavailable_returns_502(self):
        """
        UC2 Alternative: DynamoDB unavailable (Contracts table doesn't exist)
        Expected: HTTP 502, status ESCALATE
        """
        # Do NOT create contracts table -> simulates DynamoDB error
        client = _get_client()
        response = client.post("/chat", json={
            "message": "Show contract",
            "contract_id": "C123"
        })

        assert response.status_code == 502
        data = response.json()
        assert data["status"] == "ESCALATE"
        assert data["contract_summary"] is None

    # --- Response Schema ---

    @mock_aws
    def test_uc2_response_schema_conforms(self):
        """
        UC2: Response has message (str), contract_summary (str), status (AUTO)
        """
        _create_contracts_table()

        with patch("bedrock_client.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_summary_response(
                "• Summary bullet 1\n• Summary bullet 2\n• Summary bullet 3"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "Contract info",
                "contract_id": "C123"
            })

        data = response.json()
        assert "message" in data
        assert "contract_summary" in data
        assert "status" in data
        assert isinstance(data["message"], str)
        assert isinstance(data["contract_summary"], str)
        assert data["status"] in ("AUTO", "ESCALATE")

    @mock_aws
    def test_uc2_response_contains_contract_id_in_message(self):
        """
        UC2: Success response message contains the contract_id.
        """
        _create_contracts_table()

        with patch("bedrock_client.boto3.client") as mock_boto:
            mock_runtime = MagicMock()
            mock_boto.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_summary_response(
                "Summary"
            )

            client = _get_client()
            response = client.post("/chat", json={
                "message": "Contract lookup",
                "contract_id": "C123"
            })

        data = response.json()
        assert data["status"] == "AUTO"
        assert "C123" in data["message"]
