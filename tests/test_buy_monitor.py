"""Unit tests for Phase 2: Buy Monitoring & Telegram Alerts (Green Candle Feature)."""

import asyncio
from pathlib import Path
import sqlite3
from unittest.mock import AsyncMock, patch

import pytest

from zoe.db.connections import open_operational_db
from zoe.monitor import (
    check_recent_buys,
    enqueue_proactive_alert,
    fetch_token_recent_buys,
    format_buy_alert_message,
)


def test_format_buy_alert_message():
    """Verify that Green Candle messages adhere to required PRD format."""
    msg = format_buy_alert_message(
        token_name="One Love",
        amount_usd=150.00,
        token_amount=1000.5,
        tx_hash="5K6u7v8w9xYzAbCdEfGhIjKlMnOpQrStUvWxYz1234567890",
    )
    assert "🟢 **BUY ALERT!** Someone just bought **$150.00** worth of $One Love! Green candles only! 🚀" in msg
    assert "🪙 **Amount:** 1,000.50 One Love" in msg
    assert "solscan.io/tx/5K6u7v8w9xYzAbCdEfGhIjKlMnOpQrStUvWxYz1234567890" in msg


def test_enqueue_proactive_alert_success(tmp_path):
    """Verify that proactive alerts are correctly inserted into outbox_messages and inbox_messages."""
    op_db_path = str(tmp_path / "operational.db")
    # Initialize operational database with full transactional schema
    conn = open_operational_db(op_db_path)
    conn.close()

    outbox_id = enqueue_proactive_alert(
        project_id="proj_onelove_demo",
        group_id="-100987654321",
        text="🟢 **BUY ALERT!** Someone just bought **$500.00** worth of $One Love! Green candles only! 🚀",
        op_db_path=op_db_path,
        simulated=False,
    )

    assert outbox_id is not None
    assert outbox_id > 0

    # Query operational database to verify persistence
    verify_conn = open_operational_db(op_db_path)
    cur = verify_conn.cursor()
    cur.execute(
        "SELECT id, project_id, group_id, text, state, simulated FROM outbox_messages WHERE id = ?",
        (outbox_id,),
    )
    row = cur.fetchone()
    assert row is not None
    assert row[1] == "proj_onelove_demo"
    assert row[2] == "-100987654321"
    assert "BUY ALERT!" in row[3]
    assert row[4] == "pending"

    # Verify matching inbox_messages record
    cur.execute(
        "SELECT id, project_id, state, decision, decision_reason FROM inbox_messages WHERE project_id = ?",
        ("proj_onelove_demo",),
    )
    inbox_row = cur.fetchone()
    assert inbox_row is not None
    assert inbox_row[2] == "response_pending"
    assert inbox_row[3] == "respond"
    assert inbox_row[4] == "proactive_buy_alert"
    verify_conn.close()


def test_check_recent_buys_triggers_outbox(tmp_path):
    """Mock DexScreener/RPC buy transaction and verify end-to-end outbox enqueueing."""
    async def _run():
        op_db_path = str(tmp_path / "operational.db")
        dev_db_path = str(tmp_path / "dev_db.sqlite")

        # 1. Initialize operational.db
        conn_op = open_operational_db(op_db_path)
        conn_op.close()

        # 2. Initialize dev_db.sqlite with a project and an active buy monitor
        conn_dev = sqlite3.connect(dev_db_path)
        conn_dev.execute(
            """
            CREATE TABLE dev_projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                token_address TEXT,
                telegram_group_id TEXT
            )
            """
        )
        conn_dev.execute(
            """
            CREATE TABLE dev_buy_monitors (
                project_id TEXT PRIMARY KEY,
                min_buy_usd REAL DEFAULT 10.0,
                active INTEGER DEFAULT 1,
                last_tx_signature TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn_dev.execute(
            "INSERT INTO dev_projects (id, name, token_address, telegram_group_id) VALUES (?, ?, ?, ?)",
            ("proj_ol_1", "One Love Project", "987SolanaOneLoveTokenCA1234567890AbCdEfGh", "-100888777"),
        )
        conn_dev.execute(
            "INSERT INTO dev_buy_monitors (project_id, min_buy_usd, active, last_tx_signature, updated_at) VALUES (?, ?, 1, NULL, ?)",
            ("proj_ol_1", 20.0, "2026-11-17T00:00:00Z"),
        )
        conn_dev.commit()
        conn_dev.close()

        # Mock mock buys returned from fetch_token_recent_buys
        mock_buys = [
            {
                "tx_hash": "mock_tx_buy_99999",
                "amount_usd": 125.50,
                "token_amount": 2500.0,
                "token_name": "One Love",
            }
        ]

        with patch("zoe.monitor.get_dev_db_conn", side_effect=lambda: sqlite3.connect(dev_db_path)), \
             patch("zoe.monitor.get_supabase_client", return_value=None), \
             patch("zoe.monitor.fetch_token_recent_buys", return_value=(mock_buys, "mock_tx_buy_99999")):

            alerts = await check_recent_buys(op_db_path=op_db_path)

            assert len(alerts) == 1
            assert alerts[0]["project_id"] == "proj_ol_1"
            assert alerts[0]["amount_usd"] == 125.50
            assert "🟢 **BUY ALERT!** Someone just bought **$125.50** worth of $One Love! Green candles only! 🚀" in alerts[0]["message"]

            # Assert outbox_messages was populated in operational.db
            verify_conn = open_operational_db(op_db_path)
            cur = verify_conn.cursor()
            cur.execute("SELECT id, text, state FROM outbox_messages WHERE project_id = ?", ("proj_ol_1",))
            row = cur.fetchone()
            assert row is not None
            assert "BUY ALERT!" in row[1]
            assert row[2] == "pending"

            # Assert dev_buy_monitors updated last_tx_signature to prevent duplicate alerts
            dev_verify = sqlite3.connect(dev_db_path)
            cur_dev = dev_verify.cursor()
            cur_dev.execute("SELECT last_tx_signature FROM dev_buy_monitors WHERE project_id = ?", ("proj_ol_1",))
            last_sig_row = cur_dev.fetchone()
            assert last_sig_row is not None
            assert last_sig_row[0] == "mock_tx_buy_99999"

            verify_conn.close()
            dev_verify.close()

    asyncio.run(_run())


def test_check_recent_buys_ignores_below_threshold(tmp_path):
    """Verify that buys smaller than min_buy_usd are filtered out."""
    async def _run():
        op_db_path = str(tmp_path / "operational.db")
        dev_db_path = str(tmp_path / "dev_db.sqlite")

        conn_op = open_operational_db(op_db_path)
        conn_op.close()

        conn_dev = sqlite3.connect(dev_db_path)
        conn_dev.execute("CREATE TABLE dev_projects (id TEXT PRIMARY KEY, name TEXT, token_address TEXT, telegram_group_id TEXT)")
        conn_dev.execute("CREATE TABLE dev_buy_monitors (project_id TEXT PRIMARY KEY, min_buy_usd REAL, active INTEGER, last_tx_signature TEXT, updated_at TEXT)")
        conn_dev.execute(
            "INSERT INTO dev_projects (id, name, token_address, telegram_group_id) VALUES (?, ?, ?, ?)",
            ("proj_ol_2", "One Love", "TokenCA123456", "-100111222"),
        )
        # min_buy_usd is $50.00
        conn_dev.execute(
            "INSERT INTO dev_buy_monitors (project_id, min_buy_usd, active, last_tx_signature, updated_at) VALUES (?, ?, 1, NULL, ?)",
            ("proj_ol_2", 50.0, "2026-11-17T00:00:00Z"),
        )
        conn_dev.commit()
        conn_dev.close()

        # Buy is only $5.00 (below $50.00 threshold)
        small_buys = [
            {"tx_hash": "tx_small", "amount_usd": 5.0, "token_amount": 10.0, "token_name": "One Love"}
        ]

        with patch("zoe.monitor.get_dev_db_conn", side_effect=lambda: sqlite3.connect(dev_db_path)), \
             patch("zoe.monitor.get_supabase_client", return_value=None), \
             patch("zoe.monitor.fetch_token_recent_buys", return_value=(small_buys, "tx_small")):

            alerts = await check_recent_buys(op_db_path=op_db_path)
            assert len(alerts) == 0

            verify_conn = open_operational_db(op_db_path)
            cur = verify_conn.cursor()
            cur.execute("SELECT COUNT(*) FROM outbox_messages WHERE project_id = ?", ("proj_ol_2",))
            assert cur.fetchone()[0] == 0
            verify_conn.close()

    asyncio.run(_run())

