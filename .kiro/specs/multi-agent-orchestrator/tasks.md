# Implementation Plan: Multi-Agent Orchestrator

## Overview

Add multi-agent orchestration to the AI Banking Assistant. An LLM-based Intent Classifier routes requests to either the existing Contract Agent or a new Account Balance Agent within the existing `/chat` endpoint. Implementation follows the existing modular patterns using Python, FastAPI, boto3, and pytest with moto/hypothesis.

## Tasks

- [x] 1. Add AccountRecord model and Accounts DynamoDB client
  - [x] 1.1 Add AccountRecord Pydantic model to models.py
    - Add `AccountRecord` class with fields: `account_id` (str), `balance` (float), `currency` (str), `account_type` (str)
    - Follow existing `ContractRecord` pattern with docstring and type annotations
    - _Requirements: 6.4, 3.2_

  - [x] 1.2 Create `accounts_dynamodb_client.py` module
    - Implement `AccountsDynamoDBClient` class with `get_account(account_id: str) -> Optional[AccountRecord]` method
    - Use boto3 DynamoDB resource with 5-second connect and read timeout configuration
    - Raise `DynamoDBError` on connection failures or timeouts consistent with existing error handling pattern
    - Return `None` when account not found, `AccountRecord` when found
    - _Requirements: 3.1, 3.4, 6.2, 6.3_

  - [ ]* 1.3 Write unit tests for AccountsDynamoDBClient
    - Use moto to mock DynamoDB Accounts table
    - Test successful account retrieval, account not found, and connection error scenarios
    - _Requirements: 3.1, 3.2, 3.4_

  - [ ]* 1.4 Write property test for AccountsDynamoDBClient
    - **Property 7: DynamoDB errors propagate as DynamoDBError and produce HTTP 502**
    - Generate random boto3 exceptions and verify they always raise DynamoDBError
    - **Validates: Requirements 2.6, 6.3**

- [x] 2. Implement Intent Classifier
  - [x] 2.1 Create `intent_classifier.py` module
    - Implement `IntentClassifier` class with `classify(message: str) -> IntentType` method
    - Define `IntentType = Literal["balance_inquiry", "contract_inquiry"]`
    - Use Bedrock model `us.anthropic.claude-haiku-4-5-20251001-v1:0` in us-east-1
    - Include classification prompt template that constrains output to valid intents
    - Raise `BedrockError` on API errors, timeouts, or unparseable responses
    - _Requirements: 1.1, 1.5_

  - [ ]* 2.2 Write unit tests for IntentClassifier
    - Mock Bedrock `invoke_model` responses to test valid intent parsing
    - Test timeout handling, API errors, and invalid response parsing
    - _Requirements: 1.1, 1.5, 1.6_

  - [ ]* 2.3 Write property test for intent classification validity
    - **Property 1: Intent classification returns valid intent**
    - Generate random strings as mock Bedrock responses and verify the classifier either returns a valid IntentType or raises BedrockError
    - **Validates: Requirements 1.1**

- [x] 3. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Account Balance Agent
  - [x] 4.1 Create `account_balance_agent.py` module
    - Implement `AccountBalanceAgent` class with `handle(request: ChatRequest) -> ChatResponse | JSONResponse` method
    - Implement `extract_account_id(message: str) -> str | None` using regex pattern `r"\b(ACC-\d{4,})\b"`
    - When account found: return ChatResponse with balance, currency, account_type in message and status "AUTO"
    - When account not found: return ChatResponse with status "ESCALATE"
    - When no account_id extracted: return ChatResponse prompting user with status "AUTO"
    - When DynamoDB error: return JSONResponse with HTTP 502, status "ESCALATE"
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 6.1_

  - [ ]* 4.2 Write unit tests for AccountBalanceAgent
    - Test `extract_account_id` with valid patterns (ACC-1234), missing patterns, and edge cases
    - Test `handle` method with mocked DynamoDB client for all response scenarios
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 4.3 Write property test for account balance response fields
    - **Property 5: Account balance response contains required fields**
    - Generate random AccountRecord instances and verify response message always contains balance, currency, and account_type
    - **Validates: Requirements 2.3**

  - [ ]* 4.4 Write property test for missing account/ID scenarios
    - **Property 6: Missing account or missing ID produces correct response**
    - Generate random messages without account_id pattern and verify status "AUTO" with prompt
    - Generate random non-existent account_ids and verify status "ESCALATE"
    - **Validates: Requirements 2.4, 2.5**

- [x] 5. Integrate Orchestrator into /chat endpoint
  - [x] 5.1 Update `main.py` with orchestration logic
    - Import `IntentClassifier` and `AccountBalanceAgent`
    - When `contract_id` present: bypass classification, use existing Contract Agent flow
    - When no `contract_id`: invoke Intent Classifier, route to appropriate agent
    - On classification failure (BedrockError): return ChatResponse with status "ESCALATE"
    - On `balance_inquiry` intent: delegate to AccountBalanceAgent
    - On `contract_inquiry` intent without contract_id: prompt user for contract_id
    - Log classified intent using structured JSON logging
    - _Requirements: 1.2, 1.3, 1.4, 1.6, 4.1, 5.1, 5.2, 5.3, 5.5_

  - [ ]* 5.2 Write unit tests for orchestrator routing logic
    - Mock IntentClassifier and agents to test routing decisions
    - Verify contract_id requests bypass classification
    - Verify classification failure returns ESCALATE
    - Verify intent-based routing to correct agent
    - _Requirements: 1.2, 1.3, 1.4, 1.6, 4.1_

  - [ ]* 5.3 Write property test for contract_id bypass
    - **Property 3: Contract_id bypasses classification**
    - Generate random ChatRequests with non-null contract_id and verify Intent Classifier is never invoked
    - **Validates: Requirements 1.4, 4.1**

  - [ ]* 5.4 Write property test for routing correctness
    - **Property 2: Routing correctness by intent**
    - Generate random intents and verify the correct agent is selected
    - **Validates: Requirements 1.2, 1.3**

  - [ ]* 5.5 Write property test for classification failure
    - **Property 4: Classification failure produces ESCALATE**
    - Generate random BedrockError instances and verify response always has status "ESCALATE"
    - **Validates: Requirements 1.6**

  - [ ]* 5.6 Write property test for valid status values
    - **Property 9: All responses use valid status values**
    - Generate random ChatRequests (with/without contract_id) and verify response status is always "AUTO" or "ESCALATE"
    - **Validates: Requirements 5.5**

- [x] 6. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Backward compatibility and integration testing
  - [x] 7.1 Write integration tests for end-to-end /chat flows
    - Use moto for DynamoDB and mock for Bedrock
    - Test contract_id flow produces identical responses to current behavior
    - Test balance inquiry flow end-to-end with test data (ACC-1001, ACC-1002, ACC-1003)
    - Verify ChatRequest/ChatResponse schema unchanged
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 3.3_

  - [ ]* 7.2 Write property test for full request passthrough
    - **Property 8: Full request passthrough to agents**
    - Generate random ChatRequests and verify the agent receives the complete unmodified request object
    - **Validates: Requirements 5.2**

  - [ ]* 7.3 Write property test for unexpected error handling
    - **Property 10: Unexpected errors return HTTP 500 ESCALATE**
    - Generate random unhandled exceptions and verify endpoint returns HTTP 500 with status "ESCALATE" and message "Internal error"
    - **Validates: Requirements 5.4**

- [x] 8. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Uses existing patterns: DynamoDBError/BedrockError exceptions, structured JSON logging, AUTO/ESCALATE status
- The `ACCOUNT_ID_PATTERN` regex (`ACC-\d{4,}`) should be documented for users
- Integration tests use moto for DynamoDB mocking and test data from Requirements 3.3

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["1.2", "2.2", "2.3"] },
    { "id": 2, "tasks": ["1.3", "1.4", "4.1"] },
    { "id": 3, "tasks": ["4.2", "4.3", "4.4"] },
    { "id": 4, "tasks": ["5.1"] },
    { "id": 5, "tasks": ["5.2", "5.3", "5.4", "5.5", "5.6"] },
    { "id": 6, "tasks": ["7.1", "7.2", "7.3"] }
  ]
}
```
