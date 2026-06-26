"""
Pydantic models module for the AI Banking Assistant.

This module defines request/response schemas and domain data models
including ChatRequest, ContractRecord, and ChatResponse.

Requirements: 1.1, 2.2, 5.1, 6.4 - Modules can be imported and tested independently.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for the POST /chat endpoint.

    Attributes:
        message: The user's chat message (required, max 1000 characters).
        contract_id: Optional contract identifier to look up.
    """

    message: str = Field(..., max_length=1000)
    contract_id: Optional[str] = None


class ContractRecord(BaseModel):
    """Domain model representing a contract record from DynamoDB.

    Attributes:
        contract_id: The unique identifier of the contract.
        amount: The monetary amount of the contract.
        interest_rate: The annual interest rate (decimal).
        duration: The contract duration (e.g., "5 years").
    """

    contract_id: str
    amount: float
    interest_rate: float
    duration: str


class AccountRecord(BaseModel):
    """Domain model representing an account record from DynamoDB.

    Attributes:
        account_id: The unique identifier of the account.
        balance: The current account balance.
        currency: The currency code (e.g., "USD").
        account_type: The type of account (e.g., "savings", "checking").
    """

    account_id: str
    balance: float
    currency: str
    account_type: str


class ChatResponse(BaseModel):
    """Response model for the POST /chat endpoint.

    Attributes:
        message: Human-readable response message.
        contract_summary: Bedrock-generated summary or null.
        status: Either "AUTO" or "ESCALATE".
    """

    message: str
    contract_summary: Optional[str] = None
    status: str
