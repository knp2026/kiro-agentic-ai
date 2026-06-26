"""Generate Use Cases PDF for AI Banking Assistant - Human in the Loop."""

from fpdf import FPDF


class UseCasePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "AI Banking Assistant - Use Cases", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, "Human-in-the-Loop Escalation Flow", new_x="LMARGIN", new_y="NEXT", align="C")
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

    def code_block(self, text):
        self.set_font("Courier", "", 9)
        self.set_fill_color(245, 245, 245)
        for line in text.strip().split("\n"):
            self.cell(0, 5, f"  {line}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def flow_step(self, number, text, is_escalation=False):
        self.set_font("Helvetica", "B", 10)
        if is_escalation:
            self.set_text_color(200, 50, 50)
        else:
            self.set_text_color(30, 100, 50)
        self.cell(8, 6, str(number))
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def status_badge(self, status):
        if status == "AUTO":
            self.set_fill_color(200, 240, 200)
            self.set_font("Helvetica", "B", 10)
            self.cell(50, 7, "  STATUS: AUTO", fill=True, new_x="LMARGIN", new_y="NEXT")
        else:
            self.set_fill_color(255, 220, 220)
            self.set_font("Helvetica", "B", 10)
            self.cell(70, 7, "  STATUS: ESCALATE", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)


pdf = UseCasePDF()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

# Introduction
pdf.body_text(
    "This document describes two primary use cases for the AI Banking Assistant, "
    "demonstrating how the system decides whether to handle a request automatically (AUTO) "
    "or escalate it to a human support agent (ESCALATE)."
)

pdf.body_text(
    "The 'status' field in every response drives the human-in-the-loop decision:\n"
    "- AUTO = AI handled the request successfully, no human needed\n"
    "- ESCALATE = AI cannot complete the request, route to human agent"
)

# ================================================================
# USE CASE 1
# ================================================================
pdf.section_title("Use Case 1: Valid Contract ID (Happy Path)")

pdf.subsection("Scenario")
pdf.body_text(
    "A banking customer sends a message asking about their loan contract and provides "
    "a valid contract_id (C123) that exists in the DynamoDB Contracts table."
)

pdf.subsection("Request")
pdf.code_block("""POST /chat
Content-Type: application/json

{
  "message": "Can you show me the details of my loan contract?",
  "contract_id": "C123"
}""")

pdf.subsection("Processing Flow")
pdf.flow_step(1, "Customer sends message with contract_id = 'C123'")
pdf.flow_step(2, "API validates request (message present, under 1000 chars)")
pdf.flow_step(3, "DynamoDB Client queries Contracts table for 'C123'")
pdf.flow_step(4, "Contract FOUND - record returned (amount, interest_rate, duration)")
pdf.flow_step(5, "Bedrock Client generates 3-bullet-point summary of the contract")
pdf.flow_step(6, "API returns response with summary and status AUTO")
pdf.ln(2)

pdf.subsection("Expected Response (HTTP 200)")
pdf.code_block("""{
  "message": "Contract C123 found and summarized successfully.",
  "contract_summary": "- Contract amount: $50,000\\n- Interest rate: 5%\\n- Duration: 5 years",
  "status": "AUTO"
}""")

pdf.status_badge("AUTO")

pdf.subsection("Human-in-the-Loop Decision")
pdf.body_text(
    "NO ESCALATION NEEDED. The AI successfully:\n"
    "1. Found the contract in DynamoDB\n"
    "2. Generated a clear summary via Bedrock LLM\n"
    "3. Returned the result to the customer\n\n"
    "The frontend displays the summary directly to the customer. "
    "No support ticket is created. No human agent is involved."
)

# ================================================================
# USE CASE 2
# ================================================================
pdf.add_page()
pdf.section_title("Use Case 2: Invalid Contract ID (Human-in-the-Loop Escalation)")

pdf.subsection("Scenario")
pdf.body_text(
    "A banking customer sends a message with a contract_id that does NOT exist in the "
    "DynamoDB Contracts table. The AI cannot find the contract, so it escalates "
    "the request to a human support agent who can manually assist."
)

pdf.subsection("Request")
pdf.code_block("""POST /chat
Content-Type: application/json

{
  "message": "Please check my loan status",
  "contract_id": "INVALID_CONTRACT_999"
}""")

pdf.subsection("Processing Flow")
pdf.flow_step(1, "Customer sends message with contract_id = 'INVALID_CONTRACT_999'", is_escalation=True)
pdf.flow_step(2, "API validates request (message present, under 1000 chars)", is_escalation=True)
pdf.flow_step(3, "DynamoDB Client queries Contracts table for 'INVALID_CONTRACT_999'", is_escalation=True)
pdf.flow_step(4, "Contract NOT FOUND - DynamoDB returns None", is_escalation=True)
pdf.flow_step(5, "API triggers escalation - human support needed", is_escalation=True)
pdf.flow_step(6, "API returns response with status ESCALATE", is_escalation=True)
pdf.ln(2)

pdf.subsection("Expected Response (HTTP 200)")
pdf.code_block("""{
  "message": "Contract not found, escalating to support",
  "contract_summary": null,
  "status": "ESCALATE"
}""")

pdf.status_badge("ESCALATE")

pdf.subsection("Human-in-the-Loop Decision")
pdf.body_text(
    "ESCALATION TRIGGERED! The system cannot resolve this request automatically.\n\n"
    "What happens next:\n"
    "1. Frontend detects status = 'ESCALATE'\n"
    "2. System creates a support ticket with the customer's context\n"
    "3. Human agent receives the ticket with:\n"
    "   - Customer message: 'Please check my loan status'\n"
    "   - Attempted contract_id: 'INVALID_CONTRACT_999'\n"
    "4. Human agent investigates:\n"
    "   - Is the contract_id a typo?\n"
    "   - Was the contract closed or transferred?\n"
    "   - Does the customer need help finding their correct contract ID?\n"
    "5. Human agent responds directly to the customer"
)

pdf.subsection("Why Escalation Matters")
pdf.body_text(
    "Without human-in-the-loop, the customer would be stuck. The AI correctly identifies "
    "that it cannot help (contract doesn't exist) and hands off to a human who has access "
    "to additional systems and context to resolve the issue.\n\n"
    "This prevents:\n"
    "- Frustrated customers stuck in an AI loop\n"
    "- Incorrect information being provided\n"
    "- Loss of customer trust when the AI pretends to have answers it doesn't have"
)

# ================================================================
# COMPARISON TABLE
# ================================================================
pdf.add_page()
pdf.section_title("Comparison: AUTO vs ESCALATE")

pdf.set_font("Helvetica", "B", 10)
headers = ["Aspect", "Use Case 1 (Valid)", "Use Case 2 (Invalid)"]
col_widths = [50, 65, 65]
for i, h in enumerate(headers):
    pdf.cell(col_widths[i], 7, h, border=1)
pdf.ln()

rows = [
    ("Contract ID", "C123 (exists)", "INVALID_CONTRACT_999"),
    ("DynamoDB Result", "Record found", "None (not found)"),
    ("Bedrock Called?", "Yes - generates summary", "No - never reached"),
    ("Response Status", "AUTO", "ESCALATE"),
    ("HTTP Code", "200", "200"),
    ("contract_summary", "Populated with summary", "null"),
    ("Human Needed?", "No", "Yes - support agent"),
    ("Customer Experience", "Gets instant answer", "Routed to live support"),
]

pdf.set_font("Helvetica", "", 9)
for row in rows:
    for i, cell in enumerate(row):
        pdf.cell(col_widths[i], 6, cell, border=1)
    pdf.ln()

pdf.ln(5)

# Flow diagram as text
pdf.section_title("Visual Flow Summary")

pdf.subsection("Use Case 1: Valid Contract (AUTO)")
pdf.set_font("Courier", "", 9)
flow1 = [
    "Customer ---> POST /chat (contract_id=C123)",
    "   |",
    "   v",
    "FastAPI ---> DynamoDB (query contract_id=C123)",
    "   |",
    "   v         FOUND! Returns ContractRecord",
    "   |",
    "   v",
    "FastAPI ---> Bedrock LLM (generate summary)",
    "   |",
    "   v         Summary generated successfully",
    "   |",
    "   v",
    "Customer <--- {status: AUTO, contract_summary: '...'}",
    "",
    "Result: Customer sees contract summary. Done.",
]
for line in flow1:
    pdf.cell(0, 5, f"  {line}", new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)

pdf.subsection("Use Case 2: Invalid Contract (ESCALATE)")
pdf.set_font("Courier", "", 9)
flow2 = [
    "Customer ---> POST /chat (contract_id=INVALID_CONTRACT_999)",
    "   |",
    "   v",
    "FastAPI ---> DynamoDB (query contract_id=INVALID_CONTRACT_999)",
    "   |",
    "   v         NOT FOUND! Returns None",
    "   |",
    "   v",
    "FastAPI ---> ESCALATION TRIGGERED",
    "   |",
    "   v",
    "Customer <--- {status: ESCALATE, message: 'Contract not found...'}",
    "   |",
    "   v",
    "Support System ---> Creates ticket ---> Human Agent picks up",
    "   |",
    "   v",
    "Human Agent ---> Contacts customer ---> Resolves issue",
]
for line in flow2:
    pdf.cell(0, 5, f"  {line}", new_x="LMARGIN", new_y="NEXT")

# Testing commands page
pdf.add_page()
pdf.section_title("Quick Test Commands")

pdf.subsection("Start the server:")
pdf.code_block("uvicorn main:app --reload --port 8000")

pdf.subsection("Use Case 1 - Valid Contract:")
pdf.code_block("""curl -s -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Show my contract", "contract_id": "C123"}' | python3 -m json.tool""")

pdf.subsection("Use Case 2 - Invalid Contract:")
pdf.code_block("""curl -s -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Check loan status", "contract_id": "INVALID999"}' | python3 -m json.tool""")

pdf.subsection("Run automated demo script:")
pdf.code_block("python demo_use_cases.py")

# Save
output_path = "/Users/k.nayak.pradeep/Downloads/Kirodemo/use_cases_human_in_the_loop.pdf"
pdf.output(output_path)
print(f"PDF generated: {output_path}")
