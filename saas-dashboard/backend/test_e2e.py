"""Zoe Platform End-to-End System Verification Script (Final Polish).

Tests the full user lifecycle using httpx against FastAPI:
1. User Registration & Authentication (JWT token)
2. Project Management (GET /api/projects)
3. On-Chain Intelligence Scanner (POST /api/investigate with Safety Score)
4. Paper Trading Engine (POST /api/trading/execute & balance deduction)
5. Billing & Invoices (GET /api/billing/history)
"""

import sys
import uuid
from pathlib import Path

# Add project root and backend to PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from main import app


def run_e2e_tests():
    print("=" * 70)
    print("🧪 Zoe SaaS Platform — End-to-End System Verification Suite")
    print("=" * 70)

    results = []
    
    def log_result(test_name: str, passed: bool, detail: str = ""):
        status_tag = "✅ PASS" if passed else "❌ FAIL"
        results.append((test_name, passed, detail))
        print(f"[{status_tag}] {test_name}")
        if detail:
            print(f"        └─ {detail}")

    with TestClient(app) as client:
        # ---------------------------------------------------------
        # STEP 1: User Registration & JWT Authentication
        # ---------------------------------------------------------
        test_email = f"e2e_trader_{uuid.uuid4().hex[:6]}@example.com"
        test_pass = "SecureE2EPass123!"

        try:
            reg_res = client.post(
                "/api/auth/register",
                json={"email": test_email, "password": test_pass},
            )
            if reg_res.status_code == 200:
                data = reg_res.json()
                token = data.get("access_token")
                user = data.get("user") or {}
                if token:
                    log_result("1. User Registration & Auth", True, f"Token received for {test_email}")
                else:
                    log_result("1. User Registration & Auth", False, "No access_token returned")
                    return
            else:
                log_result("1. User Registration & Auth", False, f"HTTP {reg_res.status_code}: {reg_res.text}")
                return
        except Exception as exc:
            log_result("1. User Registration & Auth", False, str(exc))
            return

        headers = {"Authorization": f"Bearer {token}"}

        # ---------------------------------------------------------
        # STEP 2: Project Management (GET /api/projects)
        # ---------------------------------------------------------
        try:
            proj_res = client.get("/api/projects", headers=headers)
            if proj_res.status_code == 200:
                projects = proj_res.json()
                assert isinstance(projects, list)
                log_result("2. Project Management API", True, f"Retrieved {len(projects)} projects for user")
            else:
                log_result("2. Project Management API", False, f"HTTP {proj_res.status_code}: {proj_res.text}")
        except Exception as exc:
            log_result("2. Project Management API", False, str(exc))

        # ---------------------------------------------------------
        # STEP 3: Intelligence Scanner (POST /api/investigate)
        # ---------------------------------------------------------
        solana_ca = "So11111111111111111111111111111111111111112"
        try:
            inv_res = client.post(
                "/api/investigate",
                headers=headers,
                json={"contract_address": solana_ca},
            )
            if inv_res.status_code == 200:
                report = inv_res.json()
                valid = report.get("valid") is True
                score = report.get("safety_score")
                ai_summary = report.get("ai_summary")
                chain = report.get("chain")
                assert valid, "Scan report invalid"
                assert score is not None, "Missing safety score"
                log_result(
                    "3. Intelligence Scanner",
                    True,
                    f"Token: {report.get('name')} | Chain: {chain} | Safety Score: {score}/100",
                )
            else:
                log_result("3. Intelligence Scanner", False, f"HTTP {inv_res.status_code}: {inv_res.text}")
        except Exception as exc:
            log_result("3. Intelligence Scanner", False, str(exc))

        # ---------------------------------------------------------
        # STEP 4: Paper Trading Engine (POST /api/trading/execute)
        # ---------------------------------------------------------
        try:
            # 1. Fetch initial wallet balance
            w_res = client.get("/api/trading/wallet", headers=headers)
            initial_balance = w_res.json().get("balance_usdt", 10000.0)

            # 2. Execute a simulated buy order for $200 USDT of SOL
            buy_payload = {
                "token_address": solana_ca,
                "trade_type": "buy",
                "amount_usdt": 200.0,
                "token_name": "Wrapped SOL",
            }
            trade_res = client.post("/api/trading/execute", headers=headers, json=buy_payload)
            if trade_res.status_code == 200:
                trade_data = trade_res.json()
                new_balance = trade_data.get("balance_usdt")
                expected_balance = round(initial_balance - 200.0, 2)
                assert abs(new_balance - expected_balance) < 0.05, f"Balance mismatch: {new_balance} vs {expected_balance}"
                log_result(
                    "4. Paper Trading Engine",
                    True,
                    f"Executed BUY $200.00 USDT. Balance deducted: ${initial_balance:.2f} -> ${new_balance:.2f} USDT",
                )
            else:
                log_result("4. Paper Trading Engine", False, f"HTTP {trade_res.status_code}: {trade_res.text}")
        except Exception as exc:
            log_result("4. Paper Trading Engine", False, str(exc))

        # ---------------------------------------------------------
        # STEP 5: Billing & Invoices (GET /api/billing/history)
        # ---------------------------------------------------------
        try:
            bill_res = client.get("/api/billing/history", headers=headers)
            if bill_res.status_code == 200:
                invoices = bill_res.json()
                assert isinstance(invoices, list)
                log_result("5. Billing & Invoices API", True, f"Retrieved {len(invoices)} billing receipts")
            else:
                log_result("5. Billing & Invoices API", False, f"HTTP {bill_res.status_code}: {bill_res.text}")
        except Exception as exc:
            log_result("5. Billing & Invoices API", False, str(exc))

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    total_tests = len(results)
    passed_tests = sum(1 for _, p, _ in results if p)
    failed_tests = total_tests - passed_tests

    if failed_tests == 0:
        print(f"🎉 ALL {total_tests}/{total_tests} END-TO-END VERIFICATION TESTS PASSED (100% GREEN)!")
    else:
        print(f"⚠️ {failed_tests}/{total_tests} TESTS FAILED. REVIEW DETAILS ABOVE.")
    print("=" * 70 + "\n")

    if failed_tests > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_e2e_tests()
