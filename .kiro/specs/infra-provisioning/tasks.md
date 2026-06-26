# Implementation Plan: Infrastructure Provisioning

## Overview

This plan covers the implementation of infrastructure provisioning for the Multi-Agent Orchestrator feature. Tasks include creating the CloudFormation template, implementing the Python setup script with all provisioning functions, and validating the infrastructure end-to-end.

## Tasks

- [x] 1. Create CloudFormation Template
  - [x] 1.1 Create `infra/` directory and `infra/cloudformation.yaml` file
  - [x] 1.2 Define `AccountsTable` resource with partition key `account_id` (String), PAY_PER_REQUEST billing, and project tags
  - [x] 1.3 Define `OrchestratorPolicy` IAM managed policy with `AccountsTableReadAccess` (dynamodb:GetItem) and `BedrockIntentClassification` (bedrock:InvokeModel) statements
  - [x] 1.4 Add stack outputs for table ARN, table name, and policy ARN
  - [x] 1.5 Validate template syntax with `aws cloudformation validate-template`
- [x] 2. Create Configuration Module
  - [x] 2.1 Create `setup_infra.py` file with module docstring
  - [x] 2.2 Implement `ProvisioningStatus` enum (PENDING, IN_PROGRESS, COMPLETED, FAILED, SKIPPED)
  - [x] 2.3 Implement `ProvisioningResult` dataclass with fields: step_name, status, message, resource_arn (optional)
  - [x] 2.4 Implement `InfraConfig` dataclass with defaults: region=us-east-1, account_id=861976376325, table_name=Accounts, stack_name=MultiAgentOrchestratorInfra, bedrock_model_id, policy_name
  - [x] 2.5 Implement `AccountSeedData` dataclass with fields: account_id, balance, currency, account_type
- [x] 3. Implement CloudFormation Deployment Function
  - [x] 3.1 Implement stack existence check using `describe_stacks`
  - [x] 3.2 Implement `create_stack` path with CAPABILITY_NAMED_IAM and project tags
  - [x] 3.3 Implement `update_stack` path with "No updates" handling (return SKIPPED)
  - [x] 3.4 Add waiter logic for `stack_create_complete` and `stack_update_complete`
  - [x] 3.5 Return `ProvisioningResult` with stack ARN on success
- [x] 4. Implement IAM Policy Function
  - [x] 4.1 Build policy document JSON with two statements: AccountsTableReadAccess and BedrockIntentClassification
  - [x] 4.2 Implement policy existence check (handle EntityAlreadyExists, return SKIPPED)
  - [x] 4.3 Implement `create_policy` call with correct policy document
  - [x] 4.4 Implement optional `attach_to_role` parameter using `attach_role_policy`
  - [x] 4.5 Return `ProvisioningResult` with policy ARN
- [x] 5. Implement Bedrock Model Access Verification
  - [x] 5.1 Create Bedrock client (not bedrock-runtime) for `get_foundation_model` call
  - [x] 5.2 Call `get_foundation_model` with model ID `anthropic.claude-haiku-4-5-20251001-v1:0`
  - [x] 5.3 Parse response for `modelDetails.modelLifecycle.status`
  - [x] 5.4 Return COMPLETED with model ARN if ACTIVE, FAILED with instructions if not
  - [x] 5.5 Handle exceptions (invalid model ID, permission errors) with descriptive messages
- [x] 6. Implement Test Data Seeding Function
  - [x] 6.1 Implement conditional write logic: check existence with `get_item` when `overwrite=False`
  - [x] 6.2 Implement `put_item` for each account using `batch_writer` for efficiency
  - [x] 6.3 Define default test accounts list (ACC-1001: $5250.75 savings, ACC-1002: $1200.00 checking, ACC-1003: $48000.00 investment)
  - [x] 6.4 Convert float balances to `Decimal` for DynamoDB compatibility
  - [x] 6.5 Return `ProvisioningResult` with count of items written
- [x] 7. Implement Resource Verification Function
  - [x] 7.1 Implement DynamoDB table status check using `describe_table`
  - [x] 7.2 Implement seed data count check using `scan` with `Select=COUNT`
  - [x] 7.3 Implement Bedrock model access check using `get_foundation_model`
  - [x] 7.4 Implement IAM policy existence check using `get_policy` with constructed ARN
  - [x] 7.5 Ensure each check is wrapped in try/except so failures are independent
  - [x] 7.6 Return list of `ProvisioningResult` (one per check)
- [x] 8. Implement CLI Entrypoint and Orchestrator
  - [x] 8.1 Implement `run_provisioning()` orchestrator: CFN deploy → Bedrock verify → Seed data → Verify all
  - [x] 8.2 Add `argparse` with `--action` (choices: deploy, verify, seed) and `--region` (default: us-east-1)
  - [x] 8.3 Implement `__main__` block routing to appropriate function based on action
  - [x] 8.4 Implement summary report printer showing pass/fail per step with colored output
  - [x] 8.5 Ensure idempotent behavior by using `skip_existing=True` as default
- [x] 9. Testing and Validation
  - [x] 9.1 Write unit tests for `InfraConfig` defaults and overrides
  - [x] 9.2 Write unit tests for `ProvisioningResult` and `ProvisioningStatus` enum
  - [x] 9.3 Write integration test: run `setup_infra.py --action verify` against live resources in us-east-1
  - [x] 9.4 Validate CloudFormation template deploys cleanly in a test stack
  - [x] 9.5 Verify end-to-end: deploy stack → seed data → query ACC-1001 via application → confirm balance $5,250.75

## Notes

- The DynamoDB Accounts table already exists in us-east-1 (account 861976376325) with seed data. The CloudFormation template should handle the case where the table already exists.
- Bedrock model access requires manual enablement via the AWS console — the script can only verify access, not grant it.
- All provisioning operations are designed to be idempotent and safe to re-run.
- The `setup_infra.py` script uses `boto3` and requires valid AWS credentials in the environment.

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": [1, 2],
      "description": "Foundation: CloudFormation template and configuration module"
    },
    {
      "wave": 2,
      "tasks": [3, 4, 5],
      "description": "Service functions: CloudFormation deploy, IAM policy, Bedrock verification"
    },
    {
      "wave": 3,
      "tasks": [6, 7],
      "description": "Data and validation: test data seeding and resource verification"
    },
    {
      "wave": 4,
      "tasks": [8],
      "description": "CLI orchestrator and entrypoint"
    },
    {
      "wave": 5,
      "tasks": [9],
      "description": "Testing and end-to-end validation"
    }
  ]
}
```
