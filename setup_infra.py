"""Infrastructure provisioning script for the Multi-Agent Orchestrator feature.

This module provides automated provisioning of AWS infrastructure required by
the AI Banking Assistant's Multi-Agent Orchestrator. It handles:

- CloudFormation stack deployment (DynamoDB Accounts table + IAM policy)
- IAM policy creation for DynamoDB read access and Bedrock model invocation
- Amazon Bedrock model access verification
- Test data seeding into the DynamoDB Accounts table
- Resource verification across all provisioned components

Usage:
    python setup_infra.py --action deploy    # Full provisioning workflow
    python setup_infra.py --action verify    # Verify existing resources
    python setup_infra.py --action seed      # Seed test data only
"""

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import List, Optional

import boto3
from botocore.exceptions import WaiterError


class ProvisioningStatus(Enum):
    """Status of a provisioning step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ProvisioningResult:
    """Result of a single provisioning step."""

    step_name: str
    status: ProvisioningStatus
    message: str
    resource_arn: Optional[str] = None


@dataclass
class InfraConfig:
    """Configuration for infrastructure provisioning."""

    region: str = "us-east-1"
    account_id: str = "861976376325"
    table_name: str = "Accounts"
    stack_name: str = "MultiAgentOrchestratorInfra"
    bedrock_model_id: str = "anthropic.claude-haiku-4-5-20251001-v1:0"
    policy_name: str = "MultiAgentOrchestratorPolicy"


@dataclass
class AccountSeedData:
    """Seed data for a single account record."""

    account_id: str
    balance: float
    currency: str
    account_type: str


def _stack_exists(cfn_client, stack_name: str) -> bool:
    """Check if a CloudFormation stack exists and is not in DELETE_COMPLETE state.

    Args:
        cfn_client: A boto3 CloudFormation client.
        stack_name: The name of the stack to check.

    Returns:
        True if the stack exists and is not in DELETE_COMPLETE state, False otherwise.
    """
    try:
        response = cfn_client.describe_stacks(StackName=stack_name)
        stacks = response["Stacks"]
        return len(stacks) > 0 and stacks[0]["StackStatus"] != "DELETE_COMPLETE"
    except cfn_client.exceptions.ClientError as e:
        if "does not exist" in str(e):
            return False
        raise


def deploy_cloudformation_stack(
    config: InfraConfig,
    template_path: str,
    wait: bool = True,
) -> ProvisioningResult:
    """Deploy or update the CloudFormation stack.

    Args:
        config: Infrastructure configuration.
        template_path: Path to the CloudFormation template file.
        wait: Whether to wait for stack operations to complete.

    Returns:
        ProvisioningResult with the outcome of the deployment.
    """
    cfn_client = boto3.client("cloudformation", region_name=config.region)

    # Read template
    with open(template_path, "r") as f:
        template_body = f.read()

    # Check if stack exists
    stack_exists = _stack_exists(cfn_client, config.stack_name)

    try:
        if not stack_exists:
            # Create new stack
            response = cfn_client.create_stack(
                StackName=config.stack_name,
                TemplateBody=template_body,
                Capabilities=["CAPABILITY_NAMED_IAM"],
                Tags=[
                    {"Key": "Project", "Value": "AIBankingAssistant"},
                    {"Key": "Feature", "Value": "MultiAgentOrchestrator"},
                ],
            )
        else:
            # Update existing stack
            try:
                cfn_client.update_stack(
                    StackName=config.stack_name,
                    TemplateBody=template_body,
                    Capabilities=["CAPABILITY_NAMED_IAM"],
                    Tags=[
                        {"Key": "Project", "Value": "AIBankingAssistant"},
                        {"Key": "Feature", "Value": "MultiAgentOrchestrator"},
                    ],
                )
            except cfn_client.exceptions.ClientError as e:
                if "No updates are to be performed" in str(e):
                    return ProvisioningResult(
                        step_name="deploy_cloudformation_stack",
                        status=ProvisioningStatus.SKIPPED,
                        message="No updates are to be performed",
                    )
                raise

        # Waiter logic for stack_create_complete and stack_update_complete
        if wait:
            try:
                if not stack_exists:
                    waiter = cfn_client.get_waiter("stack_create_complete")
                else:
                    waiter = cfn_client.get_waiter("stack_update_complete")
                waiter.wait(StackName=config.stack_name)
            except WaiterError as e:
                return ProvisioningResult(
                    step_name="deploy_cloudformation_stack",
                    status=ProvisioningStatus.FAILED,
                    message=f"Stack operation failed while waiting: {str(e)}",
                )

        # Retrieve actual stack ARN after successful operation
        describe_response = cfn_client.describe_stacks(StackName=config.stack_name)
        stack_arn = describe_response["Stacks"][0]["StackId"]

        success_message = (
            "Stack created successfully"
            if not stack_exists
            else "Stack updated successfully"
        )

        return ProvisioningResult(
            step_name="deploy_cloudformation_stack",
            status=ProvisioningStatus.COMPLETED,
            message=success_message,
            resource_arn=stack_arn,
        )

    except cfn_client.exceptions.ClientError as e:
        return ProvisioningResult(
            step_name="deploy_cloudformation_stack",
            status=ProvisioningStatus.FAILED,
            message=f"CloudFormation deployment failed: {str(e)}",
        )


def create_iam_policy(
    config: InfraConfig,
    attach_to_role: Optional[str] = None,
) -> ProvisioningResult:
    """Create the IAM managed policy for DynamoDB + Bedrock access.

    Args:
        config: Infrastructure configuration.
        attach_to_role: Optional IAM role name to attach the policy to.

    Returns:
        ProvisioningResult with the outcome of the policy creation.
    """
    iam_client = boto3.client("iam", region_name=config.region)

    # Build policy document with two statements
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AccountsTableReadAccess",
                "Effect": "Allow",
                "Action": ["dynamodb:GetItem"],
                "Resource": f"arn:aws:dynamodb:{config.region}:{config.account_id}:table/{config.table_name}",
            },
            {
                "Sid": "BedrockIntentClassification",
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": f"arn:aws:bedrock:{config.region}::foundation-model/{config.bedrock_model_id}",
            },
        ],
    }

    # Create policy, handle EntityAlreadyExists
    policy_arn = f"arn:aws:iam::{config.account_id}:policy/{config.policy_name}"
    try:
        response = iam_client.create_policy(
            PolicyName=config.policy_name,
            PolicyDocument=json.dumps(policy_document),
            Description="IAM policy for Multi-Agent Orchestrator - DynamoDB read + Bedrock invoke",
        )
        policy_arn = response["Policy"]["Arn"]
    except iam_client.exceptions.EntityAlreadyExistsException:
        return ProvisioningResult(
            step_name="create_iam_policy",
            status=ProvisioningStatus.SKIPPED,
            message="Policy already exists",
            resource_arn=policy_arn,
        )
    except Exception as e:
        return ProvisioningResult(
            step_name="create_iam_policy",
            status=ProvisioningStatus.FAILED,
            message=f"Failed to create IAM policy: {str(e)}",
        )

    # Optional attach_to_role
    if attach_to_role:
        try:
            iam_client.attach_role_policy(
                RoleName=attach_to_role,
                PolicyArn=policy_arn,
            )
        except Exception as e:
            return ProvisioningResult(
                step_name="create_iam_policy",
                status=ProvisioningStatus.FAILED,
                message=f"Policy created but failed to attach to role '{attach_to_role}': {str(e)}",
                resource_arn=policy_arn,
            )

    # Return success with policy ARN
    return ProvisioningResult(
        step_name="create_iam_policy",
        status=ProvisioningStatus.COMPLETED,
        message="IAM policy created successfully",
        resource_arn=policy_arn,
    )


def verify_bedrock_model_access(config: InfraConfig) -> ProvisioningResult:
    """Verify that the Bedrock model is accessible in the target region.

    Args:
        config: Infrastructure configuration.

    Returns:
        ProvisioningResult with the outcome of the verification.
    """
    # 5.1: Create Bedrock client (NOT bedrock-runtime)
    try:
        bedrock_client = boto3.client("bedrock", region_name=config.region)
    except Exception as e:
        return ProvisioningResult(
            step_name="verify_bedrock_model_access",
            status=ProvisioningStatus.FAILED,
            message=f"Failed to create Bedrock client: {str(e)}",
        )

    # 5.2: Call get_foundation_model
    try:
        response = bedrock_client.get_foundation_model(
            modelIdentifier=config.bedrock_model_id
        )
    except bedrock_client.exceptions.ResourceNotFoundException:
        # 5.5: Handle invalid model ID
        return ProvisioningResult(
            step_name="verify_bedrock_model_access",
            status=ProvisioningStatus.FAILED,
            message=f"Model '{config.bedrock_model_id}' not found. Verify the model ID is correct.",
        )
    except bedrock_client.exceptions.AccessDeniedException:
        # 5.5: Handle permission errors
        return ProvisioningResult(
            step_name="verify_bedrock_model_access",
            status=ProvisioningStatus.FAILED,
            message="Access denied. Ensure your IAM credentials have bedrock:GetFoundationModel permission.",
        )
    except Exception as e:
        # 5.5: Handle other exceptions
        return ProvisioningResult(
            step_name="verify_bedrock_model_access",
            status=ProvisioningStatus.FAILED,
            message=f"Failed to verify Bedrock model access: {str(e)}",
        )

    # 5.3: Parse response for modelLifecycle status
    model_details = response.get("modelDetails", {})
    model_lifecycle = model_details.get("modelLifecycle", {})
    status = model_lifecycle.get("status", "UNKNOWN")
    model_arn = model_details.get("modelArn", "")

    # 5.4: Return based on status
    if status == "ACTIVE":
        return ProvisioningResult(
            step_name="verify_bedrock_model_access",
            status=ProvisioningStatus.COMPLETED,
            message=f"Bedrock model is active and accessible (status: {status})",
            resource_arn=model_arn,
        )
    else:
        return ProvisioningResult(
            step_name="verify_bedrock_model_access",
            status=ProvisioningStatus.FAILED,
            message=(
                f"Bedrock model status is '{status}', not ACTIVE. "
                "Please enable model access via the AWS Bedrock console: "
                "https://console.aws.amazon.com/bedrock/home#/modelaccess"
            ),
            resource_arn=model_arn,
        )


# 6.3: Default test accounts
DEFAULT_TEST_ACCOUNTS: List[AccountSeedData] = [
    AccountSeedData("ACC-1001", 5250.75, "USD", "savings"),
    AccountSeedData("ACC-1002", 1200.00, "USD", "checking"),
    AccountSeedData("ACC-1003", 48000.00, "USD", "investment"),
]


def seed_test_data(
    config: InfraConfig,
    accounts: Optional[List[AccountSeedData]] = None,
    overwrite: bool = False,
) -> ProvisioningResult:
    """Seed the Accounts table with test data.

    Args:
        config: Infrastructure configuration.
        accounts: List of accounts to seed. Defaults to DEFAULT_TEST_ACCOUNTS.
        overwrite: Whether to overwrite existing records.

    Returns:
        ProvisioningResult with the outcome of the seeding.
    """
    if accounts is None:
        accounts = DEFAULT_TEST_ACCOUNTS

    dynamodb = boto3.resource("dynamodb", region_name=config.region)
    table = dynamodb.Table(config.table_name)

    items_written = 0

    try:
        # 6.2: Use batch_writer for efficiency
        with table.batch_writer() as batch:
            for account in accounts:
                # 6.1: Conditional write - check existence when overwrite=False
                if not overwrite:
                    try:
                        response = table.get_item(Key={"account_id": account.account_id})
                        if "Item" in response:
                            continue  # Skip existing items
                    except Exception:
                        pass  # If check fails, proceed with write

                # 6.4: Convert float balance to Decimal for DynamoDB compatibility
                item = {
                    "account_id": account.account_id,
                    "balance": Decimal(str(account.balance)),
                    "currency": account.currency,
                    "account_type": account.account_type,
                }
                batch.put_item(Item=item)
                items_written += 1

        # 6.5: Return result with count of items written
        return ProvisioningResult(
            step_name="seed_test_data",
            status=ProvisioningStatus.COMPLETED,
            message=f"Successfully seeded {items_written} items to {config.table_name}",
        )

    except Exception as e:
        return ProvisioningResult(
            step_name="seed_test_data",
            status=ProvisioningStatus.FAILED,
            message=f"Failed to seed test data: {str(e)}",
        )


def verify_all_resources(config: InfraConfig) -> List[ProvisioningResult]:
    """Run verification checks on all provisioned resources.

    Each check is independent — one failure does not prevent others from running.
    This function is read-only and does not modify any resources.

    Args:
        config: Infrastructure configuration.

    Returns:
        List of ProvisioningResult, one per verification check.
    """
    results: List[ProvisioningResult] = []

    # 7.1: DynamoDB table status check
    try:
        dynamodb_client = boto3.client("dynamodb", region_name=config.region)
        response = dynamodb_client.describe_table(TableName=config.table_name)
        table_status = response["Table"]["TableStatus"]
        table_arn = response["Table"]["TableArn"]
        if table_status == "ACTIVE":
            results.append(ProvisioningResult(
                step_name="verify_dynamodb_table",
                status=ProvisioningStatus.COMPLETED,
                message=f"Table '{config.table_name}' is ACTIVE",
                resource_arn=table_arn,
            ))
        else:
            results.append(ProvisioningResult(
                step_name="verify_dynamodb_table",
                status=ProvisioningStatus.FAILED,
                message=f"Table '{config.table_name}' status is '{table_status}', expected ACTIVE",
                resource_arn=table_arn,
            ))
    except Exception as e:
        results.append(ProvisioningResult(
            step_name="verify_dynamodb_table",
            status=ProvisioningStatus.FAILED,
            message=f"Failed to verify DynamoDB table: {str(e)}",
        ))

    # 7.2: Seed data count check
    try:
        dynamodb_client = boto3.client("dynamodb", region_name=config.region)
        response = dynamodb_client.scan(TableName=config.table_name, Select="COUNT")
        count = response["Count"]
        results.append(ProvisioningResult(
            step_name="verify_seed_data",
            status=ProvisioningStatus.COMPLETED,
            message=f"Table contains {count} items",
        ))
    except Exception as e:
        results.append(ProvisioningResult(
            step_name="verify_seed_data",
            status=ProvisioningStatus.FAILED,
            message=f"Failed to verify seed data: {str(e)}",
        ))

    # 7.3: Bedrock model access check
    try:
        bedrock_client = boto3.client("bedrock", region_name=config.region)
        response = bedrock_client.get_foundation_model(
            modelIdentifier=config.bedrock_model_id
        )
        model_details = response.get("modelDetails", {})
        model_lifecycle = model_details.get("modelLifecycle", {})
        status = model_lifecycle.get("status", "UNKNOWN")
        model_arn = model_details.get("modelArn", "")
        if status == "ACTIVE":
            results.append(ProvisioningResult(
                step_name="verify_bedrock_model",
                status=ProvisioningStatus.COMPLETED,
                message=f"Bedrock model is ACTIVE",
                resource_arn=model_arn,
            ))
        else:
            results.append(ProvisioningResult(
                step_name="verify_bedrock_model",
                status=ProvisioningStatus.FAILED,
                message=f"Bedrock model status is '{status}', not ACTIVE",
                resource_arn=model_arn,
            ))
    except Exception as e:
        results.append(ProvisioningResult(
            step_name="verify_bedrock_model",
            status=ProvisioningStatus.FAILED,
            message=f"Failed to verify Bedrock model: {str(e)}",
        ))

    # 7.4: IAM policy existence check
    try:
        iam_client = boto3.client("iam", region_name=config.region)
        policy_arn = f"arn:aws:iam::{config.account_id}:policy/{config.policy_name}"
        response = iam_client.get_policy(PolicyArn=policy_arn)
        results.append(ProvisioningResult(
            step_name="verify_iam_policy",
            status=ProvisioningStatus.COMPLETED,
            message=f"IAM policy '{config.policy_name}' exists",
            resource_arn=policy_arn,
        ))
    except Exception as e:
        results.append(ProvisioningResult(
            step_name="verify_iam_policy",
            status=ProvisioningStatus.FAILED,
            message=f"Failed to verify IAM policy: {str(e)}",
        ))

    # 7.6: Return list of results
    return results


def run_provisioning(
    config: InfraConfig,
    skip_existing: bool = True,
) -> List[ProvisioningResult]:
    """Orchestrate the full provisioning workflow.

    Executes: CloudFormation deploy → Bedrock verify → Seed data → Verify all.

    Args:
        config: Infrastructure configuration.
        skip_existing: Skip steps where resources already exist.

    Returns:
        Ordered list of all step results.
    """
    results: List[ProvisioningResult] = []

    # Step 1: Deploy CloudFormation stack
    cfn_result = deploy_cloudformation_stack(config, "infra/cloudformation.yaml", wait=True)
    results.append(cfn_result)

    # Step 2: Verify Bedrock model access
    bedrock_result = verify_bedrock_model_access(config)
    results.append(bedrock_result)

    # Step 3: Create standalone IAM policy (fallback if CFN failed)
    if cfn_result.status == ProvisioningStatus.FAILED:
        iam_result = create_iam_policy(config)
        results.append(iam_result)

    # Step 4: Seed test data
    seed_result = seed_test_data(config, overwrite=not skip_existing)
    results.append(seed_result)

    # Step 5: Verify all resources
    verification_results = verify_all_resources(config)
    results.extend(verification_results)

    return results


def print_summary_report(results: List[ProvisioningResult]) -> None:
    """Print a colored summary report of provisioning results.

    Args:
        results: List of ProvisioningResult to display.
    """
    # ANSI color codes
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    print(f"\n{BOLD}{'='*60}")
    print("  Infrastructure Provisioning Summary")
    print(f"{'='*60}{RESET}\n")

    for result in results:
        if result.status == ProvisioningStatus.COMPLETED:
            icon = f"{GREEN}✓{RESET}"
        elif result.status == ProvisioningStatus.SKIPPED:
            icon = f"{YELLOW}○{RESET}"
        elif result.status == ProvisioningStatus.FAILED:
            icon = f"{RED}✗{RESET}"
        else:
            icon = "•"

        print(f"  {icon} {result.step_name}: {result.message}")
        if result.resource_arn:
            print(f"      ARN: {result.resource_arn}")

    # Summary counts
    completed = sum(1 for r in results if r.status == ProvisioningStatus.COMPLETED)
    failed = sum(1 for r in results if r.status == ProvisioningStatus.FAILED)
    skipped = sum(1 for r in results if r.status == ProvisioningStatus.SKIPPED)

    print(f"\n{BOLD}Results:{RESET} {GREEN}{completed} passed{RESET}, {RED}{failed} failed{RESET}, {YELLOW}{skipped} skipped{RESET}")
    print()


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Infrastructure provisioning for Multi-Agent Orchestrator"
    )
    parser.add_argument(
        "--action",
        choices=["deploy", "verify", "seed"],
        required=True,
        help="Action to perform: deploy (full workflow), verify (check resources), seed (seed data only)",
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    config = InfraConfig(region=args.region)

    if args.action == "deploy":
        results = run_provisioning(config, skip_existing=True)
    elif args.action == "verify":
        results = verify_all_resources(config)
    elif args.action == "seed":
        result = seed_test_data(config)
        results = [result]

    print_summary_report(results)
