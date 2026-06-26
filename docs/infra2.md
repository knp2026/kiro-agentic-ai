# Infrastructure Setup: Multi-Agent Orchestrator

This document captures all the AWS resources and configuration needed to support the multi-agent orchestrator feature.

---

## 1. DynamoDB Accounts Table

### AWS CLI

```bash
aws dynamodb create-table \
  --table-name Accounts \
  --key-schema AttributeName=account_id,KeyType=HASH \
  --attribute-definitions AttributeName=account_id,AttributeType=S \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### Seed Test Data

```bash
aws dynamodb put-item \
  --table-name Accounts \
  --region us-east-1 \
  --item '{
    "account_id": {"S": "ACC-1001"},
    "balance": {"N": "5250.75"},
    "currency": {"S": "USD"},
    "account_type": {"S": "savings"}
  }'

aws dynamodb put-item \
  --table-name Accounts \
  --region us-east-1 \
  --item '{
    "account_id": {"S": "ACC-1002"},
    "balance": {"N": "1200.00"},
    "currency": {"S": "USD"},
    "account_type": {"S": "checking"}
  }'

aws dynamodb put-item \
  --table-name Accounts \
  --region us-east-1 \
  --item '{
    "account_id": {"S": "ACC-1003"},
    "balance": {"N": "48000.00"},
    "currency": {"S": "USD"},
    "account_type": {"S": "investment"}
  }'
```

### CloudFormation

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: DynamoDB Accounts table for the Multi-Agent Orchestrator

Resources:
  AccountsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: Accounts
      BillingMode: PAY_PER_REQUEST
      KeySchema:
        - AttributeName: account_id
          KeyType: HASH
      AttributeDefinitions:
        - AttributeName: account_id
          AttributeType: S
      Tags:
        - Key: Project
          Value: AIBankingAssistant
        - Key: Feature
          Value: MultiAgentOrchestrator
```

---

## 2. Amazon Bedrock Model Access

The Intent Classifier uses the following Bedrock model:

- **Model ID:** `anthropic.claude-haiku-4-5-20251001-v1:0`
- **Region:** `us-east-1`

### Enable Model Access

1. Navigate to the [Amazon Bedrock console](https://console.aws.amazon.com/bedrock/) in us-east-1
2. Go to **Model catalog** in the left navigation
3. Search for **Claude Haiku** (Anthropic)
4. Click on the model and select **Request access** or **Enable**
5. Accept the EULA/terms and submit the request
6. Wait for status to show "Access granted"

### AWS CLI (check access status)

```bash
aws bedrock get-foundation-model \
  --model-identifier anthropic.claude-haiku-4-5-20251001-v1:0 \
  --region us-east-1
```

---

## 3. IAM Permissions

The application's execution role needs the following permissions added for the new resources:

### DynamoDB Accounts Table Access

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AccountsTableReadAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/Accounts"
    }
  ]
}
```

### Bedrock Intent Classification Access

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockIntentClassification",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0"
    }
  ]
}
```

### Combined IAM Policy (CloudFormation)

```yaml
  OrchestratorPolicy:
    Type: AWS::IAM::ManagedPolicy
    Properties:
      ManagedPolicyName: MultiAgentOrchestratorPolicy
      Description: Permissions for the Multi-Agent Orchestrator feature
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Sid: AccountsTableReadAccess
            Effect: Allow
            Action:
              - dynamodb:GetItem
            Resource: !GetAtt AccountsTable.Arn
          - Sid: BedrockIntentClassification
            Effect: Allow
            Action:
              - bedrock:InvokeModel
            Resource: 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0'
```

---

## 4. Table Schema Reference

### Accounts Table

| Attribute    | Type   | Key           | Description                              |
|-------------|--------|---------------|------------------------------------------|
| account_id  | String | Partition Key | Unique account identifier (e.g. ACC-1001)|
| balance     | Number | —             | Current account balance                  |
| currency    | String | —             | Currency code (e.g. USD)                 |
| account_type| String | —             | Account type (savings/checking/investment)|

---

## 5. Python Setup Script

For local development and testing with real AWS resources:

```python
"""Setup script to create and seed the Accounts DynamoDB table."""

import boto3
from decimal import Decimal

def create_accounts_table(region: str = "us-east-1"):
    """Create the Accounts DynamoDB table if it doesn't exist."""
    dynamodb = boto3.resource("dynamodb", region_name=region)

    table = dynamodb.create_table(
        TableName="Accounts",
        KeySchema=[
            {"AttributeName": "account_id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "account_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    print(f"Table 'Accounts' created successfully in {region}")
    return table


def seed_test_data(region: str = "us-east-1"):
    """Seed the Accounts table with test data."""
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table("Accounts")

    test_accounts = [
        {
            "account_id": "ACC-1001",
            "balance": Decimal("5250.75"),
            "currency": "USD",
            "account_type": "savings",
        },
        {
            "account_id": "ACC-1002",
            "balance": Decimal("1200.00"),
            "currency": "USD",
            "account_type": "checking",
        },
        {
            "account_id": "ACC-1003",
            "balance": Decimal("48000.00"),
            "currency": "USD",
            "account_type": "investment",
        },
    ]

    with table.batch_writer() as batch:
        for account in test_accounts:
            batch.put_item(Item=account)

    print(f"Seeded {len(test_accounts)} accounts into 'Accounts' table")


if __name__ == "__main__":
    create_accounts_table()
    seed_test_data()
```

---

## 6. Verification Checklist

After provisioning, verify the setup:

```bash
# Verify table exists and is ACTIVE
aws dynamodb describe-table --table-name Accounts --region us-east-1 \
  --query "Table.TableStatus"

# Verify test data was seeded
aws dynamodb scan --table-name Accounts --region us-east-1 \
  --query "Count"

# Verify Bedrock model access
aws bedrock get-foundation-model \
  --model-identifier anthropic.claude-haiku-4-5-20251001-v1:0 \
  --region us-east-1 \
  --query "modelDetails.modelLifecycle.status"

# Test a balance inquiry end-to-end
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the balance for ACC-1001?"}'
```
