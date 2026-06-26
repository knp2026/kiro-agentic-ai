"""
MCP Server for S3 Document Operations.

Exposes read and update tools for documents (Word, PDF, text) stored in
the S3 bucket 'aabg-kiro-demo'. The orchestrator connects to this server
to read and update documents.

Usage:
    python mcp_s3_server.py

Requires:
    pip install mcp boto3 python-docx PyPDF2
"""

import io
import json
import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BUCKET_NAME = "aabg-kiro-demo"
REGION = "us-east-1"

s3_client = boto3.client("s3", region_name=REGION)


def read_document(key: str) -> dict[str, Any]:
    """Read a document from S3 and return its content.

    Supports .txt, .pdf, .docx files.

    Args:
        key: The S3 object key (path) of the document.

    Returns:
        Dict with 'content', 'content_type', and 'metadata'.
    """
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
        body = response["Body"].read()
        content_type = response.get("ContentType", "")
        metadata = response.get("Metadata", {})

        # Extract text based on file type
        if key.endswith(".txt"):
            text_content = body.decode("utf-8")
        elif key.endswith(".pdf"):
            text_content = _extract_pdf_text(body)
        elif key.endswith(".docx"):
            text_content = _extract_docx_text(body)
        else:
            text_content = body.decode("utf-8", errors="replace")

        return {
            "content": text_content,
            "content_type": content_type,
            "metadata": metadata,
            "key": key,
            "size_bytes": len(body),
        }
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            return {"error": f"Document not found: {key}"}
        raise


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)
    except ImportError:
        return "[PyPDF2 not installed — cannot extract PDF text]"
    except Exception as e:
        return f"[Error extracting PDF text: {e}]"


def _extract_docx_text(docx_bytes: bytes) -> str:
    """Extract text from a Word (.docx) file."""
    try:
        from docx import Document

        doc = Document(io.BytesIO(docx_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except ImportError:
        return "[python-docx not installed — cannot extract Word text]"
    except Exception as e:
        return f"[Error extracting Word text: {e}]"


def update_document(key: str, content: str, content_type: str = None) -> dict[str, Any]:
    """Upload or replace a document in S3.

    Args:
        key: The S3 object key (path) for the document.
        content: The text content to upload.
        content_type: MIME type (auto-detected from extension if not provided).

    Returns:
        Dict with upload confirmation details.
    """
    if content_type is None:
        content_type = _detect_content_type(key)

    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=content.encode("utf-8"),
            ContentType=content_type,
        )
        return {
            "status": "success",
            "key": key,
            "bucket": BUCKET_NAME,
            "content_type": content_type,
            "size_bytes": len(content.encode("utf-8")),
        }
    except ClientError as e:
        return {"status": "error", "error": str(e)}


def list_documents(prefix: str = "") -> dict[str, Any]:
    """List documents in the S3 bucket with optional prefix filter.

    Args:
        prefix: Optional path prefix to filter results.

    Returns:
        Dict with list of document keys and metadata.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        documents = []
        for obj in response.get("Contents", []):
            documents.append({
                "key": obj["Key"],
                "size_bytes": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            })
        return {"documents": documents, "count": len(documents)}
    except ClientError as e:
        return {"error": str(e)}


def _detect_content_type(key: str) -> str:
    """Detect MIME type from file extension."""
    if key.endswith(".txt"):
        return "text/plain"
    elif key.endswith(".pdf"):
        return "application/pdf"
    elif key.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif key.endswith(".json"):
        return "application/json"
    return "application/octet-stream"


# ─── MCP Server Setup ───────────────────────────────────────────────────────

try:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("s3-documents", instructions="MCP server for reading and updating documents in S3 bucket aabg-kiro-demo")

    @mcp.tool()
    def read_s3_document(key: str) -> str:
        """Read a document from the aabg-kiro-demo S3 bucket.

        Supports .txt, .pdf, and .docx files. Returns extracted text content.

        Args:
            key: The S3 object key (e.g., 'documents/contract.pdf')
        """
        result = read_document(key)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def update_s3_document(key: str, content: str, content_type: str = None) -> str:
        """Upload or replace a document in the aabg-kiro-demo S3 bucket.

        Args:
            key: The S3 object key (e.g., 'documents/summary.txt')
            content: The text content to upload
            content_type: Optional MIME type (auto-detected from extension if omitted)
        """
        result = update_document(key, content, content_type)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def list_s3_documents(prefix: str = "") -> str:
        """List documents in the aabg-kiro-demo S3 bucket.

        Args:
            prefix: Optional path prefix to filter (e.g., 'contracts/')
        """
        result = list_documents(prefix)
        return json.dumps(result, indent=2, default=str)

    if __name__ == "__main__":
        mcp.run()

except ImportError:
    logger.warning("MCP package not installed. Install with: pip install mcp")
    if __name__ == "__main__":
        print("Error: MCP package required. Install with: pip install mcp")
