import pytest
import sqlite3
import asyncio
from unittest.mock import patch
from zoe.monitor import check_watchlist_tokens

def test_check_watchlist_tokens_alert_trigger(tmp_path):
    async def _run():
        db_path = str(tmp_path / "test_monitor.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE dev_watchlists (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                contract_address TEXT NOT NULL,
                token_name TEXT,
                initial_liquidity REAL,
                initial_price REAL,
                current_liquidity REAL,
                current_price REAL,
                last_checked_at TEXT,
                created_at TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE dev_alerts (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                contract_address TEXT NOT NULL,
                token_name TEXT,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                old_value REAL,
                new_value REAL,
                created_at TEXT
            );
        """)
        cursor.execute(
            "INSERT INTO dev_watchlists (id, contract_address, token_name, initial_liquidity, initial_price) VALUES (?, ?, ?, ?, ?)",
            ("w1", "test_ca_123", "TestToken", 100000.0, 1.0)
        )
        conn.commit()
        conn.close()

        with patch("zoe.monitor.get_dev_db_conn", side_effect=lambda: sqlite3.connect(db_path)), \
             patch("zoe.monitor.get_supabase_client", return_value=None), \
             patch("zoe.monitor.fetch_dexscreener_market_data", return_value={"found": True, "liquidity_usd": 70000.0, "price_usd": 0.70}):

            alerts = await check_watchlist_tokens()
            assert len(alerts) == 1
            assert alerts[0]["alert_type"] == "LIQUIDITY_DUMP"
            assert "30.0%" in alerts[0]["message"]

            verify_conn = sqlite3.connect(db_path)
            cur = verify_conn.cursor()
            cur.execute("SELECT contract_address, alert_type, old_value, new_value FROM dev_alerts")
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "test_ca_123"
            assert row[1] == "LIQUIDITY_DUMP"
            assert row[2] == 100000.0
            assert row[3] == 70000.0
            verify_conn.close()

    asyncio.run(_run())

def test_check_watchlist_tokens_healthy(tmp_path):
    async def _run():
        db_path = str(tmp_path / "test_monitor_healthy.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE dev_watchlists (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                contract_address TEXT NOT NULL,
                token_name TEXT,
                initial_liquidity REAL,
                initial_price REAL,
                current_liquidity REAL,
                current_price REAL,
                last_checked_at TEXT,
                created_at TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE dev_alerts (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                contract_address TEXT NOT NULL,
                token_name TEXT,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                old_value REAL,
                new_value REAL,
                created_at TEXT
            );
        """)
        cursor.execute(
            "INSERT INTO dev_watchlists (id, contract_address, token_name, initial_liquidity, initial_price) VALUES (?, ?, ?, ?, ?)",
            ("w2", "test_ca_456", "HealthyToken", 100000.0, 1.0)
        )
        conn.commit()
        conn.close()

        with patch("zoe.monitor.get_dev_db_conn", side_effect=lambda: sqlite3.connect(db_path)), \
             patch("zoe.monitor.get_supabase_client", return_value=None), \
             patch("zoe.monitor.fetch_dexscreener_market_data", return_value={"found": True, "liquidity_usd": 95000.0, "price_usd": 0.98}):

            alerts = await check_watchlist_tokens()
            assert len(alerts) == 0

            verify_conn = sqlite3.connect(db_path)
            cur = verify_conn.cursor()
            cur.execute("SELECT COUNT(*) FROM dev_alerts")
            count = cur.fetchone()[0]
            assert count == 0
            verify_conn.close()

    asyncio.run(_run())
