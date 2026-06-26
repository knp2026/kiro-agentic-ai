"""Generate AWS Verification Checklist PDF for AI Banking Assistant."""

from fpdf import FPDF


class ChecklistPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "AI Banking Assistant - AWS Verification Checklist", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, "Recommended Region: us-east-1", ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(230, 240, 255)
        self.cell(0, 9, f"  {title}", ln=True, fill=True)
        self.ln(2)

    def check_item(self, item, detail=""):
        self.set_font("ZapfDingbats", "", 11)
        self.cell(7, 6, "o")  # empty checkbox
        self.set_font("Helvetica", "B", 10)
        self.cell(60, 6, item)
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, detail)
        self.ln(1)

    def code_block(self, text):
        self.set_font("Courier", "", 9)
        self.set_fill_color(245, 245, 245)
        for line in text.strip().split("\n"):
            self.cell(0, 5, f"  {line}", ln=True, fill=True)
        self.ln(3)

    def note(self, text):
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(80, 80, 80)
        self.multi_cell(0, 5, text)
        self.set_text_color(0, 0, 0)
        self.ln(2)


pdf = ChecklistPDF()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

# Section 1: DynamoDB
pdf.section_title("1. DynamoDB - Contracts Table (us-east-1)")
pdf.check_item("Table exists", 'Table named "Contracts" is created in DynamoDB console')
pdf.check_item("Partition key", 'contract_id (String type)')
pdf.check_item("Test item inserted", "Insert sample record with all required fields")
pdf.check_item("Billing mode", "On-demand or provisioned capacity configured")

pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 6, "Sample test item:", ln=True)
pdf.code_block("""{
  "contract_id": "C123",
  "amount": 50000,
  "interest_rate": 0.05,
  "duration": "5 years"
}""")

# Section 2: Bedrock
pdf.section_title("2. Amazon Bedrock - Model Access (us-east-1)")
pdf.check_item("Model access enabled", "anthropic.claude-3-haiku-20240307-v1:0 enabled in Bedrock console")
pdf.check_item("Access requested", "If not enabled: Bedrock > Model access > Manage model access")
pdf.check_item("Invoke permissions", "IAM role/user has bedrock:InvokeModel permission")

pdf.note("Supported regions for Claude 3 Haiku: us-east-1, us-west-2, eu-west-1, ap-northeast-1")

# Section 3: IAM
pdf.section_title("3. IAM Permissions (Global)")
pdf.check_item("DynamoDB access", "dynamodb:GetItem on arn:aws:dynamodb:us-east-1:{account}:table/Contracts")
pdf.check_item("Bedrock access", "bedrock:InvokeModel on the Claude 3 Haiku foundation model ARN")
pdf.check_item("Credentials configured", "aws configure or environment variables set with valid credentials")

pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 6, "Minimal IAM Policy:", ln=True)
pdf.code_block("""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "dynamodb:GetItem",
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/Contracts"
    },
    {
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
    }
  ]
}""")

# Section 4: Local Environment
pdf.section_title("4. Local Environment Setup")
pdf.check_item("AWS credentials valid", "aws sts get-caller-identity returns valid identity")
pdf.check_item("Region configured", "AWS_DEFAULT_REGION=us-east-1 or set in ~/.aws/config")
pdf.check_item("Dependencies installed", "pip install -r requirements.txt completes successfully")
pdf.check_item("App starts", "uvicorn main:app --reload starts without errors on port 8000")

# Section 5: End-to-End Tests
pdf.add_page()
pdf.section_title("5. End-to-End Verification Tests")

pdf.check_item("No contract_id", "Returns prompt message, status AUTO")
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 6, "Command:", ln=True)
pdf.code_block("""curl -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hello"}'""")
pdf.set_font("Helvetica", "", 10)
pdf.cell(0, 5, 'Expected: message contains "provide a contract_id", status = "AUTO"', ln=True)
pdf.ln(3)

pdf.check_item("Valid contract_id", "Returns summary, status AUTO")
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 6, "Command:", ln=True)
pdf.code_block("""curl -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Show my contract", "contract_id": "C123"}'""")
pdf.set_font("Helvetica", "", 10)
pdf.cell(0, 5, 'Expected: contract_summary is populated, status = "AUTO"', ln=True)
pdf.ln(3)

pdf.check_item("Non-existent contract", "Returns escalation message")
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 6, "Command:", ln=True)
pdf.code_block("""curl -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Show contract", "contract_id": "DOESNOTEXIST"}'""")
pdf.set_font("Helvetica", "", 10)
pdf.cell(0, 5, 'Expected: message = "Contract not found, escalating to support", status = "ESCALATE"', ln=True)
pdf.ln(3)

pdf.check_item("Invalid request", "Returns 422 validation error")
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 6, "Command:", ln=True)
pdf.code_block("""curl -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"contract_id": "C123"}'""")
pdf.set_font("Helvetica", "", 10)
pdf.cell(0, 5, "Expected: HTTP 422 with validation error (missing message field)", ln=True)
pdf.ln(5)

# Section 6: Expected Response Codes
pdf.section_title("6. Expected HTTP Response Codes Summary")
pdf.set_font("Courier", "", 9)
rows = [
    ("Scenario", "HTTP Code", "Status Field"),
    ("No contract_id provided", "200", "AUTO"),
    ("Contract found + summary OK", "200", "AUTO"),
    ("Contract not found", "200", "ESCALATE"),
    ("DynamoDB connection error", "502", "ESCALATE"),
    ("Bedrock error/timeout", "200", "ESCALATE"),
    ("Invalid request body", "422", "N/A"),
    ("Unexpected server error", "500", "ESCALATE"),
]
col_widths = [80, 30, 40]
for i, row in enumerate(rows):
    if i == 0:
        pdf.set_font("Helvetica", "B", 10)
    else:
        pdf.set_font("Helvetica", "", 10)
    for j, cell in enumerate(row):
        pdf.cell(col_widths[j], 6, cell, border=1)
    pdf.ln()

pdf.ln(5)
pdf.note("Tip: Use us-east-1 for all services to keep DynamoDB and Bedrock co-located for lowest latency.")

# Save
output_path = "/Users/k.nayak.pradeep/Downloads/Kirodemo/aws_verification_checklist.pdf"
pdf.output(output_path)
print(f"PDF generated: {output_path}")
