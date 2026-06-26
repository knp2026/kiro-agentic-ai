"""Intent classification module for the Multi-Agent Orchestrator."""

import json
import logging
from typing import Literal

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ReadTimeoutError, ConnectTimeoutError

from exceptions import BedrockError

logger = logging.getLogger(__name__)

IntentType = Literal["balance_inquiry", "contract_inquiry"]

CLASSIFICATION_PROMPT_TEMPLATE = """Classify the following user message into exactly one intent.

Possible intents:
- "balance_inquiry": The user wants to check an account balance or account information.
- "contract_inquiry": The user wants to look up or ask about a contract.

User message: {message}

Respond with ONLY the intent name, nothing else. Your response must be exactly one of: balance_inquiry, contract_inquiry"""


class IntentClassifier:
    """Classifies user messages into intents using Bedrock LLM.

    Attributes:
        model_id: The Bedrock model identifier for classification.
        timeout: Timeout in seconds for Bedrock API calls.
    """

    VALID_INTENTS: set[str] = {"balance_inquiry", "contract_inquiry"}

    def __init__(
        self,
        model_id: str = "anthropic.claude-haiku-4-5-20251001-v1:0",
        timeout: int = 30,
    ) -> None:
        self.model_id = model_id
        self.timeout = timeout

        config = Config(
            region_name="us-east-1",
            read_timeout=timeout,
            connect_timeout=timeout,
            retries={"max_attempts": 0},
        )
        self._client = boto3.client("bedrock-runtime", config=config)

    def classify(self, message: str) -> IntentType:
        """Classify a user message into an intent.

        Args:
            message: The user's chat message.

        Returns:
            The classified intent: "balance_inquiry" or "contract_inquiry".

        Raises:
            BedrockError: On API errors, timeout, or unparseable response.
        """
        try:
            prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(message=message)

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": prompt}],
            })

            response = self._client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=body,
            )

            response_body = json.loads(response["body"].read())
            intent = response_body["content"][0]["text"].strip().lower()

            if intent not in self.VALID_INTENTS:
                raise BedrockError(
                    reason=f"Invalid intent returned: '{intent}'"
                )

            return intent  # type: ignore[return-value]

        except BedrockError:
            raise
        except (ReadTimeoutError, ConnectTimeoutError) as e:
            raise BedrockError(reason=f"Intent classification timed out: {e}")
        except ClientError as e:
            raise BedrockError(
                reason=f"Intent classification API error: {e.response['Error']['Message']}"
            )
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise BedrockError(
                reason=f"Failed to parse classification response: {e}"
            )
        except Exception as e:
            raise BedrockError(reason=f"Unexpected classification error: {e}")
