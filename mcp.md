# MCP Server — S3 Document Operations

This MCP server provides read and update access to documents stored in the `aabg-kiro-demo` S3 bucket. The orchestrator uses these tools to retrieve and modify Word, PDF, and text files.

## Setup

### Install Dependencies

```bash
pip install mcp boto3 python-docx PyPDF2
```

### Configure MCP in Kiro

Add to `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "s3-documents": {
      "command": "python",
      "args": ["mcp_s3_server.py"],
      "env": {
        "AWS_DEFAULT_REGION": "us-east-1"
      },
      "disabled": false,
      "autoApprove": ["read_s3_document", "list_s3_documents"]
    }
  }
}
```

### AWS Credentials

The server uses the default AWS credentials (same ones configured for this project). Ensure your credentials have S3 read/write access to `aabg-kiro-demo`.

Required IAM permissions:
- `s3:GetObject`
- `s3:PutObject`
- `s3:ListBucket`

## Available Tools

### `read_s3_document`

Read and extract text from a document in S3.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `key` | string | Yes | S3 object key (e.g., `documents/contract.pdf`) |

**Supported formats:** `.txt`, `.pdf`, `.docx`

**Example:**
```json
{
  "key": "contracts/C123.pdf"
}
```

**Response:**
```json
{
  "content": "Contract terms and conditions...",
  "content_type": "application/pdf",
  "metadata": {},
  "key": "contracts/C123.pdf",
  "size_bytes": 45320
}
```

---

### `update_s3_document`

Upload or replace a document in S3.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `key` | string | Yes | S3 object key (e.g., `summaries/output.txt`) |
| `content` | string | Yes | Text content to upload |
| `content_type` | string | No | MIME type (auto-detected from extension) |

**Example:**
```json
{
  "key": "summaries/C123_summary.txt",
  "content": "Contract C123: $50,000 loan at 5% for 5 years."
}
```

**Response:**
```json
{
  "status": "success",
  "key": "summaries/C123_summary.txt",
  "bucket": "aabg-kiro-demo",
  "content_type": "text/plain",
  "size_bytes": 52
}
```

---

### `list_s3_documents`

List documents in the bucket, optionally filtered by prefix.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `prefix` | string | No | Path prefix filter (e.g., `contracts/`) |

**Example:**
```json
{
  "prefix": "contracts/"
}
```

**Response:**
```json
{
  "documents": [
    {
      "key": "contracts/C123.pdf",
      "size_bytes": 45320,
      "last_modified": "2026-06-26T10:30:00+00:00"
    }
  ],
  "count": 1
}
```

## Orchestrator Usage

The orchestrator can call these tools via the MCP protocol:

```python
# Read a document
result = await mcp_client.call_tool("read_s3_document", {"key": "contracts/C123.pdf"})

# Update a document
result = await mcp_client.call_tool("update_s3_document", {
    "key": "summaries/C123_summary.txt",
    "content": "Updated summary content here."
})

# List documents
result = await mcp_client.call_tool("list_s3_documents", {"prefix": "contracts/"})
```

## Running Standalone (for testing)

```bash
python mcp_s3_server.py
```

The server starts in stdio mode, ready to accept MCP protocol messages.

## Bucket Details

| Property | Value |
|----------|-------|
| Bucket ARN | `arn:aws:s3:::aabg-kiro-demo` |
| Region | us-east-1 |
| Supported formats | `.txt`, `.pdf`, `.docx` |
