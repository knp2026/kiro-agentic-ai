"""
Bedrock client module for the AI Banking Assistant.

This module encapsulates all Amazon Bedrock LLM invocation logic,
providing a class to generate contract summaries. It contains no
endpoint routing or data access logic.

Requirements: 6.2 - Dedicated Bedrock_Client module file that exposes
a callable function for generating summaries with no endpoint routing
or data access logic.
"""

import json
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ReadTimeoutError, ConnectTimeoutError

from exceptions import BedrockError
from models import ContractRecord

logger = logging.getLogger(__name__)

MAX_SUMMARY_LENGTH = 1024


class BedrockClient:
    """Client for generating contract summaries via Amazon Bedrock LLM.

    Attributes:
        model_id: The Bedrock model identifier to use for generation.
        timeout: The timeout in seconds for Bedrock API calls.
    """

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
        timeout: int = 30,
    ) -> None:
        """Initialize the Bedrock runtime client with timeout configuration.

        Args:
            model_id: The Bedrock model ID to use (default: Claude 3 Haiku).
            timeout: Timeout in seconds for API calls (default: 30).
        """
        self.model_id = model_id
        self.timeout = timeout

        config = Config(
            read_timeout=timeout,
            connect_timeout=timeout,
            retries={"max_attempts": 0},
        )
        self._client = boto3.client("bedrock-runtime", config=config)

    def _build_prompt(self, contract_record: ContractRecord) -> str:
        """Construct the prompt for the Bedrock model.

        Args:
            contract_record: The contract data to include in the prompt.

        Returns:
            The formatted prompt string containing all contract fields.
        """
        prompt = (
            "Summarize the following contract details in 3 bullet points:\n"
            f"Contract ID: {contract_record.contract_id}\n"
            f"Amount: {contract_record.amount}\n"
            f"Interest Rate: {contract_record.interest_rate}\n"
            f"Duration: {contract_record.duration}"
        )
        return prompt

    def generate_summary(self, contract_record: ContractRecord) -> str:
        """Generate a summary of a contract using Bedrock LLM.

        Constructs a prompt from the contract record, invokes the Bedrock
        model, extracts the generated text, and truncates to 1024 characters.

        Args:
            contract_record: The contract data to summarize.

        Returns:
            Summary text, truncated to a maximum of 1024 characters.

        Raises:
            BedrockError: On API errors or timeout.
        """
        try:
            prompt = self._build_prompt(contract_record)

            body = json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 512,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                }
            )

            response = self._client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=body,
            )

            response_body = json.loads(response["body"].read())
            generated_text = response_body["content"][0]["text"]

            # Truncate to maximum 1024 characters
            return generated_text[:MAX_SUMMARY_LENGTH]

        except (ReadTimeoutError, ConnectTimeoutError) as e:
            reason = f"Bedrock request timed out: {str(e)}"
            logger.error(reason)
            raise BedrockError(reason=reason)
        except ClientError as e:
            reason = f"Bedrock API error: {e.response['Error']['Message']}"
            logger.error(reason)
            raise BedrockError(reason=reason)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            reason = f"Failed to parse Bedrock response: {str(e)}"
            logger.error(reason)
            raise BedrockError(reason=reason)
        except Exception as e:
            reason = f"Unexpected error invoking Bedrock: {str(e)}"
            logger.error(reason)
            raise BedrockError(reason=reason)
