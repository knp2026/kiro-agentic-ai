# Requirements Document

## Introduction

This document defines the requirements for an AI-powered banking assistant. The assistant provides a chat-based API built with Python (FastAPI) that retrieves contract data from AWS DynamoDB, generates summaries using Amazon Bedrock LLM, and handles escalation when contracts are not found. The system is designed with clean modular architecture and comprehensive logging.

## Glossary

- **Chat_API**: The FastAPI-based HTTP interface that accepts user messages and returns AI-generated responses
- **Contracts_Table**: The AWS DynamoDB table named "Contracts" storing contract records with fields contract_id, amount, interest_rate, and duration
- **Contract_Record**: A single item in the Contracts_Table identified by contract_id containing amount, interest_rate, and duration fields
- **DynamoDB_Client**: The boto3-based module responsible for retrieving contract data from the Contracts_Table
- **Bedrock_Client**: The module responsible for invoking Amazon Bedrock LLM to generate contract summaries
- **Chat_Response**: The structured JSON response returned by the Chat_API containing message, contract_summary, and status fields
- **AUTO_Status**: The response status indicating the assistant successfully processed the request without human intervention
- **ESCALATE_Status**: The response status indicating the request requires human support intervention

## Requirements

### Requirement 1: Chat Endpoint

**User Story:** As a banking customer, I want to send a message to the chat endpoint, so that I can get information about my contract.

#### Acceptance Criteria

1. THE Chat_API SHALL expose a POST /chat endpoint that accepts a JSON body containing a required message field (string, maximum 1000 characters) and an optional contract_id field (string)
2. WHEN a request is received without a contract_id, THE Chat_API SHALL return a Chat_Response with the message field set to a prompt asking the user to provide a contract_id, the contract_summary field set to null, and the status field set to AUTO_Status
3. WHEN a request is received with a non-empty contract_id, THE Chat_API SHALL process the request and return a Chat_Response with HTTP 200 status
4. IF the request body is malformed or missing the message field, THEN THE Chat_API SHALL return an HTTP 422 response with a JSON body containing a validation error indicating which field failed validation
5. IF the message field exceeds 1000 characters, THEN THE Chat_API SHALL return an HTTP 422 response with a validation error indicating the maximum length was exceeded

### Requirement 2: DynamoDB Contract Retrieval

**User Story:** As a banking customer, I want the assistant to retrieve my contract details, so that I can receive accurate information about my contract.

#### Acceptance Criteria

1. WHEN a contract_id is provided, THE DynamoDB_Client SHALL query the Contracts_Table using the contract_id as the primary key within 5 seconds
2. WHEN a matching Contract_Record exists, THE DynamoDB_Client SHALL return the contract_id, amount, interest_rate, and duration fields as received from the Contracts_Table
3. WHEN no matching Contract_Record exists, THE DynamoDB_Client SHALL return a None value to the caller indicating that the contract was not found
4. IF a DynamoDB connection error or timeout occurs, THEN THE DynamoDB_Client SHALL raise an error containing the failure reason and the contract_id that was queried
5. IF the provided contract_id is empty or None, THEN THE DynamoDB_Client SHALL raise an error indicating that a valid contract_id is required

### Requirement 3: Contract Not Found Escalation

**User Story:** As a banking customer, I want to be informed when my contract cannot be found, so that I know my request is being escalated to support.

#### Acceptance Criteria

1. WHEN the DynamoDB_Client indicates a contract was not found, THE Chat_API SHALL return an HTTP 200 response containing a Chat_Response with the message "Contract not found, escalating to support"
2. WHEN the DynamoDB_Client indicates a contract was not found, THE Chat_API SHALL set the status field to ESCALATE_Status
3. WHEN the DynamoDB_Client indicates a contract was not found, THE Chat_API SHALL set the contract_summary field to null
4. IF the DynamoDB_Client raises a connection error during contract retrieval, THEN THE Chat_API SHALL return an HTTP 502 response containing a Chat_Response with the status field set to ESCALATE_Status, the contract_summary field set to null, and a message indicating that the service is temporarily unavailable

### Requirement 4: Bedrock LLM Contract Summary

**User Story:** As a banking customer, I want to receive a clear summary of my contract, so that I can quickly understand the key details.

#### Acceptance Criteria

1. WHEN a Contract_Record is successfully retrieved, THE Bedrock_Client SHALL send a prompt to Amazon Bedrock containing the text "Summarize the following contract details in 3 bullet points:" followed by the contract_id, amount, interest_rate, and duration fields from the Contract_Record
2. WHEN Amazon Bedrock returns a response within 30 seconds, THE Bedrock_Client SHALL extract the generated summary text from the response
3. IF Amazon Bedrock returns an error or does not respond within 30 seconds, THEN THE Bedrock_Client SHALL raise a descriptive error containing the failure reason
4. THE Bedrock_Client SHALL use either the Claude or Titan model available through Amazon Bedrock
5. WHEN the Bedrock_Client extracts a generated summary, THE Bedrock_Client SHALL return the summary text truncated to a maximum of 1024 characters

### Requirement 5: Structured Response Format

**User Story:** As a frontend developer, I want the API to return a consistent structured response, so that I can reliably parse and display the results.

#### Acceptance Criteria

1. THE Chat_API SHALL return a JSON response containing exactly three fields: message (string), contract_summary (string or null), and status (string)
2. WHEN a contract is successfully summarized, THE Chat_API SHALL set the status field to AUTO_Status
3. WHEN a contract is successfully summarized, THE Chat_API SHALL populate the contract_summary field with the Bedrock-generated summary
4. WHEN a contract is successfully summarized, THE Chat_API SHALL set the message field to a string that contains the contract_id and indicates the contract was found and summarized
5. IF the Bedrock_Client raises an error after a Contract_Record is retrieved, THEN THE Chat_API SHALL return a Chat_Response with the status field set to ESCALATE_Status, the contract_summary field set to null, and the message field indicating that summary generation failed

### Requirement 6: Modular Code Structure

**User Story:** As a developer, I want the code to be organized into separate modules, so that the codebase is maintainable and testable.

#### Acceptance Criteria

1. THE Chat_API SHALL implement all DynamoDB access logic in a dedicated DynamoDB_Client module file that contains no endpoint routing or LLM invocation logic
2. THE Chat_API SHALL implement all Bedrock LLM invocation logic in a dedicated Bedrock_Client module file that exposes a callable function for generating summaries and contains no endpoint routing or data access logic
3. THE Chat_API SHALL implement endpoint routing and request handling in a module that does not directly contain DynamoDB query logic or Bedrock invocation logic, delegating those responsibilities to the DynamoDB_Client and Bedrock_Client modules
4. THE Chat_API SHALL structure modules such that the DynamoDB_Client and Bedrock_Client modules can each be imported and tested independently without requiring the endpoint routing module

### Requirement 7: Request and Response Logging

**User Story:** As a DevOps engineer, I want comprehensive logging of the request flow, so that I can monitor and troubleshoot the system.

#### Acceptance Criteria

1. WHEN a request is received, THE Chat_API SHALL log the incoming request at INFO level including the user message content and contract_id if present
2. WHEN the DynamoDB_Client successfully retrieves a contract, THE Chat_API SHALL log at INFO level the contract_id and a success indicator
3. IF the DynamoDB_Client fails to retrieve a contract, THEN THE Chat_API SHALL log at WARNING level the contract_id and the reason for failure
4. WHEN the Bedrock_Client successfully generates a summary, THE Chat_API SHALL log at INFO level a success indicator for the generation
5. IF the Bedrock_Client fails to generate a summary, THEN THE Chat_API SHALL log at ERROR level the failure reason
6. WHEN a response is sent, THE Chat_API SHALL log at INFO level the response status field value (AUTO_Status or ESCALATE_Status)
7. IF an unexpected error occurs during processing, THEN THE Chat_API SHALL log at ERROR level the error type, error message, and stack trace
