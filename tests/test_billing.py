import pytest
import sqlite3
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import sys
from pathlib import Path

# Add saas-dashboard/backend to path
backend_dir = Path(__file__).resolve().parent.parent / "saas-dashboard" / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import (
    get_user_entitlement,
    verify_solana_usdt_payment,
    ZOE_SOLANA_WALLET,
)

def test_user_entitlement_default_free(tmp_path):
    # Tests that a user with no record defaults to free plan
    db_path = str(tmp_path / "test_billing.db")
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE dev_entitlements (
            user_id TEXT PRIMARY KEY,
            plan TEXT DEFAULT 'free',
            expires_at TEXT,
            updated_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

    with patch("main.get_dev_db", side_effect=lambda: sqlite3.connect(db_path)), \
         patch("main.get_supabase", return_value=None):
        ent = get_user_entitlement("user_free_123")
        assert ent["plan"] == "free"
        assert ent["is_pro"] is False
        assert ent["receiving_wallet"] == ZOE_SOLANA_WALLET

def test_user_entitlement_active_pro(tmp_path):
    # Tests that a user with valid future expiration is marked pro
    db_path = str(tmp_path / "test_billing_pro.db")
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE dev_entitlements (
            user_id TEXT PRIMARY KEY,
            plan TEXT DEFAULT 'free',
            expires_at TEXT,
            updated_at TEXT NOT NULL
        );
    """)
    future_date = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()
    conn.execute(
        "INSERT INTO dev_entitlements (user_id, plan, expires_at, updated_at) VALUES (?, ?, ?, ?)",
        ("user_pro_456", "pro", future_date, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()

    with patch("main.get_dev_db", side_effect=lambda: sqlite3.connect(db_path)), \
         patch("main.get_supabase", return_value=None):
        ent = get_user_entitlement("user_pro_456")
        assert ent["plan"] == "pro"
        assert ent["is_pro"] is True
        assert ent["expires_at"] == future_date

def test_user_entitlement_expired_pro(tmp_path):
    # Tests that an expired pro user reverts to free
    db_path = str(tmp_path / "test_billing_exp.db")
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE dev_entitlements (
            user_id TEXT PRIMARY KEY,
            plan TEXT DEFAULT 'free',
            expires_at TEXT,
            updated_at TEXT NOT NULL
        );
    """)
    past_date = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    conn.execute(
        "INSERT INTO dev_entitlements (user_id, plan, expires_at, updated_at) VALUES (?, ?, ?, ?)",
        ("user_exp_789", "pro", past_date, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()

    with patch("main.get_dev_db", side_effect=lambda: sqlite3.connect(db_path)), \
         patch("main.get_supabase", return_value=None):
        ent = get_user_entitlement("user_exp_789")
        assert ent["plan"] == "free"
        assert ent["is_pro"] is False

def test_verify_solana_usdt_dev_signature():
    async def _run():
        # Dev test bypass signature
        valid, msg = await verify_solana_usdt_payment("dev_test_signature_xyz")
        assert valid is True
        assert "Development" in msg

        # Empty hash
        valid_empty, msg_empty = await verify_solana_usdt_payment("   ")
        assert valid_empty is False
        assert "empty" in msg_empty

        # Invalid short hash
        valid_short, msg_short = await verify_solana_usdt_payment("abc")
        assert valid_short is False
        assert "Invalid" in msg_short

    asyncio.run(_run())

def test_admin_revenue_endpoint(tmp_path):
    from fastapi import HTTPException
    from main import get_admin_revenue

    # 1. Non-super admin should raise 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        get_admin_revenue(current_user={"id": "u1", "role": "project_owner"})
    assert exc_info.value.status_code == 403

    # 2. Super admin gets revenue summary and invoices
    db_path = str(tmp_path / "test_rev.db")
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE dev_invoices (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            amount_usdt REAL NOT NULL DEFAULT 20.0,
            status TEXT DEFAULT 'pending',
            tx_hash TEXT,
            created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE dev_users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE dev_entitlements (
            user_id TEXT PRIMARY KEY,
            plan TEXT DEFAULT 'free',
            expires_at TEXT,
            updated_at TEXT NOT NULL
        );
    """)
    conn.execute("INSERT INTO dev_users (id, email, password_hash, created_at) VALUES ('u_admin', 'buyer@zoe.network', 'hash', '2026-11-16')")
    conn.execute("INSERT INTO dev_invoices (id, user_id, amount_usdt, status, tx_hash, created_at) VALUES ('inv_1', 'u_admin', 20.0, 'paid', '5K7eZ...', '2026-11-16')")
    conn.execute("INSERT INTO dev_invoices (id, user_id, amount_usdt, status, tx_hash, created_at) VALUES ('inv_2', 'u_admin', 20.0, 'pending', NULL, '2026-11-16')")
    conn.execute("INSERT INTO dev_entitlements (user_id, plan, expires_at, updated_at) VALUES ('u_admin', 'pro', '2027-01-01T00:00:00+00:00', '2026-11-16')")
    conn.commit()
    conn.close()

    with patch("main.get_dev_db", side_effect=lambda: sqlite3.connect(db_path)), \
         patch("main.get_supabase_admin", return_value=None):
        res = get_admin_revenue(current_user={"id": "admin_user", "role": "super_admin"})
        assert "summary" in res
        assert "invoices" in res
        assert res["summary"]["total_revenue"] == 20.0
        assert res["summary"]["paid_invoices_count"] == 1
        assert res["summary"]["pending_invoices_count"] == 1
        assert res["summary"]["active_pro_subscribers"] == 1
        assert len(res["invoices"]) == 2
        assert res["invoices"][0]["email"] == "buyer@zoe.network"
