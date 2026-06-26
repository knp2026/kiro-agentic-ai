# Infrastructure Setup Tasks: AI Banking Assistant

## Overview

This plan provisions the required AWS resources for the AI Banking Assistant in us-east-1. It creates the DynamoDB Contracts table, inserts test data, and verifies Bedrock model access.

## Tasks

- [x] 1. Create DynamoDB Contracts table
  - [x] 1.1 Create the Contracts table in us-east-1
    - Create DynamoDB table named "Contracts" with partition key `contract_id` (String)
    - Use on-demand (PAY_PER_REQUEST) billing mode
    - Region: us-east-1
    - Wait for table to become ACTIVE

  - [x] 1.2 Insert test data into Contracts table
    - Insert record: contract_id="C123", amount=50000, interest_rate=0.05, duration="5 years"
    - Insert record: contract_id="C456", amount=100000, interest_rate=0.035, duration="10 years"
    - Insert record: contract_id="C789", amount=25000, interest_rate=0.07, duration="3 years"

  - [x] 1.3 Verify table and data
    - Confirm table status is ACTIVE
    - Confirm all 3 test records are retrievable via get-item

- [x] 2. Verify Bedrock model access
  - [x] 2.1 Check Bedrock Claude Haiku 4.5 model availability
    - List foundation models and confirm anthropic.claude-haiku-4-5-20251001-v1:0 is available
    - Verify invoke permissions are granted

- [x] 3. Verify end-to-end connectivity
  - [x] 3.1 Run a DynamoDB connectivity test
    - Query contract_id="C123" from the Contracts table via boto3
    - Confirm the record is returned with correct fields

  - [x] 3.2 Run a Bedrock connectivity test
    - Send a simple prompt to Claude Haiku 4.5 (anthropic.claude-haiku-4-5-20251001-v1:0) via invoke_model
    - Confirm a response is returned without errors

## Notes

- All resources are created in us-east-1
- DynamoDB on-demand billing: you only pay per request (pennies for test usage)
- Bedrock model access must be enabled via the AWS Console if not already done
- These tasks modify your AWS account by creating real resources

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3", "3.1"] },
    { "id": 3, "tasks": ["3.2"] }
  ]
}
```
