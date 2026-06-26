"""Integration tests for infrastructure provisioning against live AWS resources.

These tests require:
- Valid AWS credentials configured (via env vars, profiles, or instance role)
- Access to the us-east-1 region
- The DynamoDB Accounts table to exist in account 861976376325

Run with: pytest test_integration_infra.py -m integration

Requirements: 5.1, 5.2, 5.4, 6.2
"""

import json
import os
import subprocess
import sys
from decimal import Decimal

import boto3
import pytest
import yaml

from setup_infra import (
    InfraConfig,
    ProvisioningResult,
    ProvisioningStatus,
    seed_test_data,
    verify_all_resources,
)

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "infra", "cloudformation.yaml")


class _CfnLoader(yaml.SafeLoader):
    """YAML loader that handles CloudFormation intrinsic function tags."""
    pass


# Register constructors for common CloudFormation intrinsic functions
_CFN_TAGS = [
    "!Ref", "!GetAtt", "!Sub", "!Join", "!Select", "!Split",
    "!If", "!Equals", "!Not", "!And", "!Or", "!FindInMap",
    "!Base64", "!Cidr", "!GetAZs", "!ImportValue",
    "!Condition", "!Transform",
]

for tag in _CFN_TAGS:
    _CfnLoader.add_constructor(
        tag, lambda loader, node: loader.construct_scalar(node)
    )
    _CfnLoader.add_multi_constructor(
        tag, lambda loader, suffix, node: loader.construct_scalar(node)
    )


def _load_cfn_template(path: str) -> dict:
    """Load a CloudFormation YAML template, handling intrinsic function tags."""
    with open(path, "r") as f:
        return yaml.load(f, Loader=_CfnLoader)


@pytest.mark.integration
class TestVerifyAllResourcesLive:
    """Integration tests for verify_all_resources against live AWS resources in us-east-1."""

    def test_verify_returns_list_of_provisioning_results(self):
        """verify_all_resources should return a list of ProvisioningResult objects."""
        config = InfraConfig()
        results = verify_all_resources(config)

        assert isinstance(results, list)
        assert len(results) > 0
        for result in results:
            assert isinstance(result, ProvisioningResult)

    def test_each_result_has_valid_fields(self):
        """Each ProvisioningResult should have valid step_name, status, and message."""
        config = InfraConfig()
        results = verify_all_resources(config)

        for result in results:
            # step_name must be a non-empty string
            assert isinstance(result.step_name, str)
            assert len(result.step_name) > 0

            # status must be a valid ProvisioningStatus enum value
            assert isinstance(result.status, ProvisioningStatus)
            assert result.status in (
                ProvisioningStatus.COMPLETED,
                ProvisioningStatus.FAILED,
                ProvisioningStatus.SKIPPED,
                ProvisioningStatus.PENDING,
                ProvisioningStatus.IN_PROGRESS,
            )

            # message must be a non-empty string
            assert isinstance(result.message, str)
            assert len(result.message) > 0

            # resource_arn is optional (str or None)
            assert result.resource_arn is None or isinstance(result.resource_arn, str)

    def test_dynamodb_table_check_passes(self):
        """The DynamoDB Accounts table verification should pass (table exists in us-east-1)."""
        config = InfraConfig()
        results = verify_all_resources(config)

        # Find the DynamoDB table verification result
        dynamo_results = [r for r in results if "dynamodb" in r.step_name.lower() or "table" in r.step_name.lower()]
        assert len(dynamo_results) > 0, "Expected at least one DynamoDB table verification result"

        # The table exists in us-east-1, so this check should pass
        table_result = dynamo_results[0]
        assert table_result.status == ProvisioningStatus.COMPLETED
        assert "Accounts" in table_result.message or "ACTIVE" in table_result.message

    def test_verification_checks_are_independent(self):
        """All verification checks should execute regardless of individual failures."""
        config = InfraConfig()
        results = verify_all_resources(config)

        # verify_all_resources checks: table status, seed data count, Bedrock model, IAM policy
        # We expect at least 4 results (one per check)
        assert len(results) >= 4

        # Each check should have a distinct step_name
        step_names = [r.step_name for r in results]
        assert len(step_names) == len(set(step_names)), "Each verification check should have a unique step_name"


@pytest.mark.integration
class TestSetupInfraCliVerify:
    """Integration test running setup_infra.py --action verify as a subprocess."""

    def test_verify_action_exits_successfully(self):
        """Running 'python setup_infra.py --action verify' should exit with code 0."""
        result = subprocess.run(
            [sys.executable, "setup_infra.py", "--action", "verify"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, (
            f"setup_infra.py --action verify exited with code {result.returncode}.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_verify_action_produces_output(self):
        """Running verify action should produce summary output on stdout."""
        result = subprocess.run(
            [sys.executable, "setup_infra.py", "--action", "verify"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # The script should print a summary report
        assert len(result.stdout) > 0, "Expected output from verify action"
        # Summary report should contain provisioning-related keywords
        assert any(
            keyword in result.stdout.lower()
            for keyword in ["passed", "failed", "skipped", "completed", "summary", "verify"]
        ), f"Expected provisioning summary keywords in output. Got: {result.stdout}"


@pytest.mark.integration
class TestCloudFormationTemplateValidation:
    """Integration tests validating the CloudFormation template syntax and structure."""

    def test_validate_template_via_aws_cli(self):
        """aws cloudformation validate-template should succeed for our template."""
        result = subprocess.run(
            [
                "aws", "cloudformation", "validate-template",
                "--template-body", f"file://{TEMPLATE_PATH}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"CloudFormation validate-template failed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # The output should be valid JSON containing template metadata
        output = json.loads(result.stdout)
        assert "Parameters" in output or "Description" in output or "Capabilities" in output

    def test_template_contains_expected_resources(self):
        """The CloudFormation template should define AccountsTable and OrchestratorPolicy."""
        template = _load_cfn_template(TEMPLATE_PATH)

        # Template must have a Resources section
        assert "Resources" in template, "Template is missing a 'Resources' section"

        resources = template["Resources"]

        # Must define the AccountsTable DynamoDB resource
        assert "AccountsTable" in resources, "Template missing 'AccountsTable' resource"
        assert resources["AccountsTable"]["Type"] == "AWS::DynamoDB::Table"

        # Must define the OrchestratorPolicy IAM resource
        assert "OrchestratorPolicy" in resources, "Template missing 'OrchestratorPolicy' resource"
        assert resources["OrchestratorPolicy"]["Type"] == "AWS::IAM::ManagedPolicy"

    def test_template_has_expected_outputs(self):
        """The CloudFormation template should export table ARN, table name, and policy ARN."""
        template = _load_cfn_template(TEMPLATE_PATH)

        assert "Outputs" in template, "Template is missing an 'Outputs' section"

        outputs = template["Outputs"]
        assert "AccountsTableArn" in outputs, "Template missing 'AccountsTableArn' output"
        assert "AccountsTableName" in outputs, "Template missing 'AccountsTableName' output"
        assert "OrchestratorPolicyArn" in outputs, "Template missing 'OrchestratorPolicyArn' output"


@pytest.mark.integration
class TestEndToEndSeedAndQuery:
    """End-to-end integration test: seed data → query DynamoDB → confirm expected values.

    This test class verifies the complete provisioning flow by seeding data into
    the live DynamoDB Accounts table and then querying each account to confirm
    the expected balance, currency, and account_type values.

    Requires live AWS access to DynamoDB in us-east-1.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Seed test data and create DynamoDB resource for querying."""
        self.config = InfraConfig()
        # Ensure seed data exists in the table
        seed_test_data(self.config)
        # Create DynamoDB resource for direct queries
        self.dynamodb = boto3.resource("dynamodb", region_name=self.config.region)
        self.table = self.dynamodb.Table(self.config.table_name)

    def _get_account(self, account_id: str) -> dict:
        """Helper to fetch an account item by account_id."""
        response = self.table.get_item(Key={"account_id": account_id})
        assert "Item" in response, f"Account {account_id} not found in table"
        return response["Item"]

    def test_acc_1001_balance(self):
        """ACC-1001 should have balance of $5,250.75."""
        item = self._get_account("ACC-1001")
        assert item["balance"] == Decimal("5250.75")

    def test_acc_1001_currency(self):
        """ACC-1001 should have currency USD."""
        item = self._get_account("ACC-1001")
        assert item["currency"] == "USD"

    def test_acc_1001_account_type(self):
        """ACC-1001 should be a savings account."""
        item = self._get_account("ACC-1001")
        assert item["account_type"] == "savings"

    def test_acc_1002_present_with_expected_values(self):
        """ACC-1002 should exist with balance $1,200.00, USD, checking."""
        item = self._get_account("ACC-1002")
        assert item["balance"] == Decimal("1200.00")
        assert item["currency"] == "USD"
        assert item["account_type"] == "checking"

    def test_acc_1003_present_with_expected_values(self):
        """ACC-1003 should exist with balance $48,000.00, USD, investment."""
        item = self._get_account("ACC-1003")
        assert item["balance"] == Decimal("48000.00")
        assert item["currency"] == "USD"
        assert item["account_type"] == "investment"
