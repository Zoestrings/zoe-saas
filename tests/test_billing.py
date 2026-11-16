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
