"""
AI Banking Assistant - Demo Use Cases
=====================================
Runs two scenarios against the live /chat endpoint:
  Use Case 1: Valid contract_id → AI handles automatically (AUTO)
  Use Case 2: Invalid contract_id → Escalates to human support (ESCALATE)

Prerequisites:
  1. Server running: uvicorn main:app --port 8000
  2. DynamoDB "Contracts" table exists with test record (contract_id: "C123")
  3. Bedrock model access enabled for Claude 3 Haiku

Usage:
  python demo_use_cases.py
"""

import httpx
import json
import sys

BASE_URL = "http://localhost:8000"
DIVIDER = "=" * 70


def print_header(title: str):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def print_request(payload: dict):
    print("\n📤 REQUEST:")
    print(f"   POST {BASE_URL}/chat")
    print(f"   Body: {json.dumps(payload, indent=2)}")


def print_response(response: httpx.Response):
    status_icon = "✅" if response.status_code == 200 else "⚠️"
    print(f"\n📥 RESPONSE ({status_icon} HTTP {response.status_code}):")
    try:
        body = response.json()
        print(f"   {json.dumps(body, indent=2)}")
    except Exception:
        print(f"   {response.text}")


def print_human_loop_action(status: str, context: str):
    print(f"\n🔄 HUMAN-IN-THE-LOOP ACTION:")
    if status == "AUTO":
        print("   ➡️  No escalation needed.")
        print(f"   ➡️  {context}")
    elif status == "ESCALATE":
        print("   🚨 ESCALATION TRIGGERED!")
        print(f"   ➡️  {context}")
        print("   ➡️  System creates a support ticket and routes to human agent.")
        print("   ➡️  Human agent sees the customer's message and contract_id.")


def use_case_1_valid_contract():
    """Use Case 1: Valid contract_id — AI handles the request automatically."""
    print_header("USE CASE 1: Valid Contract ID (Happy Path)")
    print("\n📋 SCENARIO:")
    print("   A banking customer asks about their contract using a valid contract_id.")
    print("   The system retrieves the contract from DynamoDB, generates a summary")
    print("   via Bedrock AI, and returns the result — no human intervention needed.")

    payload = {
        "message": "Can you show me the details of my loan contract?",
        "contract_id": "C123"
    }

    print_request(payload)

    try:
        response = httpx.post(f"{BASE_URL}/chat", json=payload, timeout=60)
        print_response(response)

        body = response.json()
        status = body.get("status", "")

        print_human_loop_action(status, "AI successfully summarized the contract. Display response to customer.")

        print("\n📊 FLOW:")
        print("   Customer → API → DynamoDB (found) → Bedrock (summary) → Customer")
        print("   Status: AUTO (fully automated, no human needed)")

        return response.status_code == 200 and status == "AUTO"

    except httpx.ConnectError:
        print("\n❌ ERROR: Cannot connect to server. Is uvicorn running on port 8000?")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def use_case_2_invalid_contract():
    """Use Case 2: Invalid contract_id — Escalates to human support."""
    print_header("USE CASE 2: Invalid Contract ID (Human-in-the-Loop Escalation)")
    print("\n📋 SCENARIO:")
    print("   A banking customer provides a contract_id that doesn't exist in the system.")
    print("   The AI cannot find the contract, so it escalates to a human support agent.")
    print("   The human agent can then manually assist the customer.")

    payload = {
        "message": "Please check my loan status",
        "contract_id": "INVALID_CONTRACT_999"
    }

    print_request(payload)

    try:
        response = httpx.post(f"{BASE_URL}/chat", json=payload, timeout=60)
        print_response(response)

        body = response.json()
        status = body.get("status", "")

        print_human_loop_action(
            status,
            "Contract not found. Customer needs help from a human agent to locate their contract."
        )

        print("\n📊 FLOW:")
        print("   Customer → API → DynamoDB (NOT found) → ESCALATE → Human Agent")
        print("   Status: ESCALATE (AI cannot resolve, human takes over)")
        print("\n👤 HUMAN AGENT RECEIVES:")
        print(f'   • Customer message: "{payload["message"]}"')
        print(f'   • Attempted contract_id: "{payload["contract_id"]}"')
        print("   • Action: Help customer find correct contract_id or investigate")

        return response.status_code == 200 and status == "ESCALATE"

    except httpx.ConnectError:
        print("\n❌ ERROR: Cannot connect to server. Is uvicorn running on port 8000?")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def main():
    print(DIVIDER)
    print("  AI BANKING ASSISTANT — HUMAN-IN-THE-LOOP DEMO")
    print("  Two Use Cases: Valid vs Invalid Contract ID")
    print(DIVIDER)

    results = []

    # Run Use Case 1
    passed = use_case_1_valid_contract()
    results.append(("Use Case 1: Valid Contract ID", passed))

    # Run Use Case 2
    passed = use_case_2_invalid_contract()
    results.append(("Use Case 2: Invalid Contract ID", passed))

    # Summary
    print_header("RESULTS SUMMARY")
    all_passed = True
    for name, passed in results:
        icon = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {icon} — {name}")
        if not passed:
            all_passed = False

    print(f"\n{'✅ All use cases passed!' if all_passed else '⚠️  Some use cases failed. Check server and AWS configuration.'}")
    print()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
