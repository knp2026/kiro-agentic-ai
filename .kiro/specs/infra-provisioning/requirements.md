# Requirements Document

## Introduction

This document defines the requirements for infrastructure provisioning supporting the Multi-Agent Orchestrator feature of the AI Banking Assistant. It covers IAM policy deployment, Bedrock model access verification, CloudFormation template for reproducible infrastructure, and a Python setup script for local development. The DynamoDB Accounts table already exists in us-east-1 (account 861976376325) with seed data.

## Glossary

- **CloudFormation**: AWS service for provisioning infrastructure as code using YAML/JSON templates.
- **DynamoDB**: AWS NoSQL database service used to store account data.
- **Bedrock**: AWS managed service providing access to foundation models (LLMs).
- **IAM**: AWS Identity and Access Management for controlling permissions.
- **Multi-Agent Orchestrator**: The AI Banking Assistant feature that routes user intents to specialized agents.

## Requirements

### Requirement 1: CloudFormation Stack Deployment

**User Story:** As a developer, I want a CloudFormation template and deployment function that provisions the Accounts DynamoDB table and IAM managed policy as a single stack, so that infrastructure is reproducible and version-controlled.

#### Acceptance Criteria

- 1.1. Given a valid CloudFormation template and AWS credentials, when `deploy_cloudformation_stack()` is called, then the stack reaches `CREATE_COMPLETE` or `UPDATE_COMPLETE` status.
- 1.2. Given the stack already exists with no template changes, when `deploy_cloudformation_stack()` is called, then the function returns `SKIPPED` status without error.
- 1.3. Given the CloudFormation template, then it defines an `AccountsTable` resource of type `AWS::DynamoDB::Table` with partition key `account_id` (String) and `PAY_PER_REQUEST` billing mode.
- 1.4. Given the CloudFormation template, then the stack includes tags `Project: AIBankingAssistant` and `Feature: MultiAgentOrchestrator` on all resources.
- 1.5. Given the stack deploys an IAM managed policy, then the policy is named `MultiAgentOrchestratorPolicy` and uses `CAPABILITY_NAMED_IAM`.

### Requirement 2: IAM Policy Configuration

**User Story:** As a developer, I want an IAM managed policy granting minimal permissions for the Multi-Agent Orchestrator feature, so that the application follows the principle of least privilege.

#### Acceptance Criteria

- 2.1. Given the IAM policy is created, then it contains exactly two statements: `AccountsTableReadAccess` and `BedrockIntentClassification`.
- 2.2. Given the `AccountsTableReadAccess` statement, then it allows only `dynamodb:GetItem` on `arn:aws:dynamodb:us-east-1:861976376325:table/Accounts`.
- 2.3. Given the `BedrockIntentClassification` statement, then it allows only `bedrock:InvokeModel` on `arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0`.
- 2.4. Given the policy already exists, when `create_iam_policy()` is called, then the function returns `SKIPPED` status without creating a duplicate.
- 2.5. Given an optional `attach_to_role` parameter, when a valid role name is provided, then the policy is attached to that IAM role.

### Requirement 3: Bedrock Model Access Verification

**User Story:** As a developer, I want to verify that the required Bedrock foundation model is accessible in the target region, so that I can confirm the application will work before deploying.

#### Acceptance Criteria

- 3.1. Given the model ID `anthropic.claude-haiku-4-5-20251001-v1:0` and region `us-east-1`, when `verify_bedrock_model_access()` is called, then it returns the model's lifecycle status.
- 3.2. Given the model access is granted (status ACTIVE), then the function returns `COMPLETED` status with the model ARN.
- 3.3. Given the model access is not enabled, then the function returns `FAILED` status with a message instructing the user to enable access via the Bedrock console.
- 3.4. The verification function shall not modify any resources (read-only operation).

### Requirement 4: Test Data Seeding

**User Story:** As a developer, I want to seed the Accounts DynamoDB table with predefined test records, so that I can run integration tests and local development without manual data entry.

#### Acceptance Criteria

- 4.1. Given a valid DynamoDB table in ACTIVE state, when `seed_test_data()` is called with the default accounts list, then records for ACC-1001, ACC-1002, and ACC-1003 are written to the table.
- 4.2. Given `overwrite=False` and an account already exists, when `seed_test_data()` is called, then existing records are not overwritten.
- 4.3. Given `overwrite=True`, when `seed_test_data()` is called, then existing records are replaced with the provided data.
- 4.4. Each seeded record shall contain fields: `account_id` (String), `balance` (Number >= 0), `currency` (String), and `account_type` (String, one of: savings, checking, investment).
- 4.5. The seed data shall match: ACC-1001 ($5,250.75 savings), ACC-1002 ($1,200.00 checking), ACC-1003 ($48,000.00 investment).

### Requirement 5: Resource Verification

**User Story:** As a developer, I want a verification function that validates all provisioned infrastructure resources, so that I can confirm the environment is correctly set up.

#### Acceptance Criteria

- 5.1. Given `verify_all_resources()` is called, then it checks: DynamoDB table status, seed data count, Bedrock model access, and IAM policy existence.
- 5.2. Given all resources are properly provisioned, then every verification check returns `COMPLETED` status.
- 5.3. Given one resource check fails, then subsequent checks still execute (independent verification).
- 5.4. The verification function shall return a list of `ProvisioningResult` objects with step name, status, message, and optional resource ARN.
- 5.5. The verification function shall not modify any resources (read-only operation).

### Requirement 6: Python Setup Script

**User Story:** As a developer, I want a CLI-driven Python setup script (`setup_infra.py`) that orchestrates all provisioning steps, so that I can set up the entire infrastructure with a single command.

#### Acceptance Criteria

- 6.1. Given the script is run with `--action deploy`, then it executes the full provisioning workflow: CloudFormation deploy → Bedrock verify → Seed data → Verify all.
- 6.2. Given the script is run with `--action verify`, then it runs only the verification checks without modifying resources.
- 6.3. Given the script is run with `--action seed`, then it only seeds test data to the Accounts table.
- 6.4. The script shall use `argparse` for CLI argument parsing with `--action` (required) and `--region` (optional, default: us-east-1).
- 6.5. The script shall print a summary report showing pass/fail status for each provisioning step.
- 6.6. The provisioning workflow shall be idempotent — running it multiple times produces the same end state without errors.

### Requirement 7: Configuration Management

**User Story:** As a developer, I want a centralized configuration dataclass for all infrastructure parameters, so that values are consistent and easily overridable for different environments.

#### Acceptance Criteria

- 7.1. The `InfraConfig` dataclass shall include: `region`, `account_id`, `table_name`, `stack_name`, `bedrock_model_id`, and `policy_name`.
- 7.2. All fields shall have sensible defaults matching the production values (region: us-east-1, account: 861976376325, table: Accounts).
- 7.3. Configuration values shall be overridable via constructor parameters for testing and multi-environment support.
