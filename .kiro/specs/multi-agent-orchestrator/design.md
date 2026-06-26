# Design Document

## Overview

This design adds multi-agent orchestration to the existing AI Banking Assistant. The system introduces an LLM-based intent classifier that analyzes user messages and routes them to the appropriate agent — either the existing Contract Agent or a new Account Balance Agent. The orchestration layer fits inside the existing `/chat` endpoint, preserving backward compatibility for requests that include a `contract_id`.

## Architecture

### High-Level Flow

```
POST /chat (ChatRequest)
       │
       ▼
┌─────────────────────┐
│  Orchestrator       │
│  (main.py /chat)    │
├─────────────────────┤
│ contract_id present?│──Yes──▶ Contract Agent (existing flow)
│         │           │
│         No          │
│         ▼           │
│ Intent Classifier   │
│ (Bedrock LLM call)  │
│         │           │
│    ┌────┴────┐      │
│    ▼         ▼      │
│ "balance"  "contract"│
└────┬─────────┬──────┘
     │         │
     ▼         ▼
Account     Contract
Balance     Agent
Agent       (existing)
     │         │
     ▼         ▼
Accounts   Contracts
Table      Table
(DynamoDB) (DynamoDB)
```

### Component Interaction

1. The `/chat` endpoint receives a `ChatRequest`
2. If `contract_id` is present, the request goes directly to the Contract Agent (existing behavior)
3. If no `contract_id`, the Orchestrator invokes the Intent Classifier
4. The Intent Classifier calls Bedrock to classify the message as `"balance_inquiry"` or `"contract_inquiry"`
5. Based on the classified intent, the Orchestrator delegates to the appropriate agent
6. The agent processes the request and returns a `ChatResponse`

## Components and Interfaces

### 1. Intent Classifier (`intent_classifier.py`)

A dedicated module that encapsulates the Bedrock LLM call for intent classification.

```python
"""Intent classification module for the Multi-Agent Orchestrator."""

import json
import logging
from typing import Literal

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ReadTimeoutError, ConnectTimeoutError

from exceptions import BedrockError

logger = logging.getLogger(__name__)

IntentType = Literal["balance_inquiry", "contract_inquiry"]

CLASSIFICATION_PROMPT_TEMPLATE = """Classify the following user message into exactly one intent.

Possible intents:
- "balance_inquiry": The user wants to check an account balance or account information.
- "contract_inquiry": The user wants to look up or ask about a contract.

User message: {message}

Respond with ONLY the intent name, nothing else. Your response must be exactly one of: balance_inquiry, contract_inquiry"""


class IntentClassifier:
    """Classifies user messages into intents using Bedrock LLM.

    Attributes:
        model_id: The Bedrock model identifier for classification.
        timeout: Timeout in seconds for Bedrock API calls.
    """

    VALID_INTENTS: set[str] = {"balance_inquiry", "contract_inquiry"}

    def __init__(
        self,
        model_id: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        timeout: int = 30,
    ) -> None:
        self.model_id = model_id
        self.timeout = timeout

        config = Config(
            region_name="us-east-1",
            read_timeout=timeout,
            connect_timeout=timeout,
            retries={"max_attempts": 0},
        )
        self._client = boto3.client("bedrock-runtime", config=config)

    def classify(self, message: str) -> IntentType:
        """Classify a user message into an intent.

        Args:
            message: The user's chat message.

        Returns:
            The classified intent: "balance_inquiry" or "contract_inquiry".

        Raises:
            BedrockError: On API errors, timeout, or unparseable response.
        """
        try:
            prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(message=message)

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": prompt}],
            })

            response = self._client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=body,
            )

            response_body = json.loads(response["body"].read())
            intent = response_body["content"][0]["text"].strip().lower()

            if intent not in self.VALID_INTENTS:
                raise BedrockError(
                    reason=f"Invalid intent returned: '{intent}'"
                )

            return intent  # type: ignore[return-value]

        except BedrockError:
            raise
        except (ReadTimeoutError, ConnectTimeoutError) as e:
            raise BedrockError(reason=f"Intent classification timed out: {e}")
        except ClientError as e:
            raise BedrockError(
                reason=f"Intent classification API error: {e.response['Error']['Message']}"
            )
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise BedrockError(
                reason=f"Failed to parse classification response: {e}"
            )
        except Exception as e:
            raise BedrockError(reason=f"Unexpected classification error: {e}")
```

### 2. Accounts DynamoDB Client (`accounts_dynamodb_client.py`)

Follows the same pattern as the existing `dynamodb_client.py` but targets the Accounts table.

```python
"""Accounts DynamoDB client module for the AI Banking Assistant."""

import logging
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ConnectionError, EndpointConnectionError

from exceptions import DynamoDBError
from models import AccountRecord

logger = logging.getLogger(__name__)


class AccountsDynamoDBClient:
    """Client for retrieving account records from DynamoDB.

    Attributes:
        table_name: Name of the Accounts DynamoDB table.
    """

    def __init__(self, table_name: str = "Accounts") -> None:
        self.table_name = table_name
        config = Config(
            connect_timeout=5,
            read_timeout=5,
            retries={"max_attempts": 0},
        )
        self._resource = boto3.resource("dynamodb", config=config)
        self._table = self._resource.Table(table_name)

    def get_account(self, account_id: str) -> Optional[AccountRecord]:
        """Retrieve an account from DynamoDB by account_id.

        Args:
            account_id: The partition key to query.

        Returns:
            AccountRecord if found, None if not found.

        Raises:
            DynamoDBError: On connection errors or timeouts.
        """
        if not account_id:
            raise DynamoDBError(
                contract_id=account_id or "",
                reason="A valid account_id is required",
            )

        try:
            response = self._table.get_item(Key={"account_id": account_id})
        except (ClientError, ConnectionError, EndpointConnectionError) as exc:
            raise DynamoDBError(
                contract_id=account_id,
                reason=str(exc),
            ) from exc

        item = response.get("Item")
        if item is None:
            return None

        return AccountRecord(
            account_id=item["account_id"],
            balance=float(item["balance"]),
            currency=item["currency"],
            account_type=item["account_type"],
        )
```

### 3. Account Balance Agent (`account_balance_agent.py`)

Dedicated module implementing the Account Balance Agent logic.

```python
"""Account Balance Agent module for the AI Banking Assistant."""

import re
import logging

from fastapi.responses import JSONResponse

from models import ChatRequest, ChatResponse, AccountRecord
from accounts_dynamodb_client import AccountsDynamoDBClient
from exceptions import DynamoDBError

logger = logging.getLogger(__name__)

ACCOUNT_ID_PATTERN = re.compile(r"\b(ACC-\d{4,})\b", re.IGNORECASE)


class AccountBalanceAgent:
    """Agent for handling account balance inquiries.

    Extracts account_id from user messages, queries the Accounts table,
    and returns formatted balance information.
    """

    def __init__(self) -> None:
        self._db_client = AccountsDynamoDBClient()

    def extract_account_id(self, message: str) -> str | None:
        """Extract account_id from a user message.

        Args:
            message: The user's chat message.

        Returns:
            The extracted account_id or None if not found.
        """
        match = ACCOUNT_ID_PATTERN.search(message)
        return match.group(1) if match else None

    def handle(self, request: ChatRequest) -> ChatResponse | JSONResponse:
        """Handle an account balance inquiry request.

        Args:
            request: The incoming ChatRequest.

        Returns:
            ChatResponse with balance info (AUTO) or error info (ESCALATE).
        """
        account_id = self.extract_account_id(request.message)

        if account_id is None:
            return ChatResponse(
                message="Please provide your account ID (e.g., ACC-1234) to check your balance.",
                contract_summary=None,
                status="AUTO",
            )

        try:
            account = self._db_client.get_account(account_id)
        except DynamoDBError as exc:
            logger.warning(
                "Accounts DynamoDB retrieval failed",
                extra={"contract_id": account_id, "reason": exc.reason},
            )
            return JSONResponse(
                status_code=502,
                content={
                    "message": "Service temporarily unavailable",
                    "contract_summary": None,
                    "status": "ESCALATE",
                },
            )

        if account is None:
            return ChatResponse(
                message=f"Account {account_id} not found, escalating to support.",
                contract_summary=None,
                status="ESCALATE",
            )

        return ChatResponse(
            message=(
                f"Account {account.account_id}: "
                f"Balance: {account.balance} {account.currency}, "
                f"Type: {account.account_type}"
            ),
            contract_summary=None,
            status="AUTO",
        )
```

### 4. Updated Models (`models.py` addition)

```python
class AccountRecord(BaseModel):
    """Domain model representing an account record from DynamoDB.

    Attributes:
        account_id: The unique identifier of the account.
        balance: The current account balance.
        currency: The currency code (e.g., "USD").
        account_type: The type of account (e.g., "savings", "checking").
    """

    account_id: str
    balance: float
    currency: str
    account_type: str
```

### 5. Updated Orchestrator Logic (`main.py` modifications)

The existing `/chat` endpoint is enhanced with orchestration logic:

```python
from intent_classifier import IntentClassifier
from account_balance_agent import AccountBalanceAgent


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse | JSONResponse:
    """POST /chat endpoint with multi-agent orchestration.

    Flow:
    1. If contract_id present → Contract Agent (existing, no classification)
    2. If no contract_id → classify intent via Bedrock
    3. Route to appropriate agent based on intent
    """
    logger.info("Incoming chat request", extra={"contract_id": request.contract_id})

    # Backward compatibility: contract_id present → existing Contract Agent flow
    if request.contract_id:
        return _handle_contract_request(request)

    # No contract_id → classify intent
    classifier = IntentClassifier()
    try:
        intent = classifier.classify(request.message)
    except BedrockError as exc:
        logger.error("Intent classification failed", extra={"reason": exc.reason})
        return ChatResponse(
            message="Unable to classify your request. Please try again or contact support.",
            contract_summary=None,
            status="ESCALATE",
        )

    logger.info("Intent classified", extra={"intent": intent})

    # Route to appropriate agent
    if intent == "balance_inquiry":
        agent = AccountBalanceAgent()
        response = agent.handle(request)
    else:
        # contract_inquiry without contract_id → prompt user
        response = ChatResponse(
            message="Please provide a contract_id to retrieve your contract details.",
            contract_summary=None,
            status="AUTO",
        )

    return response
```

### Interfaces

#### Intent Classifier Interface

| Method | Input | Output | Raises |
|--------|-------|--------|--------|
| `classify(message: str)` | User message string | `IntentType` ("balance_inquiry" \| "contract_inquiry") | `BedrockError` |

### AccountsDynamoDBClient Interface

| Method | Input | Output | Raises |
|--------|-------|--------|--------|
| `get_account(account_id: str)` | Account ID string | `Optional[AccountRecord]` | `DynamoDBError` |

### AccountBalanceAgent Interface

| Method | Input | Output | Raises |
|--------|-------|--------|--------|
| `extract_account_id(message: str)` | User message string | `Optional[str]` | - |
| `handle(request: ChatRequest)` | Full ChatRequest | `ChatResponse \| JSONResponse` | - |

## Data Models

### AccountRecord (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| `account_id` | `str` | Partition key, e.g., "ACC-1001" |
| `balance` | `float` | Current balance |
| `currency` | `str` | Currency code, e.g., "USD" |
| `account_type` | `str` | "savings", "checking", or "investment" |

### Accounts DynamoDB Table Schema

| Attribute | Type | Key |
|-----------|------|-----|
| `account_id` | String | Partition Key |
| `balance` | Number | - |
| `currency` | String | - |
| `account_type` | String | - |

### Test Data (Accounts Table)

| account_id | balance | currency | account_type |
|------------|---------|----------|--------------|
| ACC-1001 | 5250.75 | USD | savings |
| ACC-1002 | 1200.00 | USD | checking |
| ACC-1003 | 48000.00 | USD | investment |

## Error Handling

| Error Scenario | Source | Response |
|---------------|--------|----------|
| Intent classification Bedrock failure | IntentClassifier | ChatResponse(status="ESCALATE") |
| Accounts DynamoDB connection/timeout | AccountsDynamoDBClient | HTTP 502, status="ESCALATE" |
| Account not found | AccountBalanceAgent | ChatResponse(status="ESCALATE") |
| No account_id in message | AccountBalanceAgent | ChatResponse(status="AUTO", prompt message) |
| Unexpected exception | Global handler | HTTP 500, status="ESCALATE" |

All errors follow the existing AUTO/ESCALATE pattern. DynamoDB errors raise `DynamoDBError` consistent with the existing `exceptions.py` pattern. Bedrock errors raise `BedrockError` from the same module.

## File Structure

```
├── main.py                      # Updated with orchestration logic
├── intent_classifier.py         # NEW: Intent classification via Bedrock
├── account_balance_agent.py     # NEW: Account Balance Agent
├── accounts_dynamodb_client.py  # NEW: Accounts table DynamoDB client
├── models.py                    # Updated with AccountRecord
├── dynamodb_client.py           # Existing (unchanged)
├── bedrock_client.py            # Existing (unchanged)
├── exceptions.py                # Existing (unchanged)
```

## Testing Strategy

### Unit Tests
- Test Intent Classifier with mocked Bedrock responses (valid intents, errors)
- Test AccountsDynamoDBClient with mocked boto3 (found, not found, errors)
- Test AccountBalanceAgent.extract_account_id with various message formats
- Test AccountBalanceAgent.handle with mocked DynamoDB client
- Test orchestrator routing logic with mocked classifier and agents

### Property-Based Tests
- Generate random user messages and verify classifier always returns valid intents or raises BedrockError
- Generate random ChatRequests with/without contract_id and verify routing correctness
- Generate random AccountRecords and verify response message contains all required fields
- Generate random DynamoDB errors and verify proper error propagation

### Integration Tests
- End-to-end /chat endpoint with Accounts table containing test data
- Backward compatibility: verify existing contract_id flow produces identical results

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Intent classification returns valid intent

*For any* user message string, the Intent Classifier SHALL return exactly one of the two valid intents: "balance_inquiry" or "contract_inquiry" (or raise a BedrockError).

**Validates: Requirements 1.1**

### Property 2: Routing correctness by intent

*For any* classified intent, the Orchestrator SHALL route the request to the Account_Balance_Agent when intent is "balance_inquiry", and to the Contract_Agent when intent is "contract_inquiry".

**Validates: Requirements 1.2, 1.3**

### Property 3: Contract_id bypasses classification

*For any* ChatRequest with a non-null contract_id, the Orchestrator SHALL never invoke the Intent Classifier and SHALL route the request directly to the Contract Agent.

**Validates: Requirements 1.4, 4.1**

### Property 4: Classification failure produces ESCALATE

*For any* BedrockError raised during intent classification, the Orchestrator SHALL return a ChatResponse with status "ESCALATE".

**Validates: Requirements 1.6**

### Property 5: Account balance response contains required fields

*For any* valid AccountRecord returned from the Accounts table, the Account_Balance_Agent response message SHALL contain the balance value, currency value, and account_type value from that record, with status "AUTO".

**Validates: Requirements 2.3**

### Property 6: Missing account or missing ID produces correct response

*For any* account_id not present in the Accounts table, the response SHALL have status "ESCALATE". *For any* user message without a recognizable account_id pattern, the response SHALL have status "AUTO" and prompt the user.

**Validates: Requirements 2.4, 2.5**

### Property 7: DynamoDB errors propagate as DynamoDBError and produce HTTP 502

*For any* boto3 connection or timeout exception raised during an Accounts table query, the AccountsDynamoDBClient SHALL raise a DynamoDBError, and the Account_Balance_Agent SHALL return HTTP 502 with status "ESCALATE".

**Validates: Requirements 2.6, 6.3**

### Property 8: Full request passthrough to agents

*For any* ChatRequest routed by the Orchestrator, the selected agent SHALL receive the complete, unmodified ChatRequest object.

**Validates: Requirements 5.2**

### Property 9: All responses use valid status values

*For any* request processed by the Orchestrator (regardless of path taken), the resulting response status SHALL be either "AUTO" or "ESCALATE".

**Validates: Requirements 5.5**

### Property 10: Unexpected errors return HTTP 500 ESCALATE

*For any* unhandled exception raised during orchestration, the endpoint SHALL return HTTP 500 with status "ESCALATE" and message "Internal error".

**Validates: Requirements 5.4**
