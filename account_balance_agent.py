"""
Account Balance Agent module for the AI Banking Assistant.

This module implements the Account Balance Agent that extracts account IDs
from user messages, queries the Accounts DynamoDB table, and returns
formatted balance information.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 6.1 - Dedicated Account Balance
Agent with regex-based account_id extraction and proper error handling.
"""

import re
import logging

from fastapi.responses import JSONResponse

from models import ChatRequest, ChatResponse, AccountRecord
from accounts_dynamodb_client import AccountsDynamoDBClient
from exceptions import DynamoDBError

logger = logging.getLogger(__name__)

ACCOUNT_ID_PATTERN = re.compile(r"\b(ACC-\d{4,})\b", re.IGNORECASE)


class AccountBalanceAgent:
    """Agent for handling account balance inquiries.

    Extracts account_id from user messages, queries the Accounts table,
    and returns formatted balance information.
    """

    def __init__(self) -> None:
        self._db_client = AccountsDynamoDBClient()

    def extract_account_id(self, message: str) -> str | None:
        """Extract account_id from a user message.

        Args:
            message: The user's chat message.

        Returns:
            The extracted account_id or None if not found.
        """
        match = ACCOUNT_ID_PATTERN.search(message)
        return match.group(1) if match else None

    def handle(self, request: ChatRequest) -> ChatResponse | JSONResponse:
        """Handle an account balance inquiry request.

        Args:
            request: The incoming ChatRequest.

        Returns:
            ChatResponse with balance info (AUTO) or error info (ESCALATE).
        """
        account_id = self.extract_account_id(request.message)

        if account_id is None:
            return ChatResponse(
                message="Please provide your account ID (e.g., ACC-1234) to check your balance.",
                contract_summary=None,
                status="AUTO",
            )

        try:
            account = self._db_client.get_account(account_id)
        except DynamoDBError as exc:
            logger.warning(
                "Accounts DynamoDB retrieval failed",
                extra={"contract_id": account_id, "reason": exc.reason},
            )
            return JSONResponse(
                status_code=502,
                content={
                    "message": "Service temporarily unavailable",
                    "contract_summary": None,
                    "status": "ESCALATE",
                },
            )

        if account is None:
            return ChatResponse(
                message=f"Account {account_id} not found, escalating to support.",
                contract_summary=None,
                status="ESCALATE",
            )

        return ChatResponse(
            message=(
                f"Account {account.account_id}: "
                f"Balance: {account.balance} {account.currency}, "
                f"Type: {account.account_type}"
            ),
            contract_summary=None,
            status="AUTO",
        )
