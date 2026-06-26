"""Generate Test Guide PDF for AI Banking Assistant."""

from fpdf import FPDF


class TestGuidePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "AI Banking Assistant - Test Execution Guide", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "I", 10)
        self.cell(0, 6, "Prerequisites & Step-by-Step Test Instructions", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(230, 240, 255)
        self.cell(0, 9, f"  {title}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def subsection(self, title):
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def step(self, number, text):
        self.set_font("Helvetica", "B", 10)
        self.cell(12, 6, f"Step {number}:")
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, text)
        self.ln(1)

    def check_item(self, text):
        self.set_font("ZapfDingbats", "", 11)
        self.cell(7, 6, "o")
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, text)
        self.ln(1)

    def code_block(self, text):
        self.set_font("Courier", "", 9)
        self.set_fill_color(245, 245, 245)
        for line in text.strip().split("\n"):
            self.cell(0, 5, f"  {line}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def note_box(self, text):
        self.set_font("Helvetica", "I", 9)
        self.set_fill_color(255, 255, 220)
        self.multi_cell(0, 5, f"NOTE: {text}", fill=True)
        self.set_font("Helvetica", "", 10)
        self.ln(3)

    def expected_result(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_fill_color(220, 255, 220)
        self.multi_cell(0, 5, f"Expected: {text}", fill=True)
        self.ln(2)


pdf = TestGuidePDF()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

# ================================================================
# PART 1: PREREQUISITES
# ================================================================
pdf.section_title("Part 1: Prerequisites (Complete Before Testing)")

pdf.body_text(
    "Complete ALL of the following prerequisites before running any tests. "
    "These steps ensure your environment is properly configured."
)

# 1.1 Software Requirements
pdf.subsection("1.1 Software Requirements")
pdf.check_item("Python 3.9+ installed (verify: python3 --version)")
pdf.check_item("pip package manager available (verify: pip --version)")
pdf.check_item("curl installed for API testing (verify: curl --version)")
pdf.check_item("AWS CLI installed and configured (verify: aws --version)")
pdf.check_item("Git installed (optional, for version control)")

# 1.2 AWS Account Setup
pdf.subsection("1.2 AWS Account & Credentials")
pdf.check_item("Active AWS account with billing enabled")
pdf.check_item("IAM user or role with DynamoDB and Bedrock permissions")
pdf.check_item("AWS credentials configured locally")
pdf.ln(1)
pdf.body_text("Configure credentials:")
pdf.code_block("""aws configure
# Enter:
#   AWS Access Key ID: <your-key>
#   AWS Secret Access Key: <your-secret>
#   Default region: us-east-1
#   Output format: json""")

pdf.body_text("Verify credentials work:")
pdf.code_block("aws sts get-caller-identity")
pdf.expected_result("Returns your Account ID, ARN, and UserId without errors")

# 1.3 DynamoDB Table
pdf.subsection("1.3 Create DynamoDB Contracts Table")
pdf.body_text("Create the table via AWS CLI:")
pdf.code_block("""aws dynamodb create-table \\
  --table-name Contracts \\
  --key-schema AttributeName=contract_id,KeyType=HASH \\
  --attribute-definitions AttributeName=contract_id,AttributeType=S \\
  --billing-mode PAY_PER_REQUEST \\
  --region us-east-1""")

pdf.body_text("Insert test data:")
pdf.code_block("""aws dynamodb put-item \\
  --table-name Contracts \\
  --region us-east-1 \\
  --item '{
    "contract_id": {"S": "C123"},
    "amount": {"N": "50000"},
    "interest_rate": {"N": "0.05"},
    "duration": {"S": "5 years"}
  }'""")

pdf.body_text("Verify the item was inserted:")
pdf.code_block("""aws dynamodb get-item \\
  --table-name Contracts \\
  --region us-east-1 \\
  --key '{"contract_id": {"S": "C123"}}'""")
pdf.expected_result("Returns the full item with contract_id, amount, interest_rate, duration")

# 1.4 Bedrock Model Access
pdf.add_page()
pdf.subsection("1.4 Enable Bedrock Model Access")
pdf.check_item("Go to AWS Console > Amazon Bedrock > Model access")
pdf.check_item("Click 'Manage model access'")
pdf.check_item("Enable: Anthropic > Claude 3 Haiku")
pdf.check_item("Click 'Save changes' and wait for status = 'Access granted'")
pdf.ln(1)
pdf.note_box("Model access can take 1-5 minutes to activate. Verify status shows 'Access granted' before proceeding.")

pdf.body_text("Verify Bedrock access via CLI (optional):")
pdf.code_block("aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[?modelId==`anthropic.claude-3-haiku-20240307-v1:0`].modelId'")
pdf.expected_result('Returns ["anthropic.claude-3-haiku-20240307-v1:0"]')

# 1.5 Install Dependencies
pdf.subsection("1.5 Install Project Dependencies")
pdf.code_block("""cd /Users/k.nayak.pradeep/Downloads/Kirodemo

# Install runtime dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-dev.txt""")

pdf.body_text("Verify installation:")
pdf.code_block("""python -c "import fastapi, boto3, pydantic, uvicorn; print('All dependencies OK')"
python -c "import pytest, hypothesis, httpx, moto; print('Test dependencies OK')" """)
pdf.expected_result("Both commands print 'OK' without import errors")

# 1.6 IAM Permissions
pdf.subsection("1.6 Verify IAM Permissions")
pdf.body_text("Minimum permissions required:")
pdf.code_block("""# DynamoDB
dynamodb:GetItem on arn:aws:dynamodb:us-east-1:*:table/Contracts

# Bedrock
bedrock:InvokeModel on arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0""")

# Prerequisites Checklist Summary
pdf.subsection("Prerequisites Completion Checklist")
pdf.check_item("Python 3.9+ installed")
pdf.check_item("AWS credentials configured (aws sts get-caller-identity works)")
pdf.check_item("DynamoDB 'Contracts' table created in us-east-1")
pdf.check_item("Test record C123 inserted into Contracts table")
pdf.check_item("Bedrock Claude 3 Haiku model access enabled")
pdf.check_item("pip install -r requirements.txt completed")
pdf.check_item("pip install -r requirements-dev.txt completed")

# ================================================================
# PART 2: TEST EXECUTION STEPS
# ================================================================
pdf.add_page()
pdf.section_title("Part 2: Test Execution Steps")

pdf.body_text(
    "Follow these steps in order. Each step builds on the previous one."
)

# Step 1: Unit Tests
pdf.subsection("Step 1: Run Unit Tests (Offline - No AWS Needed)")
pdf.body_text(
    "Unit tests use moto (AWS mock library) and do NOT require real AWS services. "
    "Run these first to verify code correctness."
)
pdf.code_block("""cd /Users/k.nayak.pradeep/Downloads/Kirodemo
pytest -v""")
pdf.expected_result("All 5 tests pass (test_dynamodb_client.py)")
pdf.note_box("If tests fail here, fix code issues before proceeding. No AWS access is needed for this step.")

# Step 2: Start Server
pdf.subsection("Step 2: Start the Application Server")
pdf.code_block("""cd /Users/k.nayak.pradeep/Downloads/Kirodemo
uvicorn main:app --reload --port 8000""")
pdf.expected_result('Console shows "Uvicorn running on http://127.0.0.1:8000"')
pdf.note_box("Keep this terminal open. Open a NEW terminal for the following test commands.")

pdf.body_text("Verify the server is running:")
pdf.code_block("curl -s http://localhost:8000/docs | head -5")
pdf.expected_result("Returns HTML content (FastAPI Swagger docs page)")

# Step 3: Test - No contract_id
pdf.subsection("Step 3: Test - No Contract ID Provided")
pdf.body_text("Simulates a customer who hasn't specified which contract they want.")
pdf.code_block("""curl -s -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hi, I need help"}' | python3 -m json.tool""")
pdf.expected_result('HTTP 200, status="AUTO", message asks user to provide contract_id, contract_summary=null')

# Step 4: Test - Valid contract_id
pdf.add_page()
pdf.subsection("Step 4: Test - Valid Contract ID (Happy Path)")
pdf.body_text("Simulates a customer providing a valid contract ID that exists in DynamoDB.")
pdf.code_block("""curl -s -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Show me my contract details", "contract_id": "C123"}' | python3 -m json.tool""")
pdf.expected_result('HTTP 200, status="AUTO", contract_summary contains AI-generated summary, message contains "C123"')
pdf.note_box("This test requires BOTH DynamoDB and Bedrock to be working. If it fails, check AWS credentials and model access.")

# Step 5: Test - Invalid contract_id (ESCALATE)
pdf.subsection("Step 5: Test - Invalid Contract ID (Human-in-the-Loop Escalation)")
pdf.body_text("Simulates a customer providing a contract ID that does NOT exist. This triggers escalation.")
pdf.code_block("""curl -s -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Check my loan", "contract_id": "DOES_NOT_EXIST"}' | python3 -m json.tool""")
pdf.expected_result('HTTP 200, status="ESCALATE", message="Contract not found, escalating to support", contract_summary=null')

# Step 6: Test - Missing message field
pdf.subsection("Step 6: Test - Missing Required Field (Validation Error)")
pdf.body_text("Simulates a malformed request where the required 'message' field is missing.")
pdf.code_block("""curl -s -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"contract_id": "C123"}' | python3 -m json.tool""")
pdf.expected_result("HTTP 422, validation error indicating 'message' field is required")

# Step 7: Test - Message too long
pdf.subsection("Step 7: Test - Message Exceeds Maximum Length")
pdf.body_text("Simulates a message that exceeds the 1000-character limit.")
pdf.code_block("""curl -s -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d "{\\"message\\": \\"$(python3 -c "print('A' * 1001)")\\"}" | python3 -m json.tool""")
pdf.expected_result("HTTP 422, validation error indicating string too long (max 1000)")

# Step 8: Run automated demo
pdf.add_page()
pdf.subsection("Step 8: Run Automated Demo Script (Both Use Cases)")
pdf.body_text("Runs both the valid and invalid contract_id scenarios automatically and reports results.")
pdf.code_block("""cd /Users/k.nayak.pradeep/Downloads/Kirodemo
python demo_use_cases.py""")
pdf.expected_result("Both use cases pass: Use Case 1 returns AUTO, Use Case 2 returns ESCALATE")

# Step 9: Check logs
pdf.subsection("Step 9: Verify Structured Logging")
pdf.body_text(
    "Check the terminal where uvicorn is running. You should see JSON-formatted log entries for each request:"
)
pdf.code_block("""# Look for entries like:
{"timestamp": "...", "level": "INFO", "message": "Incoming chat request", "contract_id": "C123"}
{"timestamp": "...", "level": "INFO", "message": "Contract retrieved successfully", "contract_id": "C123"}
{"timestamp": "...", "level": "INFO", "message": "Summary generated successfully"}
{"timestamp": "...", "level": "INFO", "message": "Response sent", "status": "AUTO"}""")
pdf.expected_result("All log entries are JSON-formatted with appropriate log levels (INFO, WARNING, ERROR)")

# ================================================================
# TROUBLESHOOTING
# ================================================================
pdf.section_title("Troubleshooting Common Issues")

pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 6, "Problem: Connection refused on localhost:8000", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
pdf.body_text("Solution: Make sure uvicorn is running. Run: uvicorn main:app --reload --port 8000")

pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 6, "Problem: HTTP 502 on valid contract_id", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
pdf.body_text("Solution: DynamoDB connection failed. Check: aws sts get-caller-identity and verify table exists in us-east-1.")

pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 6, "Problem: Summary generation failed (Bedrock error)", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
pdf.body_text("Solution: Verify Bedrock model access is enabled. Go to AWS Console > Bedrock > Model access and check Claude 3 Haiku status.")

pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 6, "Problem: Import errors when starting server", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
pdf.body_text("Solution: Run: pip install -r requirements.txt -r requirements-dev.txt")

pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 6, "Problem: Unit tests fail with moto errors", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
pdf.body_text("Solution: Ensure moto is installed: pip install moto[dynamodb]. Use moto >= 4.0.")

# Save
output_path = "/Users/k.nayak.pradeep/Downloads/Kirodemo/test_execution_guide.pdf"
pdf.output(output_path)
print(f"PDF generated: {output_path}")
