"""Integration tests for end-to-end /chat flows.

Tests backward compatibility of the contract_id flow, end-to-end balance
inquiry flows, intent classification routing, and ChatResponse schema
validation.

Requirements: 4.1, 4.2, 4.3, 4.4, 3.3
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


@pytest.fixture(autouse=True)
def aws_credentials():
    """Mock AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


def _create_contracts_table():
    """Create mock Contracts DynamoDB table with test data."""
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


def _create_accounts_table():
    """Create mock Accounts DynamoDB table with test data."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(
        TableName="Accounts",
        KeySchema=[{"AttributeName": "account_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "account_id", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    # Test data per Requirements 3.3
    table.put_item(
        Item={
            "account_id": "ACC-1001",
            "balance": Decimal("5250.75"),
            "currency": "USD",
            "account_type": "savings",
        }
    )
    table.put_item(
        Item={
            "account_id": "ACC-1002",
            "balance": Decimal("1200.00"),
            "currency": "USD",
            "account_type": "checking",
        }
    )
    table.put_item(
        Item={
            "account_id": "ACC-1003",
            "balance": Decimal("48000.00"),
            "currency": "USD",
            "account_type": "investment",
        }
    )
    return table


def _mock_bedrock_summary_response(summary_text: str):
    """Create a mock Bedrock invoke_model response for contract summaries."""
    body_content = json.dumps({
        "content": [{"text": summary_text}],
    }).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_content
    return {"body": mock_body}


def _mock_bedrock_classify_response(intent: str):
    """Create a mock Bedrock invoke_model response for intent classification."""
    body_content = json.dumps({
        "content": [{"text": intent}],
    }).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_content
    return {"body": mock_body}


def _get_test_client():
    """Get a fresh TestClient (re-import to avoid module caching issues)."""
    from main import app
    return TestClient(app)


# ===========================================================================
# 1. Contract flow (backward compatibility)
# ===========================================================================


class TestContractFlowBackwardCompatibility:
    """Test contract_id flow produces identical responses to current behavior."""

    @mock_aws
    def test_existing_contract_returns_success_with_summary(self):
        """POST /chat with contract_id=existing → success with summary."""
        _create_contracts_table()

        with patch("bedrock_client.boto3.client") as mock_boto_client:
            mock_runtime = MagicMock()
            mock_boto_client.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_bedrock_summary_response(
                "• Contract C123\n• Amount: 50000\n• Duration: 5 years"
            )

            client = _get_test_client()
            response = client.post(
                "/chat",
                json={"message": "Tell me about my contract", "contract_id": "C123"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        assert data["contract_summary"] is not None
        assert "C123" in data["message"]
        # Validate schema fields
        assert "message" in data
        assert "contract_summary" in data
        assert "status" in data

    @mock_aws
    def test_nonexistent_contract_returns_escalate(self):
        """POST /chat with contract_id=nonexistent → ESCALATE."""
        _create_contracts_table()

        client = _get_test_client()
        response = client.post(
            "/chat",
            json={"message": "Show my contract", "contract_id": "NONEXISTENT"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ESCALATE"
        assert data["contract_summary"] is None

    @mock_aws
    def test_contract_dynamo_error_returns_502(self):
        """POST /chat with contract_id + DynamoDB error → HTTP 502."""
        # Don't create the table to simulate DynamoDB error
        client = _get_test_client()
        response = client.post(
            "/chat",
            json={"message": "Get contract", "contract_id": "C123"},
        )

        assert response.status_code == 502
        data = response.json()
        assert data["status"] == "ESCALATE"
        assert data["contract_summary"] is None


# ===========================================================================
# 2. Balance inquiry flow
# ===========================================================================


class TestBalanceInquiryFlow:
    """Test balance inquiry flow end-to-end with test data."""

    @mock_aws
    def test_acc_1001_savings_balance(self):
        """POST /chat with ACC-1001 (savings, 5250.75 USD) → balance response, status AUTO."""
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto_client:
            mock_runtime = MagicMock()
            mock_boto_client.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_bedrock_classify_response(
                "balance_inquiry"
            )

            client = _get_test_client()
            response = client.post(
                "/chat",
                json={"message": "What is the balance for ACC-1001?"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        assert "5250.75" in data["message"]
        assert "USD" in data["message"]
        assert "savings" in data["message"]

    @mock_aws
    def test_acc_1002_checking_balance(self):
        """POST /chat with ACC-1002 (checking, 1200.00 USD) → balance response, status AUTO."""
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto_client:
            mock_runtime = MagicMock()
            mock_boto_client.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_bedrock_classify_response(
                "balance_inquiry"
            )

            client = _get_test_client()
            response = client.post(
                "/chat",
                json={"message": "Check balance for account ACC-1002"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        assert "1200.0" in data["message"]
        assert "USD" in data["message"]
        assert "checking" in data["message"]

    @mock_aws
    def test_acc_1003_investment_balance(self):
        """POST /chat with ACC-1003 (investment, 48000.00 USD) → balance response, status AUTO."""
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto_client:
            mock_runtime = MagicMock()
            mock_boto_client.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_bedrock_classify_response(
                "balance_inquiry"
            )

            client = _get_test_client()
            response = client.post(
                "/chat",
                json={"message": "I need the balance of ACC-1003"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        assert "48000.0" in data["message"]
        assert "USD" in data["message"]
        assert "investment" in data["message"]

    @mock_aws
    def test_nonexistent_account_returns_escalate(self):
        """POST /chat with non-existent account → ESCALATE."""
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto_client:
            mock_runtime = MagicMock()
            mock_boto_client.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_bedrock_classify_response(
                "balance_inquiry"
            )

            client = _get_test_client()
            response = client.post(
                "/chat",
                json={"message": "What is the balance for ACC-9999?"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ESCALATE"
        assert "ACC-9999" in data["message"]

    @mock_aws
    def test_message_without_account_id_prompts_user(self):
        """POST /chat without account_id pattern → prompts for account_id, status AUTO."""
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto_client:
            mock_runtime = MagicMock()
            mock_boto_client.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_bedrock_classify_response(
                "balance_inquiry"
            )

            client = _get_test_client()
            response = client.post(
                "/chat",
                json={"message": "What is my account balance?"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        assert "account ID" in data["message"] or "ACC-" in data["message"]


# ===========================================================================
# 3. Intent classification routing
# ===========================================================================


class TestIntentClassificationRouting:
    """Test intent classification routing dispatches to correct agents."""

    @mock_aws
    def test_balance_inquiry_intent_invokes_account_balance_agent(self):
        """Mock IntentClassifier returning 'balance_inquiry' → AccountBalanceAgent invoked."""
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto_client:
            mock_runtime = MagicMock()
            mock_boto_client.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_bedrock_classify_response(
                "balance_inquiry"
            )

            with patch(
                "main.AccountBalanceAgent.handle", wraps=None
            ) as mock_handle:
                mock_handle.return_value = ChatResponse(
                    message="Balance info", contract_summary=None, status="AUTO"
                )

                client = _get_test_client()
                response = client.post(
                    "/chat",
                    json={"message": "Check balance ACC-1001"},
                )

                mock_handle.assert_called_once()

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"

    @mock_aws
    def test_contract_inquiry_intent_returns_contract_id_prompt(self):
        """Mock IntentClassifier returning 'contract_inquiry' → contract_id prompt returned."""
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto_client:
            mock_runtime = MagicMock()
            mock_boto_client.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_bedrock_classify_response(
                "contract_inquiry"
            )

            client = _get_test_client()
            response = client.post(
                "/chat",
                json={"message": "I want to see my contract details"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "AUTO"
        assert "contract_id" in data["message"]

    @mock_aws
    def test_bedrock_error_returns_escalate(self):
        """Mock IntentClassifier raising BedrockError → ESCALATE response."""
        _create_accounts_table()

        with patch(
            "main.IntentClassifier.classify",
            side_effect=BedrockError(reason="Service unavailable"),
        ):
            client = _get_test_client()
            response = client.post(
                "/chat",
                json={"message": "Check my balance"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ESCALATE"


# ===========================================================================
# 4. Schema validation
# ===========================================================================


class TestSchemaValidation:
    """Verify all responses conform to ChatResponse schema."""

    def _validate_chat_response_schema(self, data: dict):
        """Assert response conforms to ChatResponse schema."""
        assert "message" in data, "Response missing 'message' field"
        assert "contract_summary" in data, "Response missing 'contract_summary' field"
        assert "status" in data, "Response missing 'status' field"
        assert isinstance(data["message"], str)
        assert data["contract_summary"] is None or isinstance(
            data["contract_summary"], str
        )
        assert data["status"] in ("AUTO", "ESCALATE")

    @mock_aws
    def test_contract_success_response_schema(self):
        """Successful contract response conforms to ChatResponse schema."""
        _create_contracts_table()

        with patch("bedrock_client.boto3.client") as mock_boto_client:
            mock_runtime = MagicMock()
            mock_boto_client.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_bedrock_summary_response(
                "Summary text"
            )

            client = _get_test_client()
            response = client.post(
                "/chat",
                json={"message": "Show contract", "contract_id": "C123"},
            )

        self._validate_chat_response_schema(response.json())

    @mock_aws
    def test_contract_not_found_response_schema(self):
        """Contract not found response conforms to ChatResponse schema."""
        _create_contracts_table()

        client = _get_test_client()
        response = client.post(
            "/chat",
            json={"message": "Show contract", "contract_id": "MISSING"},
        )

        self._validate_chat_response_schema(response.json())

    @mock_aws
    def test_balance_success_response_schema(self):
        """Balance inquiry success response conforms to ChatResponse schema."""
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto_client:
            mock_runtime = MagicMock()
            mock_boto_client.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_bedrock_classify_response(
                "balance_inquiry"
            )

            client = _get_test_client()
            response = client.post(
                "/chat",
                json={"message": "Balance for ACC-1001"},
            )

        self._validate_chat_response_schema(response.json())

    @mock_aws
    def test_balance_not_found_response_schema(self):
        """Balance not found response conforms to ChatResponse schema."""
        _create_accounts_table()

        with patch("intent_classifier.boto3.client") as mock_boto_client:
            mock_runtime = MagicMock()
            mock_boto_client.return_value = mock_runtime
            mock_runtime.invoke_model.return_value = _mock_bedrock_classify_response(
                "balance_inquiry"
            )

            client = _get_test_client()
            response = client.post(
                "/chat",
                json={"message": "Balance for ACC-9999"},
            )

        self._validate_chat_response_schema(response.json())

    @mock_aws
    def test_classification_failure_response_schema(self):
        """Classification failure response conforms to ChatResponse schema."""
        with patch(
            "main.IntentClassifier.classify",
            side_effect=BedrockError(reason="Timeout"),
        ):
            client = _get_test_client()
            response = client.post(
                "/chat",
                json={"message": "Hello"},
            )

        self._validate_chat_response_schema(response.json())

    @mock_aws
    def test_dynamo_error_response_schema(self):
        """DynamoDB error response conforms to ChatResponse schema."""
        # Don't create table → triggers DynamoDB error
        client = _get_test_client()
        response = client.post(
            "/chat",
            json={"message": "Show contract", "contract_id": "C123"},
        )

        data = response.json()
        # HTTP 502 responses also follow the schema
        assert "message" in data
        assert "contract_summary" in data
        assert "status" in data
        assert data["status"] in ("AUTO", "ESCALATE")
