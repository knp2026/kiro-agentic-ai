# AI Banking Assistant

A FastAPI-based chatbot that retrieves banking contract details from DynamoDB and generates AI-powered summaries using Amazon Bedrock (Claude). Implements a human-in-the-loop pattern where requests are either handled automatically or escalated to human support.

## Architecture

```
Customer → POST /chat → DynamoDB (contract lookup) → Bedrock (AI summary) → Response
                              ↓ (not found)
                         ESCALATE → Human Agent
```

**Key components:**

- `main.py` — FastAPI app with `/chat` endpoint and request orchestration
- `dynamodb_client.py` — DynamoDB access layer for contract retrieval
- `bedrock_client.py` — Amazon Bedrock integration for AI summary generation
- `models.py` — Pydantic request/response schemas
- `exceptions.py` — Custom exception classes for structured error handling

## Prerequisites

- Python 3.10+
- AWS account with:
  - DynamoDB table `Contracts` in us-east-1 (partition key: `contract_id`, String)
  - Bedrock model access for Claude Haiku 4.5 (`anthropic.claude-haiku-4-5-20251001-v1:0`)
- AWS credentials configured (default profile or environment variables)

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install dev dependencies (for testing)
pip install -r requirements-dev.txt
```

## Running the Server

```bash
uvicorn main:app --port 8000
```

## API Usage

### POST /chat

**Request:**
```json
{
  "message": "Show me my loan contract details",
  "contract_id": "C123"
}
```

**Response (success — AUTO):**
```json
{
  "message": "Contract C123 found and summarized successfully.",
  "contract_summary": "• Contract amount: $50,000\n• Interest rate: 5%\n• Duration: 5 years",
  "status": "AUTO"
}
```

**Response (not found — ESCALATE):**
```json
{
  "message": "Contract not found, escalating to support",
  "contract_summary": null,
  "status": "ESCALATE"
}
```

### Status Values

| Status | Meaning |
|--------|---------|
| `AUTO` | Request handled automatically by AI |
| `ESCALATE` | Requires human agent intervention |

## Running Tests

```bash
pytest
```

Tests use [moto](https://github.com/getmoto/moto) to mock AWS services locally.

## Demo

Run the demo script to exercise both use cases against a live server:

```bash
# Start server first in another terminal
uvicorn main:app --port 8000

# Run demo
python demo_use_cases.py
```

- **Use Case 1:** Valid contract → AI summary returned (AUTO)
- **Use Case 2:** Invalid contract → Escalated to human (ESCALATE)

## Project Structure

```
├── main.py                  # FastAPI app and /chat endpoint
├── dynamodb_client.py       # DynamoDB contract retrieval
├── bedrock_client.py        # Bedrock AI summary generation
├── models.py                # Pydantic data models
├── exceptions.py            # Custom exceptions
├── demo_use_cases.py        # Live demo script
├── test_dynamodb_client.py  # Unit tests
├── requirements.txt         # Runtime dependencies
└── requirements-dev.txt     # Test dependencies
```

## AWS Resources

| Resource | Details |
|----------|---------|
| DynamoDB Table | `Contracts` (on-demand billing, us-east-1) |
| Bedrock Model | `anthropic.claude-haiku-4-5-20251001-v1:0` via inference profile `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
