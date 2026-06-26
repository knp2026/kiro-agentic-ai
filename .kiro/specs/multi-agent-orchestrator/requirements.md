# Requirements Document

## Introduction

This feature adds multi-agent orchestration to the existing AI Banking Assistant. An LLM-based Orchestrator classifies user intent from the message field and routes requests to either the existing Contract Agent (contract lookups/summaries) or a new Account Balance Agent (account balance retrieval). The orchestration runs inside the existing `/chat` endpoint, maintaining backward compatibility with the current contract_id-based flow. A new DynamoDB "Accounts" table stores account data, and the Account Balance Agent follows the same AUTO/ESCALATE human-in-the-loop pattern as the existing Contract Agent.

## Glossary

- **Orchestrator**: The LLM-based component that classifies user intent and routes requests to the appropriate agent within the `/chat` endpoint.
- **Account_Balance_Agent**: The agent responsible for retrieving account balance information from the Accounts DynamoDB table.
- **Contract_Agent**: The existing agent responsible for retrieving and summarizing contract information from the Contracts DynamoDB table.
- **Intent_Classifier**: The Bedrock LLM invocation that analyzes the user message and determines which agent should handle the request.
- **Accounts_Table**: The DynamoDB table storing account records with fields: account_id, balance, currency, and account_type.
- **Chat_Endpoint**: The existing POST /chat FastAPI endpoint that serves as the single entry point for all user requests.
- **ChatRequest**: The Pydantic request model containing message (required) and contract_id (optional) fields.
- **ChatResponse**: The Pydantic response model containing message, contract_summary (optional), and status fields.

## Requirements

### Requirement 1: Intent Classification

**User Story:** As a banking customer, I want the system to understand my intent from my message, so that my request is handled by the appropriate agent without requiring me to specify which service I need.

#### Acceptance Criteria

1. WHEN a ChatRequest is received with a message and no contract_id, THE Intent_Classifier SHALL invoke the Bedrock LLM to classify the user message into one of the following intents: "balance_inquiry" or "contract_inquiry".
2. WHEN the Intent_Classifier classifies the intent as "balance_inquiry", THE Orchestrator SHALL route the request to the Account_Balance_Agent.
3. WHEN the Intent_Classifier classifies the intent as "contract_inquiry", THE Orchestrator SHALL route the request to the Contract_Agent.
4. WHEN a ChatRequest is received with a contract_id field populated, THE Orchestrator SHALL bypass intent classification and route the request directly to the Contract_Agent.
5. THE Intent_Classifier SHALL use the Bedrock model "us.anthropic.claude-haiku-4-5-20251001-v1:0" in the us-east-1 region for intent classification.
6. IF the Intent_Classifier fails to classify the intent due to a Bedrock error, THEN THE Orchestrator SHALL return a ChatResponse with status "ESCALATE" and a message indicating classification failure.

### Requirement 2: Account Balance Agent

**User Story:** As a banking customer, I want to check my account balance by providing my account ID in a chat message, so that I can quickly see my financial standing.

#### Acceptance Criteria

1. WHEN the Account_Balance_Agent receives a request, THE Account_Balance_Agent SHALL extract the account_id from the user message.
2. WHEN a valid account_id is extracted, THE Account_Balance_Agent SHALL query the Accounts_Table using the account_id as the partition key.
3. WHEN the Accounts_Table returns an account record, THE Account_Balance_Agent SHALL return a ChatResponse with the account balance, currency, and account_type in the message field and status "AUTO".
4. WHEN the Accounts_Table does not contain a record for the provided account_id, THE Account_Balance_Agent SHALL return a ChatResponse with a message indicating the account was not found and status "ESCALATE".
5. IF the Account_Balance_Agent cannot extract an account_id from the user message, THEN THE Account_Balance_Agent SHALL return a ChatResponse with a message prompting the user to provide an account_id and status "AUTO".
6. IF the Accounts_Table query fails due to a connection or timeout error, THEN THE Account_Balance_Agent SHALL return a JSON response with HTTP status 502, a message "Service temporarily unavailable", and status "ESCALATE".

### Requirement 3: Accounts DynamoDB Table

**User Story:** As a system administrator, I want account data stored in a dedicated DynamoDB table, so that account balance queries can be served reliably and independently from contract data.

#### Acceptance Criteria

1. THE Accounts_Table SHALL use "account_id" as the partition key with type String.
2. THE Accounts_Table SHALL store the following attributes for each record: account_id (String), balance (Number), currency (String), and account_type (String).
3. THE Accounts_Table SHALL contain test data with at least three account records covering different account_type values (e.g., "savings", "checking", "investment").
4. THE Accounts_Table SHALL be accessed using boto3 DynamoDB resource with a 5-second connect and read timeout configuration.

### Requirement 4: Backward Compatibility

**User Story:** As an existing user of the banking assistant, I want my current contract lookup workflow to continue working unchanged, so that the new orchestration does not disrupt my experience.

#### Acceptance Criteria

1. WHEN a ChatRequest is received with a contract_id field populated, THE Chat_Endpoint SHALL process the request using the existing Contract_Agent logic without invoking the Intent_Classifier.
2. THE Chat_Endpoint SHALL continue to accept the existing ChatRequest schema with message (required, max 1000 characters) and contract_id (optional) fields.
3. THE Chat_Endpoint SHALL continue to return responses conforming to the existing ChatResponse schema with message, contract_summary, and status fields.
4. WHEN the Contract_Agent processes a request, THE Contract_Agent SHALL produce responses identical in structure and behavior to the current implementation.

### Requirement 5: Orchestrator Integration

**User Story:** As a developer, I want the orchestrator to run within the existing /chat endpoint, so that no new API endpoints are required and the system remains simple to operate.

#### Acceptance Criteria

1. THE Orchestrator SHALL operate within the existing POST /chat endpoint without introducing additional API endpoints.
2. WHEN the Orchestrator routes a request to an agent, THE Orchestrator SHALL pass the full ChatRequest to the selected agent.
3. THE Orchestrator SHALL log the classified intent for each request using structured JSON logging consistent with the existing logging format.
4. IF an unexpected error occurs during orchestration, THEN THE Chat_Endpoint SHALL return HTTP 500 with status "ESCALATE" and message "Internal error".
5. THE Orchestrator SHALL maintain the same AUTO/ESCALATE status pattern used by the existing Contract_Agent for all agent responses.

### Requirement 6: Account Balance Agent Module Structure

**User Story:** As a developer, I want the Account Balance Agent to follow the same modular patterns as the existing codebase, so that the project remains consistent and maintainable.

#### Acceptance Criteria

1. THE Account_Balance_Agent SHALL be implemented in a dedicated module file separate from endpoint routing logic.
2. THE Account_Balance_Agent SHALL use a DynamoDB client class that encapsulates all Accounts_Table access logic with no endpoint routing or LLM invocation logic.
3. THE Account_Balance_Agent SHALL raise a DynamoDBError exception on Accounts_Table connection failures or timeouts, consistent with the existing error handling pattern.
4. THE Account_Balance_Agent SHALL define an AccountRecord Pydantic model with fields: account_id (str), balance (float), currency (str), and account_type (str).
