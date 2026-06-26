"""
Accounts DynamoDB client module for the AI Banking Assistant.

This module encapsulates all DynamoDB access logic for the Accounts table,
providing a class to retrieve account records by account_id. It contains
no endpoint routing or LLM invocation logic.

Requirements: 3.1, 3.4, 6.2, 6.3 - Dedicated Accounts DynamoDB client
with 5-second timeout and proper error handling.
"""

import logging
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ConnectionError, EndpointConnectionError

from exceptions import DynamoDBError
from models import AccountRecord

logger = logging.getLogger(__name__)


class AccountsDynamoDBClient:
    """Client for retrieving account records from DynamoDB.

    Attributes:
        table_name: Name of the Accounts DynamoDB table.
    """

    def __init__(self, table_name: str = "Accounts") -> None:
        """Initialize boto3 DynamoDB resource with 5-second timeout.

        Args:
            table_name: The name of the DynamoDB table. Defaults to "Accounts".
        """
        self.table_name = table_name
        config = Config(
            connect_timeout=5,
            read_timeout=5,
            retries={"max_attempts": 0},
        )
        self._resource = boto3.resource("dynamodb", config=config)
        self._table = self._resource.Table(table_name)

    def get_account(self, account_id: str) -> Optional[AccountRecord]:
        """Retrieve an account from DynamoDB by account_id.

        Args:
            account_id: The partition key to query.

        Returns:
            AccountRecord if found, None if not found.

        Raises:
            DynamoDBError: On empty/None account_id, connection errors,
                or timeouts.
        """
        if not account_id:
            raise DynamoDBError(
                contract_id=account_id or "",
                reason="A valid account_id is required",
            )

        try:
            response = self._table.get_item(Key={"account_id": account_id})
        except (ClientError, ConnectionError, EndpointConnectionError) as exc:
            raise DynamoDBError(
                contract_id=account_id,
                reason=str(exc),
            ) from exc

        item = response.get("Item")
        if item is None:
            return None

        return AccountRecord(
            account_id=item["account_id"],
            balance=float(item["balance"]),
            currency=item["currency"],
            account_type=item["account_type"],
        )
