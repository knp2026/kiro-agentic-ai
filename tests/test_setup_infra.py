"""Unit tests for setup_infra.py."""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from setup_infra import (
    InfraConfig,
    ProvisioningResult,
    ProvisioningStatus,
    _stack_exists,
    deploy_cloudformation_stack,
)


class TestStackExists:
    """Tests for _stack_exists helper function."""

    def test_returns_true_when_stack_exists_and_active(self):
        """Stack in CREATE_COMPLETE state should return True."""
        cfn_client = MagicMock()
        cfn_client.describe_stacks.return_value = {
            "Stacks": [
                {
                    "StackName": "TestStack",
                    "StackStatus": "CREATE_COMPLETE",
                }
            ]
        }

        assert _stack_exists(cfn_client, "TestStack") is True

    def test_returns_true_when_stack_in_update_complete(self):
        """Stack in UPDATE_COMPLETE state should return True."""
        cfn_client = MagicMock()
        cfn_client.describe_stacks.return_value = {
            "Stacks": [
                {
                    "StackName": "TestStack",
                    "StackStatus": "UPDATE_COMPLETE",
                }
            ]
        }

        assert _stack_exists(cfn_client, "TestStack") is True

    def test_returns_false_when_stack_in_delete_complete(self):
        """Stack in DELETE_COMPLETE state should return False."""
        cfn_client = MagicMock()
        cfn_client.describe_stacks.return_value = {
            "Stacks": [
                {
                    "StackName": "TestStack",
                    "StackStatus": "DELETE_COMPLETE",
                }
            ]
        }

        assert _stack_exists(cfn_client, "TestStack") is False

    def test_returns_false_when_stack_does_not_exist(self):
        """ClientError with 'does not exist' should return False."""
        cfn_client = MagicMock()
        error_response = {
            "Error": {
                "Code": "ValidationError",
                "Message": "Stack with id TestStack does not exist",
            }
        }
        cfn_client.describe_stacks.side_effect = ClientError(
            error_response, "DescribeStacks"
        )
        cfn_client.exceptions.ClientError = ClientError

        assert _stack_exists(cfn_client, "TestStack") is False

    def test_raises_other_client_errors(self):
        """ClientError without 'does not exist' should be re-raised."""
        cfn_client = MagicMock()
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "User is not authorized to perform this operation",
            }
        }
        cfn_client.describe_stacks.side_effect = ClientError(
            error_response, "DescribeStacks"
        )
        cfn_client.exceptions.ClientError = ClientError

        with pytest.raises(ClientError):
            _stack_exists(cfn_client, "TestStack")

    def test_returns_false_when_stacks_list_empty(self):
        """Empty stacks list should return False."""
        cfn_client = MagicMock()
        cfn_client.describe_stacks.return_value = {"Stacks": []}

        assert _stack_exists(cfn_client, "TestStack") is False


class TestDeployCloudFormationStackUpdate:
    """Tests for the update_stack path in deploy_cloudformation_stack."""

    @patch("setup_infra.boto3.client")
    @patch("setup_infra._stack_exists")
    @patch("builtins.open", create=True)
    def test_update_stack_no_updates_returns_skipped(
        self, mock_open, mock_stack_exists, mock_boto_client
    ):
        """When update_stack raises 'No updates are to be performed', return SKIPPED."""
        from unittest.mock import mock_open as _mock_open

        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_open.return_value.read = MagicMock(return_value="template body")

        mock_stack_exists.return_value = True

        cfn_mock = MagicMock()
        mock_boto_client.return_value = cfn_mock

        error_response = {
            "Error": {
                "Code": "ValidationError",
                "Message": "No updates are to be performed.",
            }
        }
        cfn_mock.update_stack.side_effect = ClientError(
            error_response, "UpdateStack"
        )
        cfn_mock.exceptions.ClientError = ClientError

        config = InfraConfig()
        result = deploy_cloudformation_stack(config, "template.yaml")

        assert result.status == ProvisioningStatus.SKIPPED
        assert "No updates are to be performed" in result.message

    @patch("setup_infra.boto3.client")
    @patch("setup_infra._stack_exists")
    @patch("builtins.open", create=True)
    def test_update_stack_other_error_returns_failed(
        self, mock_open, mock_stack_exists, mock_boto_client
    ):
        """When update_stack raises a different ClientError, return FAILED."""
        from unittest.mock import mock_open as _mock_open

        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_open.return_value.read = MagicMock(return_value="template body")

        mock_stack_exists.return_value = True

        cfn_mock = MagicMock()
        mock_boto_client.return_value = cfn_mock

        error_response = {
            "Error": {
                "Code": "InsufficientCapabilitiesException",
                "Message": "Requires capability CAPABILITY_NAMED_IAM",
            }
        }
        cfn_mock.update_stack.side_effect = ClientError(
            error_response, "UpdateStack"
        )
        cfn_mock.exceptions.ClientError = ClientError

        config = InfraConfig()
        result = deploy_cloudformation_stack(config, "template.yaml")

        assert result.status == ProvisioningStatus.FAILED
        assert "CloudFormation deployment failed" in result.message

    @patch("setup_infra.boto3.client")
    @patch("setup_infra._stack_exists")
    @patch("builtins.open", create=True)
    def test_update_stack_success_returns_completed(
        self, mock_open, mock_stack_exists, mock_boto_client
    ):
        """When update_stack succeeds without error, return COMPLETED."""
        from unittest.mock import mock_open as _mock_open

        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_open.return_value.read = MagicMock(return_value="template body")

        mock_stack_exists.return_value = True

        cfn_mock = MagicMock()
        mock_boto_client.return_value = cfn_mock
        cfn_mock.update_stack.return_value = {"StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/TestStack/guid"}
        cfn_mock.exceptions.ClientError = ClientError

        config = InfraConfig()
        result = deploy_cloudformation_stack(config, "template.yaml")

        assert result.status == ProvisioningStatus.COMPLETED
        cfn_mock.update_stack.assert_called_once_with(
            StackName=config.stack_name,
            TemplateBody="template body",
            Capabilities=["CAPABILITY_NAMED_IAM"],
            Tags=[
                {"Key": "Project", "Value": "AIBankingAssistant"},
                {"Key": "Feature", "Value": "MultiAgentOrchestrator"},
            ],
        )


class TestInfraConfig:
    """Tests for InfraConfig dataclass defaults and overrides."""

    def test_default_values(self):
        """InfraConfig should have correct default values for all fields."""
        config = InfraConfig()
        assert config.region == "us-east-1"
        assert config.account_id == "861976376325"
        assert config.table_name == "Accounts"
        assert config.stack_name == "MultiAgentOrchestratorInfra"
        assert config.bedrock_model_id == "anthropic.claude-haiku-4-5-20251001-v1:0"
        assert config.policy_name == "MultiAgentOrchestratorPolicy"

    def test_override_individual_field(self):
        """Overriding a single field should keep other defaults intact."""
        config = InfraConfig(region="eu-west-1")
        assert config.region == "eu-west-1"
        assert config.account_id == "861976376325"
        assert config.table_name == "Accounts"
        assert config.stack_name == "MultiAgentOrchestratorInfra"
        assert config.bedrock_model_id == "anthropic.claude-haiku-4-5-20251001-v1:0"
        assert config.policy_name == "MultiAgentOrchestratorPolicy"

    def test_override_all_fields(self):
        """Overriding all fields should use the provided values."""
        config = InfraConfig(
            region="ap-southeast-1",
            account_id="111222333444",
            table_name="CustomTable",
            stack_name="CustomStack",
            bedrock_model_id="amazon.titan-text-express-v1",
            policy_name="CustomPolicy",
        )
        assert config.region == "ap-southeast-1"
        assert config.account_id == "111222333444"
        assert config.table_name == "CustomTable"
        assert config.stack_name == "CustomStack"
        assert config.bedrock_model_id == "amazon.titan-text-express-v1"
        assert config.policy_name == "CustomPolicy"


class TestProvisioningStatus:
    """Tests for ProvisioningStatus enum values."""

    def test_all_enum_values_exist(self):
        """All expected enum members should be defined."""
        assert hasattr(ProvisioningStatus, "PENDING")
        assert hasattr(ProvisioningStatus, "IN_PROGRESS")
        assert hasattr(ProvisioningStatus, "COMPLETED")
        assert hasattr(ProvisioningStatus, "FAILED")
        assert hasattr(ProvisioningStatus, "SKIPPED")

    def test_enum_string_values(self):
        """Enum members should have correct string values."""
        assert ProvisioningStatus.PENDING.value == "pending"
        assert ProvisioningStatus.IN_PROGRESS.value == "in_progress"
        assert ProvisioningStatus.COMPLETED.value == "completed"
        assert ProvisioningStatus.FAILED.value == "failed"
        assert ProvisioningStatus.SKIPPED.value == "skipped"


class TestProvisioningResult:
    """Tests for ProvisioningResult dataclass."""

    def test_construction_with_all_fields(self):
        """ProvisioningResult should store all provided fields correctly."""
        result = ProvisioningResult(
            step_name="deploy_stack",
            status=ProvisioningStatus.COMPLETED,
            message="Stack deployed successfully",
            resource_arn="arn:aws:cloudformation:us-east-1:123456789012:stack/MyStack/guid",
        )
        assert result.step_name == "deploy_stack"
        assert result.status == ProvisioningStatus.COMPLETED
        assert result.message == "Stack deployed successfully"
        assert result.resource_arn == "arn:aws:cloudformation:us-east-1:123456789012:stack/MyStack/guid"

    def test_resource_arn_defaults_to_none(self):
        """resource_arn should default to None when not provided."""
        result = ProvisioningResult(
            step_name="verify_model",
            status=ProvisioningStatus.FAILED,
            message="Model not accessible",
        )
        assert result.step_name == "verify_model"
        assert result.status == ProvisioningStatus.FAILED
        assert result.message == "Model not accessible"
        assert result.resource_arn is None

    def test_resource_arn_explicit_none(self):
        """Explicitly passing resource_arn=None should work."""
        result = ProvisioningResult(
            step_name="seed_data",
            status=ProvisioningStatus.SKIPPED,
            message="Data already exists",
            resource_arn=None,
        )
        assert result.resource_arn is None

    def test_resource_arn_with_value(self):
        """ProvisioningResult should store a provided resource_arn."""
        arn = "arn:aws:iam::861976376325:policy/MultiAgentOrchestratorPolicy"
        result = ProvisioningResult(
            step_name="create_policy",
            status=ProvisioningStatus.COMPLETED,
            message="Policy created",
            resource_arn=arn,
        )
        assert result.resource_arn == arn
