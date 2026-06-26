"""
FastAPI application module for the AI Banking Assistant.

This module implements the POST /chat endpoint, request orchestration,
and response construction. It delegates DynamoDB access to dynamodb_client
and Bedrock LLM invocation to bedrock_client.

Requirements: 6.3 - Endpoint routing and request handling module that delegates
to DynamoDB_Client and Bedrock_Client modules.
"""

import logging
import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from models import ChatRequest, ChatResponse
from dynamodb_client import DynamoDBClient
from bedrock_client import BedrockClient
from intent_classifier import IntentClassifier
from account_balance_agent import AccountBalanceAgent
from exceptions import DynamoDBError, BedrockError


# Configure structured JSON logging
class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }
        # Include extra fields if present
        for key in ("contract_id", "status", "reason", "error_type", "error_message", "intent"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry)


# Set up logging configuration
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])

logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(title="AI Banking Assistant", version="1.0.0")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unexpected errors.

    Catches all unhandled exceptions, logs full details, and returns
    HTTP 500 with ESCALATE status.

    Requirements: 7.7
    """
    logger.error(
        "Unexpected error during request processing",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal error",
            "contract_summary": None,
            "status": "ESCALATE",
        },
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse | JSONResponse:
    """POST /chat endpoint with multi-agent orchestration.

    Flow:
    1. If contract_id present → Contract Agent (existing, no classification)
    2. If no contract_id → classify intent via Bedrock
    3. Route to appropriate agent based on intent

    Requirements: 1.2, 1.3, 1.4, 1.6, 4.1, 5.1, 5.2, 5.3, 5.5
    """
    # Log incoming request (Req 7.1)
    logger.info(
        "Incoming chat request",
        extra={
            "contract_id": request.contract_id,
        },
    )

    # Backward compatibility: contract_id present → existing Contract Agent flow
    if request.contract_id:
        return _handle_contract_request(request)

    # No contract_id → classify intent
    classifier = IntentClassifier()
    try:
        intent = classifier.classify(request.message)
    except BedrockError as exc:
        logger.error("Intent classification failed", extra={"reason": exc.reason})
        return ChatResponse(
            message="Unable to classify your request. Please try again or contact support.",
            contract_summary=None,
            status="ESCALATE",
        )

    logger.info("Intent classified", extra={"intent": intent})

    # Route to appropriate agent
    if intent == "balance_inquiry":
        agent = AccountBalanceAgent()
        response = agent.handle(request)
    else:
        # contract_inquiry without contract_id → prompt user
        response = ChatResponse(
            message="Please provide a contract_id to retrieve your contract details.",
            contract_summary=None,
            status="AUTO",
        )

    return response


def _handle_contract_request(request: ChatRequest) -> ChatResponse | JSONResponse:
    """Handle a contract inquiry request using the existing Contract Agent flow.

    This preserves the original behavior for requests that include a contract_id:
    1. Retrieve contract from DynamoDB
    2. Generate summary via Bedrock
    3. Return structured response

    Args:
        request: The incoming ChatRequest (must have contract_id set).

    Returns:
        ChatResponse on success or JSONResponse on DynamoDB/Bedrock errors.
    """
    contract_id = request.contract_id

    # Attempt to retrieve contract from DynamoDB
    dynamo_client = DynamoDBClient()
    bedrock_client = BedrockClient()

    try:
        contract = dynamo_client.get_contract(contract_id)
    except DynamoDBError as exc:
        # Log DynamoDB failure (Req 7.3)
        logger.warning(
            "DynamoDB retrieval failed",
            extra={
                "contract_id": exc.contract_id,
                "reason": exc.reason,
            },
        )
        # Log response status (Req 7.6)
        logger.info("Response sent", extra={"status": "ESCALATE"})
        # Return HTTP 502 (Req 3.4)
        return JSONResponse(
            status_code=502,
            content={
                "message": "Service temporarily unavailable",
                "contract_summary": None,
                "status": "ESCALATE",
            },
        )

    # If contract not found, escalate (Req 3.1, 3.2, 3.3)
    if contract is None:
        response = ChatResponse(
            message="Contract not found, escalating to support",
            contract_summary=None,
            status="ESCALATE",
        )
        # Log response status (Req 7.6)
        logger.info("Response sent", extra={"status": "ESCALATE"})
        return response

    # Log DynamoDB success (Req 7.2)
    logger.info(
        "Contract retrieved successfully",
        extra={"contract_id": contract_id},
    )

    # Generate summary via Bedrock
    try:
        summary = bedrock_client.generate_summary(contract)
    except BedrockError as exc:
        # Log Bedrock failure (Req 7.5)
        logger.error(
            "Bedrock summary generation failed",
            extra={"reason": exc.reason},
        )
        response = ChatResponse(
            message="Summary generation failed",
            contract_summary=None,
            status="ESCALATE",
        )
        # Log response status (Req 7.6)
        logger.info("Response sent", extra={"status": "ESCALATE"})
        return response

    # Log Bedrock success (Req 7.4)
    logger.info("Summary generated successfully")

    # Return successful response (Req 5.2, 5.3, 5.4)
    response = ChatResponse(
        message=f"Contract {contract_id} found and summarized successfully.",
        contract_summary=summary,
        status="AUTO",
    )
    # Log response status (Req 7.6)
    logger.info("Response sent", extra={"status": "AUTO"})
    return response
