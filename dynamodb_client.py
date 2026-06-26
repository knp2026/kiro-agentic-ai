"""
DynamoDB client module for the AI Banking Assistant.

This module encapsulates all DynamoDB access logic, providing a class
to retrieve contract records by contract_id. It contains no endpoint
routing or LLM invocation logic.

Requirements: 6.1 - Dedicated DynamoDB_Client module file with no
endpoint routing or LLM invocation logic.
"""

import logging
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ConnectionError, EndpointConnectionError

from exceptions import DynamoDBError
from models import ContractRecord

logger = logging.getLogger(__name__)


class DynamoDBClient:
    """Client for retrieving contract records from DynamoDB.

    Attributes:
        table_name: Name of the DynamoDB table to query.
    """

    def __init__(self, table_name: str = "Contracts") -> None:
        """Initialize boto3 DynamoDB resource with 5-second timeout.

        Args:
            table_name: The name of the DynamoDB table. Defaults to "Contracts".
        """
        self.table_name = table_name
        config = Config(
            connect_timeout=5,
            read_timeout=5,
            retries={"max_attempts": 0},
        )
        self._resource = boto3.resource("dynamodb", config=config)
        self._table = self._resource.Table(table_name)

    def get_contract(self, contract_id: str) -> Optional[ContractRecord]:
        """Retrieve a contract from DynamoDB by contract_id.

        Args:
            contract_id: The primary key to query.

        Returns:
            ContractRecord if found, None if not found.

        Raises:
            DynamoDBError: On empty/None contract_id, connection errors,
                or timeouts.
        """
        if not contract_id:
            raise DynamoDBError(
                contract_id=contract_id or "",
                reason="A valid contract_id is required",
            )

        try:
            response = self._table.get_item(Key={"contract_id": contract_id})
        except (ClientError, ConnectionError, EndpointConnectionError) as exc:
            raise DynamoDBError(
                contract_id=contract_id,
                reason=str(exc),
            ) from exc

        item = response.get("Item")
        if item is None:
            return None

        return ContractRecord(
            contract_id=item["contract_id"],
            amount=float(item["amount"]),
            interest_rate=float(item["interest_rate"]),
            duration=item["duration"],
        )
