# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-06-26

### Added
- Multi-Agent Orchestrator with intent classification (Bedrock Claude Haiku)
- Account Balance Agent (regex extraction + DynamoDB lookup)
- Contract Agent (DynamoDB lookup + Bedrock summarization)
- Infrastructure provisioning script (`setup_infra.py`) with CLI
- CloudFormation template (`infra/cloudformation.yaml`) for DynamoDB + IAM
- IAM managed policy `MultiAgentOrchestratorPolicy` (least privilege)
- Bedrock model access verification
- Test data seeding (ACC-1001, ACC-1002, ACC-1003)
- Resource verification function (read-only checks)
- Automated test suite for Use Case 1 & 2 (17 tests)
- Integration test suite with moto mocking
- MCP S3 server for document management
- Documentation: architecture overview, test guide, infrastructure checklist

### Infrastructure
- AWS Region: us-east-1
- AWS Account: 861976376325
- DynamoDB Tables: Accounts, Contracts (PAY_PER_REQUEST)
- Bedrock Model: anthropic.claude-haiku-4-5-20251001-v1:0
- CloudFormation Stack: MultiAgentOrchestratorInfra
