"""P0 Automated Test Suite: Credit System Integrity & Concurrency Verification.

Tests all 12 required conditions:
1. Normal successful deduction.
2. Insufficient balance.
3. Zero balance.
4. Negative or invalid deduction amounts.
5. Concurrent deduction attempts (multi-threaded race condition proof).
6. Duplicate requests (idempotency key protection).
7. Database failure during deduction (fail-closed behavior).
8. Failure after deduction but before feature completion.
9. Refund after failed operation.
10. Duplicate refund attempt (must fail / prevent double refund).
11. Subscription credit allocation.
12. Administrative adjustment authorization (RBAC enforcement).
"""

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import sqlite3
import pytest

from zoe.billing.credit_manager import CreditManager


@pytest.fixture
def test_db(tmp_path: Path):
    """Set up an isolated in-memory or temporary SQLite database for credit testing."""
    db_file = tmp_path / "test_credits.db"
    conn = sqlite3.connect(str(db_file), timeout=10.0, isolation_level=None)
    CreditManager.ensure_schema(conn)
    yield conn, db_file
    conn.close()


def test_1_normal_successful_deduction(test_db):
    """1. Normal successful deduction: 50 initial credits, deduct 15 -> balance 35."""
    conn, _ = test_db
    user_id = "user_normal_01"

    # Initial balance check
    bal, plan = CreditManager.get_balance(user_id, db_conn=conn)
    assert bal == 50
    assert plan == "free"

    # Deduct 15 credits
    success, msg, remaining, tx_id = CreditManager.deduct_credits(
        user_id=user_id,
        amount=15,
        action_type="token_scan",
        db_conn=conn,
    )
    assert success is True
    assert remaining == 35
    assert tx_id is not None
    assert "Deducted 15 credits" in msg

    # Verify persisted balance
    persisted_bal, _ = CreditManager.get_balance(user_id, db_conn=conn)
    assert persisted_bal == 35


def test_2_insufficient_balance(test_db):
    """2. Insufficient balance: user has 10 credits, requests action costing 15 -> blocked."""
    conn, _ = test_db
    user_id = "user_insufficient_01"

    # Set user balance to 10
    conn.execute(
        "INSERT INTO dev_entitlements (user_id, plan, credits, updated_at) VALUES (?, 'free', 10, '2026-11-25T00:00:00Z')",
        (user_id,),
    )

    success, msg, remaining, tx_id = CreditManager.deduct_credits(
        user_id=user_id,
        amount=15,
        action_type="token_scan",
        db_conn=conn,
    )
    assert success is False
    assert remaining == 10
    assert tx_id is None
    assert "Insufficient credits" in msg

    # Balance must remain unchanged
    bal, _ = CreditManager.get_balance(user_id, db_conn=conn)
    assert bal == 10


def test_3_zero_balance(test_db):
    """3. Zero balance: user has 0 credits, attempts deduction -> blocked."""
    conn, _ = test_db
    user_id = "user_zero_01"

    conn.execute(
        "INSERT INTO dev_entitlements (user_id, plan, credits, updated_at) VALUES (?, 'free', 0, '2026-11-25T00:00:00Z')",
        (user_id,),
    )

    success, msg, remaining, tx_id = CreditManager.deduct_credits(
        user_id=user_id,
        amount=5,
        action_type="web_search",
        db_conn=conn,
    )
    assert success is False
    assert remaining == 0
    assert tx_id is None
    assert "Insufficient credits" in msg


def test_4_negative_or_invalid_deduction_amounts(test_db):
    """4. Negative or invalid amounts must be rejected immediately."""
    conn, _ = test_db
    user_id = "user_invalid_amt_01"

    success, msg, remaining, tx_id = CreditManager.deduct_credits(
        user_id=user_id,
        amount=-20,
        action_type="exploit_attempt",
        db_conn=conn,
    )
    assert success is False
    assert tx_id is None
    assert "cannot be negative" in msg

    # Empty user id must be rejected
    success_empty, _, _, _ = CreditManager.deduct_credits(
        user_id="",
        amount=5,
        action_type="test",
        db_conn=conn,
    )
    assert success_empty is False


def test_5_concurrent_deduction_attempts(tmp_path: Path):
    """5. Concurrent deduction: 10 threads attempt to deduct 10 credits from a 30-credit balance.
    Exactly 3 threads must succeed, 7 must fail, and final balance must be exactly 0.
    """
    db_file = tmp_path / "concurrent_test.db"
    conn_init = sqlite3.connect(str(db_file), timeout=10.0, isolation_level=None)
    CreditManager.ensure_schema(conn_init)

    user_id = "user_race_condition_target"
    conn_init.execute(
        "INSERT INTO dev_entitlements (user_id, plan, credits, updated_at) VALUES (?, 'free', 30, '2026-11-25T00:00:00Z')",
        (user_id,),
    )
    conn_init.close()

    def attempt_deduction(thread_idx: int):
        # Each thread opens its own connection to simulate independent web workers
        thread_conn = sqlite3.connect(str(db_file), timeout=20.0, isolation_level=None)
        res = CreditManager.deduct_credits(
            user_id=user_id,
            amount=10,
            action_type="market_scan",
            db_conn=thread_conn,
        )
        thread_conn.close()
        return res[0]  # boolean success

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(attempt_deduction, range(10)))

    successes = sum(1 for r in results if r is True)
    failures = sum(1 for r in results if r is False)

    # Exactly 3 must succeed (3 * 10 = 30 credits spent)
    assert successes == 3, f"Expected exactly 3 successful deductions, got {successes}"
    assert failures == 7, f"Expected exactly 7 rejected deductions, got {failures}"

    # Final balance check
    conn_check = sqlite3.connect(str(db_file), timeout=10.0)
    bal, _ = CreditManager.get_balance(user_id, db_conn=conn_check)
    assert bal == 0, f"Expected final balance 0, got {bal}"
    conn_check.close()


def test_6_duplicate_requests_idempotency(test_db):
    """6. Duplicate requests with same idempotency key must not charge twice."""
    conn, _ = test_db
    user_id = "user_idempotent_01"
    idempotency_key = "idemp_req_abc123"

    # First request
    ok1, msg1, bal1, tx1 = CreditManager.deduct_credits(
        user_id=user_id,
        amount=10,
        action_type="contract_audit",
        idempotency_key=idempotency_key,
        db_conn=conn,
    )
    assert ok1 is True
    assert bal1 == 40  # 50 - 10
    assert tx1 is not None

    # Duplicate request with same idempotency key
    ok2, msg2, bal2, tx2 = CreditManager.deduct_credits(
        user_id=user_id,
        amount=10,
        action_type="contract_audit",
        idempotency_key=idempotency_key,
        db_conn=conn,
    )
    assert ok2 is True
    assert bal2 == 40  # Must not deduct again!
    assert tx2 == tx1
    assert "Idempotent replay" in msg2

    # Verify audit transactions only contains 1 record for this key
    cur = conn.execute("SELECT COUNT(*) FROM dev_credit_transactions WHERE idempotency_key = ?", (idempotency_key,))
    assert cur.fetchone()[0] == 1


def test_7_database_failure_during_deduction():
    """7. Database failure during deduction must fail closed (never grant free credits)."""
    # Pass a closed or broken connection
    broken_conn = sqlite3.connect(":memory:")
    broken_conn.close()

    success, msg, bal, tx_id = CreditManager.deduct_credits(
        user_id="user_broken_db",
        amount=10,
        action_type="deep_scan",
        db_conn=broken_conn,
    )
    assert success is False
    assert bal == 0
    assert tx_id is None
    assert "Billing Service Unavailable" in msg


def test_8_and_9_refund_after_failed_operation(test_db):
    """8 & 9. Feature fails after deduction -> refund restores balance and records audit trail."""
    conn, _ = test_db
    user_id = "user_refund_test_01"

    # Step 1: Initial deduction
    ok, _, bal_after_deduct, tx_id = CreditManager.deduct_credits(
        user_id=user_id,
        amount=20,
        action_type="agent_orchestrate",
        db_conn=conn,
    )
    assert ok is True
    assert bal_after_deduct == 30  # 50 - 20

    # Step 2: Simulated downstream tool failure triggers refund
    ref_ok, ref_msg, new_bal = CreditManager.refund_credits(
        user_id=user_id,
        transaction_id=tx_id,
        reason="Downstream agent timeout during synthesis",
        db_conn=conn,
    )
    assert ref_ok is True
    assert new_bal == 50  # Restored to 50
    assert "Successfully refunded 20 credits" in ref_msg

    # Verify balance in database
    bal, _ = CreditManager.get_balance(user_id, db_conn=conn)
    assert bal == 50


def test_10_duplicate_refund_attempt(test_db):
    """10. Duplicate refund attempt for same transaction must fail."""
    conn, _ = test_db
    user_id = "user_dup_refund_01"

    # Deduct
    _, _, _, tx_id = CreditManager.deduct_credits(
        user_id=user_id,
        amount=15,
        action_type="token_scan",
        db_conn=conn,
    )

    # First refund succeeds
    ok1, _, bal1 = CreditManager.refund_credits(
        user_id=user_id,
        transaction_id=tx_id,
        reason="First refund attempt",
        db_conn=conn,
    )
    assert ok1 is True
    assert bal1 == 50

    # Second refund for same transaction MUST fail
    ok2, msg2, bal2 = CreditManager.refund_credits(
        user_id=user_id,
        transaction_id=tx_id,
        reason="Malicious or duplicate refund attempt",
        db_conn=conn,
    )
    assert ok2 is False
    assert "already been refunded" in msg2

    # Balance must not be inflated
    bal, _ = CreditManager.get_balance(user_id, db_conn=conn)
    assert bal == 50


def test_11_subscription_credit_allocation(test_db):
    """11. Pro plan users bypass deductions for basic queries, but must pay for heavy operations."""
    conn, _ = test_db
    user_id = "user_pro_subscriber"

    # Enroll user in pro plan
    conn.execute(
        "INSERT INTO dev_entitlements (user_id, plan, credits, updated_at) VALUES (?, 'pro', 100, '2026-11-25T00:00:00Z')",
        (user_id,),
    )

    # Basic query: Pro user cost should be 0 credits deducted
    ok_basic, msg_basic, bal_basic, _ = CreditManager.deduct_credits(
        user_id=user_id,
        amount=5,
        action_type="web_search",
        db_conn=conn,
    )
    assert ok_basic is True
    assert bal_basic == 100  # 0 deducted

    # Heavy query: Pro user must pay
    ok_heavy, _, bal_heavy, _ = CreditManager.deduct_credits(
        user_id=user_id,
        amount=50,
        action_type="contract_audit",
        db_conn=conn,
    )
    assert ok_heavy is True
    assert bal_heavy == 50  # 100 - 50


def test_12_administrative_adjustment_authorization(test_db):
    """12. Administrative adjustments require super_admin authorization."""
    conn, _ = test_db
    target_user = "user_target_adjust"

    # Ordinary user attempts administrative adjustment -> Rejected
    ok_unauth, msg_unauth, _ = CreditManager.admin_adjust_credits(
        admin_user_id="ordinary_user_42",
        target_user_id=target_user,
        amount=500,
        reason="Unauthorized bonus",
        is_super_admin=False,
        db_conn=conn,
    )
    assert ok_unauth is False
    assert "Unauthorized" in msg_unauth

    # Super admin adjustment -> Authorized
    ok_auth, msg_auth, new_bal = CreditManager.admin_adjust_credits(
        admin_user_id="super_admin_01",
        target_user_id=target_user,
        amount=500,
        reason="VIP customer grant",
        is_super_admin=True,
        db_conn=conn,
    )
    assert ok_auth is True
    assert new_bal == 550  # 50 default + 500
    assert "Adjusted credits by +500" in msg_auth
