# Implementation Plan: AI Banking Assistant

## Overview

This plan implements a chat-based API service using Python and FastAPI that retrieves contract data from AWS DynamoDB and generates summaries via Amazon Bedrock LLM. The implementation follows a modular architecture with separate modules for routing, data access, and LLM invocation, with comprehensive error handling and logging.

## Tasks

- [x] 1. Set up project structure, dependencies, and core models
  - [x] 1.1 Create project structure and install dependencies
    - Create the project directory with `main.py`, `dynamodb_client.py`, `bedrock_client.py`, `models.py`, `exceptions.py`
    - Create `requirements.txt` with: `fastapi`, `uvicorn`, `boto3`, `pydantic`
    - Create `requirements-dev.txt` with: `pytest`, `hypothesis`, `httpx`, `moto`
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 1.2 Implement Pydantic models and custom exceptions
    - In `models.py`, define `ChatRequest` with `message` (str, max_length=1000, required) and `contract_id` (Optional[str])
    - Define `ContractRecord` with `contract_id` (str), `amount` (float), `interest_rate` (float), `duration` (str)
    - Define `ChatResponse` with `message` (str), `contract_summary` (Optional[str]), `status` (str)
    - In `exceptions.py`, define `DynamoDBError(Exception)` with `contract_id` and `reason` attributes
    - Define `BedrockError(Exception)` with `reason` attribute
    - _Requirements: 1.1, 2.2, 5.1_

- [x] 2. Implement DynamoDB client module
  - [x] 2.1 Implement DynamoDBClient class
    - In `dynamodb_client.py`, create `DynamoDBClient` class with `__init__` accepting `table_name` (default "Contracts")
    - Initialize boto3 DynamoDB resource with 5-second timeout configuration
    - Implement `get_contract(contract_id: str) -> Optional[ContractRecord]`
    - If `contract_id` is empty or None, raise `DynamoDBError` with message indicating valid contract_id required
    - Query DynamoDB using `contract_id` as partition key
    - Return `ContractRecord` if found, `None` if not found
    - Catch boto3 `ClientError` and connection errors, raise `DynamoDBError` with contract_id and failure reason
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 2.2 Write property test for DynamoDB response mapping (Property 3)
    - **Property 3: DynamoDB response mapping preserves contract data**
    - Use Hypothesis to generate random contract fields (strings, floats)
    - Mock DynamoDB response and verify ContractRecord fields match exactly
    - **Validates: Requirements 2.2**

  - [ ]* 2.3 Write property test for DynamoDB error information (Property 4)
    - **Property 4: DynamoDB errors contain contract_id and failure reason**
    - Use Hypothesis to generate random contract_ids and error messages
    - Mock DynamoDB to raise errors and verify DynamoDBError contains both contract_id and reason
    - **Validates: Requirements 2.4**

- [x] 3. Implement Bedrock client module
  - [x] 3.1 Implement BedrockClient class
    - In `bedrock_client.py`, create `BedrockClient` class with `__init__` accepting `model_id` (default "anthropic.claude-3-haiku-20240307-v1:0") and `timeout` (default 30)
    - Initialize boto3 Bedrock runtime client with timeout configuration
    - Implement `generate_summary(contract_record: ContractRecord) -> str`
    - Construct prompt: "Summarize the following contract details in 3 bullet points:" followed by all contract fields
    - Invoke Bedrock model and extract generated text
    - Truncate response to maximum 1024 characters
    - Catch boto3 errors and timeouts, raise `BedrockError` with failure reason
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 3.2 Write property test for prompt construction (Property 5)
    - **Property 5: Bedrock prompt construction includes all contract fields**
    - Use Hypothesis to generate random ContractRecords
    - Verify prompt contains "Summarize the following contract details in 3 bullet points:" and all field values
    - **Validates: Requirements 4.1**

  - [ ]* 3.3 Write property test for Bedrock error propagation (Property 6)
    - **Property 6: Bedrock errors propagate with failure reason**
    - Use Hypothesis to generate random error messages
    - Mock Bedrock to raise errors and verify BedrockError contains failure reason
    - **Validates: Requirements 4.3**

  - [ ]* 3.4 Write property test for summary truncation (Property 7)
    - **Property 7: Summary truncation to maximum 1024 characters**
    - Use Hypothesis to generate random strings of length 0–5000
    - Mock Bedrock response and verify returned summary is at most 1024 characters
    - Verify content up to truncation point matches original
    - **Validates: Requirements 4.5**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement FastAPI chat endpoint with orchestration logic
  - [x] 5.1 Implement POST /chat endpoint and request orchestration
    - In `main.py`, create FastAPI app instance
    - Implement `POST /chat` endpoint accepting `ChatRequest`
    - If no `contract_id`: return `ChatResponse` with prompt message, null summary, status "AUTO"
    - If `contract_id` present: call `DynamoDBClient.get_contract()`
    - If contract not found: return message "Contract not found, escalating to support", null summary, status "ESCALATE"
    - If contract found: call `BedrockClient.generate_summary()`
    - On success: return message containing contract_id, summary in `contract_summary`, status "AUTO"
    - On `DynamoDBError`: return HTTP 502, message "Service temporarily unavailable", null summary, status "ESCALATE"
    - On `BedrockError`: return message "Summary generation failed", null summary, status "ESCALATE"
    - Add global exception handler for unexpected errors returning HTTP 500, status "ESCALATE"
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4, 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 5.2 Implement structured logging throughout the request flow
    - Configure Python logging with JSON-structured output
    - Log incoming requests at INFO level (message content and contract_id)
    - Log DynamoDB success at INFO level (contract_id + success indicator)
    - Log DynamoDB failure at WARNING level (contract_id + reason)
    - Log Bedrock success at INFO level
    - Log Bedrock failure at ERROR level (failure reason)
    - Log response status at INFO level (AUTO or ESCALATE)
    - Log unexpected errors at ERROR level (type, message, stack trace)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [ ]* 5.3 Write property test for invalid request rejection (Property 1)
    - **Property 1: Invalid requests are rejected with 422**
    - Use Hypothesis to generate payloads with missing message or oversized strings
    - Use FastAPI TestClient to verify HTTP 422 responses
    - **Validates: Requirements 1.4, 1.5**

  - [ ]* 5.4 Write property test for valid request success (Property 2)
    - **Property 2: Valid contract_id requests return HTTP 200**
    - Use Hypothesis to generate valid messages (≤1000 chars) and contract_ids
    - Mock DynamoDB and Bedrock for success, verify HTTP 200 with valid ChatResponse
    - **Validates: Requirements 1.3**

  - [ ]* 5.5 Write property test for response structure invariant (Property 8)
    - **Property 8: Response structure invariant**
    - Use Hypothesis to generate all request variants (valid, invalid contract_id, missing contract_id)
    - Verify all 200 responses contain exactly message, contract_summary, and status fields
    - Verify status is always "AUTO" or "ESCALATE"
    - **Validates: Requirements 5.1**

  - [ ]* 5.6 Write property test for summary passthrough (Property 9)
    - **Property 9: Summary passthrough from Bedrock to response**
    - Use Hypothesis to generate random summary strings
    - Mock Bedrock to return generated summaries, verify ChatResponse contains exact summary
    - **Validates: Requirements 4.2, 5.3**

  - [ ]* 5.7 Write property test for success message containing contract_id (Property 10)
    - **Property 10: Success message contains contract_id**
    - Use Hypothesis to generate random contract_ids
    - Mock success flow, verify response message field contains the contract_id
    - **Validates: Requirements 5.4**

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis (Python PBT library)
- Unit tests validate specific examples and edge cases
- All AWS service interactions use boto3 with moto for testing
- The modular architecture enables independent testing of each component

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["2.1", "3.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "3.2", "3.3", "3.4"] },
    { "id": 4, "tasks": ["5.1"] },
    { "id": 5, "tasks": ["5.2", "5.3", "5.4", "5.5", "5.6", "5.7"] }
  ]
}
```
