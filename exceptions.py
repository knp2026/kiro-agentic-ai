"""
Custom exceptions module for the AI Banking Assistant.

This module defines custom exception classes for DynamoDB and Bedrock
error handling, enabling structured error propagation throughout
the application.

Requirements: 2.4, 4.3, 6.4 - Modules can be imported and tested independently.
"""


class DynamoDBError(Exception):
    """Raised when DynamoDB operations fail.

    Attributes:
        contract_id: The contract_id that was being queried when the error occurred.
        reason: A description of the failure reason.
    """

    def __init__(self, contract_id: str, reason: str) -> None:
        self.contract_id = contract_id
        self.reason = reason
        super().__init__(f"DynamoDB error for contract '{contract_id}': {reason}")


class BedrockError(Exception):
    """Raised when Bedrock invocation fails.

    Attributes:
        reason: A description of the failure reason.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Bedrock error: {reason}")
