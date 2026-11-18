"""Unit tests for Phase 4: Custom Price Alerts & Wallet Following."""

import asyncio
from pathlib import Path
import sqlite3
from unittest.mock import patch

import pytest

from zoe.db.connections import open_operational_db
from zoe.monitor import check_custom_alerts, check_wallet_follows
from zoe.tools.alerts import (
    add_price_alert,
    add_wallet_follow,
    deactivate_price_alerts,
    deactivate_wallet_follow,
    get_active_price_alerts,
    get_active_wallet_follows,
)


def test_add_and_deactivate_price_alert(tmp_path):
    """Test custom price alert registration and deactivation."""
    db_path = str(tmp_path / "test_alerts.db")

    with patch("zoe.tools.alerts.get_alerts_db_conn", side_effect=lambda: sqlite3.connect(db_path)), \
         patch("zoe.tools.alerts.get_supabase_client", return_value=None):

        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE dev_price_alerts (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                telegram_user_id TEXT NOT NULL,
                contract_address TEXT NOT NULL,
                target_price REAL NOT NULL,
                direction TEXT CHECK (direction IN ('above', 'below')),
                token_name TEXT,
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

        rec = add_price_alert(
            project_id="proj_p4",
            telegram_user_id="user_123",
            contract_address="DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            target_price=200.0,
            direction="above",
            token_name="SOL",
        )
        assert rec is not None
        assert rec["target_price"] == 200.0
        assert rec["direction"] == "above"

        alerts = get_active_price_alerts()
        assert len(alerts) == 1
        assert alerts[0]["token_name"] == "SOL"

        # Deactivate
        deactivated = deactivate_price_alerts("proj_p4", "user_123", "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263")
        assert deactivated == 1

        alerts_after = get_active_price_alerts()
        assert len(alerts_after) == 0


def test_add_and_deactivate_wallet_follow(tmp_path):
    """Test wallet follow creation and deactivation."""
    db_path = str(tmp_path / "test_follows.db")

    with patch("zoe.tools.alerts.get_alerts_db_conn", side_effect=lambda: sqlite3.connect(db_path)), \
         patch("zoe.tools.alerts.get_supabase_client", return_value=None):

        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE dev_wallet_follows (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                telegram_user_id TEXT NOT NULL,
                wallet_address TEXT NOT NULL,
                last_tx_signature TEXT,
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                UNIQUE(project_id, telegram_user_id, wallet_address)
            )
            """
        )
        conn.commit()
        conn.close()

        rec = add_wallet_follow(
            project_id="proj_p4",
            telegram_user_id="user_123",
            wallet_address="4C8deD4Tm8xuM5kkpkS8wn7shGgKejAMLyi6uwFkCkFA",
        )
        assert rec is not None
        assert rec["wallet_address"] == "4C8deD4Tm8xuM5kkpkS8wn7shGgKejAMLyi6uwFkCkFA"

        follows = get_active_wallet_follows()
        assert len(follows) == 1

        deactivate_wallet_follow("proj_p4", "user_123", "4C8deD4Tm8xuM5kkpkS8wn7shGgKejAMLyi6uwFkCkFA")
        follows_after = get_active_wallet_follows()
        assert len(follows_after) == 0


def test_check_custom_alerts_triggers_and_deactivates(tmp_path):
    """Test price target trigger emits outbox message and deactivates."""
    async def _run():
        op_db_path = str(tmp_path / "operational.db")
        alerts_db_path = str(tmp_path / "alerts.db")

        # 1. Operational DB
        conn_op = open_operational_db(op_db_path)
        conn_op.close()

        # 2. Alerts DB with an alert on CA above $100
        conn_a = sqlite3.connect(alerts_db_path)
        conn_a.execute(
            """
            CREATE TABLE dev_price_alerts (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                telegram_user_id TEXT NOT NULL,
                contract_address TEXT NOT NULL,
                target_price REAL NOT NULL,
                direction TEXT CHECK (direction IN ('above', 'below')),
                token_name TEXT,
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        conn_a.execute(
            """
            CREATE TABLE dev_projects (
                id TEXT PRIMARY KEY,
                telegram_group_id TEXT
            )
            """
        )
        conn_a.execute(
            "INSERT INTO dev_projects (id, telegram_group_id) VALUES (?, ?)",
            ("proj_alert_1", "-100777888"),
        )
        conn_a.execute(
            "INSERT INTO dev_price_alerts (id, project_id, telegram_user_id, contract_address, target_price, direction, token_name, active, created_at) VALUES (?, ?, ?, ?, 100.0, 'above', 'SOL', 1, ?)",
            ("alt_1", "proj_alert_1", "trader_dan", "So11111111111111111111111111111111111111112", "2026-11-17T00:00:00Z"),
        )
        conn_a.commit()
        conn_a.close()

        # Mock market data: price is $105.00 (> 100.00 target)
        mock_market = {"found": True, "price_usd": 105.00, "name": "Solana", "symbol": "SOL"}

        with patch("zoe.tools.alerts.get_alerts_db_conn", side_effect=lambda: sqlite3.connect(alerts_db_path)), \
             patch("zoe.tools.alerts.get_supabase_client", return_value=None), \
             patch("zoe.monitor.get_dev_db_conn", side_effect=lambda: sqlite3.connect(alerts_db_path)), \
             patch("zoe.monitor.fetch_dexscreener_market_data", return_value=mock_market):

            triggered = await check_custom_alerts(op_db_path=op_db_path)

            assert len(triggered) == 1
            assert triggered[0]["alert_id"] == "alt_1"
            assert triggered[0]["current_price"] == 105.00
            assert "PRICE ALERT!" in triggered[0]["message"]
            assert "$SOL" in triggered[0]["message"]
            assert "just crossed **above** **$100.0000**" in triggered[0]["message"]

            # Verify persisted in operational.db outbox_messages
            verify_op = open_operational_db(op_db_path)
            cur = verify_op.cursor()
            cur.execute("SELECT id, text, state FROM outbox_messages WHERE project_id = ?", ("proj_alert_1",))
            row_outbox = cur.fetchone()
            assert row_outbox is not None
            assert "PRICE ALERT!" in row_outbox[1]
            assert row_outbox[2] == "pending"
            verify_op.close()

            # Verify alert was marked inactive
            verify_a = sqlite3.connect(alerts_db_path)
            cur_a = verify_a.cursor()
            cur_a.execute("SELECT active FROM dev_price_alerts WHERE id = 'alt_1'")
            assert cur_a.fetchone()[0] == 0
            verify_a.close()

    asyncio.run(_run())


def test_check_wallet_follows_triggers_whale_alert(tmp_path):
    """Test new transaction detection on followed whale wallet emits outbox message."""
    async def _run():
        op_db_path = str(tmp_path / "operational.db")
        alerts_db_path = str(tmp_path / "alerts.db")

        # 1. Operational DB
        conn_op = open_operational_db(op_db_path)
        conn_op.close()

        # 2. Alerts DB with a followed wallet
        conn_a = sqlite3.connect(alerts_db_path)
        conn_a.execute(
            """
            CREATE TABLE dev_wallet_follows (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                telegram_user_id TEXT NOT NULL,
                wallet_address TEXT NOT NULL,
                last_tx_signature TEXT,
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        conn_a.execute("CREATE TABLE dev_projects (id TEXT PRIMARY KEY, telegram_group_id TEXT)")
        conn_a.execute("INSERT INTO dev_projects (id, telegram_group_id) VALUES (?, ?)", ("proj_wf_1", "-100333444"))
        conn_a.execute(
            "INSERT INTO dev_wallet_follows (id, project_id, telegram_user_id, wallet_address, last_tx_signature, active, created_at) VALUES (?, ?, ?, ?, 'old_sig_111', 1, ?)",
            ("wf_1", "proj_wf_1", "dan_user", "4C8deD4Tm8xuM5kkpkS8wn7shGgKejAMLyi6uwFkCkFA", "2026-11-17T00:00:00Z"),
        )
        conn_a.commit()
        conn_a.close()

        # Mock RPC response returning a new signature
        class MockRPCClient:
            async def post(self, url, json=None, timeout=None):
                class MockResp:
                    status_code = 200
                    def json(self):
                        return {"result": [{"signature": "new_whale_sig_99999"}]}
                return MockResp()

        with patch("zoe.tools.alerts.get_alerts_db_conn", side_effect=lambda: sqlite3.connect(alerts_db_path)), \
             patch("zoe.tools.alerts.get_supabase_client", return_value=None), \
             patch("zoe.monitor.get_dev_db_conn", side_effect=lambda: sqlite3.connect(alerts_db_path)):

            triggered = await check_wallet_follows(client=MockRPCClient(), op_db_path=op_db_path)

            assert len(triggered) == 1
            assert triggered[0]["follow_id"] == "wf_1"
            assert triggered[0]["tx_signature"] == "new_whale_sig_99999"
            assert "WHALE ALERT!" in triggered[0]["message"]

            # Verify persisted in operational.db outbox_messages
            verify_op = open_operational_db(op_db_path)
            cur = verify_op.cursor()
            cur.execute("SELECT id, text, state FROM outbox_messages WHERE project_id = ?", ("proj_wf_1",))
            row_out = cur.fetchone()
            assert row_out is not None
            assert "WHALE ALERT!" in row_out[1]
            assert "new_whale_sig_99999" in row_out[1]
            verify_op.close()

            # Verify last_tx_signature was updated
            verify_a = sqlite3.connect(alerts_db_path)
            cur_a = verify_a.cursor()
            cur_a.execute("SELECT last_tx_signature FROM dev_wallet_follows WHERE id = 'wf_1'")
            assert cur_a.fetchone()[0] == "new_whale_sig_99999"
            verify_a.close()

    asyncio.run(_run())
