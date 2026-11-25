"""Phase J Automated Tests: Unified Subscription, Billing, Reservations, & Replay Protection."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import sys

import pytest
from starlette.testclient import TestClient

backend_path = Path(__file__).resolve().parent.parent / "saas-dashboard" / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import main as backend_main
from zoe.billing.credit_manager import CreditManager, EntitlementEngine


def test_concurrent_credit_reservations_cannot_overspend(tmp_path: Path):
    """5 concurrent users/threads reserving 15 credits on a 30-credit wallet: only 2 succeed."""
    db_file = tmp_path / "billing_race.db"
    conn = sqlite3.connect(str(db_file), timeout=10.0, isolation_level=None)
    EntitlementEngine.ensure_unified_schema(conn)
    conn.execute(
        "INSERT INTO dev_entitlements (user_id, plan, credits, updated_at) VALUES ('race_user', 'free', 30, '2026-11-25T00:00:00Z')"
    )
    conn.close()

    def _reserve(idx: int):
        c = sqlite3.connect(str(db_file), timeout=20.0, isolation_level=None)
        ok, _, rsv_id = EntitlementEngine.reserve_credits("race_user", 15, "token_scan", db_conn=c)
        c.close()
        return ok, rsv_id

    with ThreadPoolExecutor(max_workers=5) as ex:
        results = list(ex.map(_reserve, range(5)))

    successes = [r for r in results if r[0]]
    assert len(successes) == 2

    # Settle 1st and release 2nd -> balance becomes 15
    c_final = sqlite3.connect(str(db_file), timeout=10.0, isolation_level=None)
    ok_settle, _, bal_after = EntitlementEngine.settle_credits(successes[0][1], 15, db_conn=c_final)
    assert ok_settle is True
    assert bal_after == 15
    ok_rel, _ = EntitlementEngine.release_reservation(successes[1][1], db_conn=c_final)
    assert ok_rel is True
    c_final.close()


def test_duplicate_payment_tx_hash_rejected(tmp_path: Path):
    """Duplicate tx_hash replay must NOT grant credits twice."""
    db_file = tmp_path / "pay_dup.db"
    conn = sqlite3.connect(str(db_file), timeout=10.0, isolation_level=None)
    EntitlementEngine.ensure_unified_schema(conn)

    ok1, _, bal1 = EntitlementEngine.record_verified_payment("u_pay", "inv_1", "tx_solana_abc123", 5.0, 500, db_conn=conn)
    assert ok1 is True
    assert bal1 == 550  # 50 + 500

    ok2, msg2, _ = EntitlementEngine.record_verified_payment("u_pay", "inv_2", "tx_solana_abc123", 5.0, 500, db_conn=conn)
    assert ok2 is False
    assert "Duplicate" in msg2
    conn.close()


def test_billing_tenant_isolation_and_admin_rbac(tmp_path: Path, monkeypatch):
    """Tenant A cannot read Tenant B's billing usage; Project Owner cannot access Admin billing controls."""
    db_file = tmp_path / "saas_dev.db"
    monkeypatch.setattr(backend_main, "DEV_DB_PATH", db_file)
    monkeypatch.setattr(backend_main, "get_supabase", lambda: None)
    conn = backend_main.get_dev_db()
    EntitlementEngine.ensure_unified_schema(conn)

    CreditManager.deduct_credits("tenant_a", 10, "token_scan", db_conn=conn)
    CreditManager.deduct_credits("tenant_b", 20, "contract_audit", db_conn=conn)

    backend_main.app.dependency_overrides[backend_main.get_current_user] = lambda: {
        "id": "tenant_a",
        "email": "a@zoe.ai",
        "role": "project_owner",
    }
    client = TestClient(backend_main.app)

    # Tenant A only sees tenant_a usage
    u_resp = client.get("/api/billing/usage")
    assert u_resp.status_code == 200
    actions = [x["action_type"] for x in u_resp.json()]
    assert "token_scan" in actions
    assert "contract_audit" not in actions

    # Project Owner blocked from Admin billing overview & adjust-credits
    assert client.get("/api/admin/billing/overview").status_code == 403
    assert client.post("/api/admin/billing/adjust-credits", json={"target_user_id": "tenant_a", "amount": 999, "reason": "hack"}).status_code == 403

    backend_main.app.dependency_overrides.clear()
