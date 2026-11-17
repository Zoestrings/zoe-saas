"""Unit tests for Phase 3: Caller Reputation & Community Leaderboards."""

import asyncio
from pathlib import Path
import sqlite3
from unittest.mock import patch

import pytest

from zoe.tools.caller_reputation import (
    get_leaderboard_text,
    get_reputation_db_conn,
    record_token_call,
    update_ath_for_calls,
)


def test_record_token_call(tmp_path):
    """Test recording a token call creates callers and token_calls records."""
    db_path = str(tmp_path / "test_reputation.db")

    with patch("zoe.tools.caller_reputation.get_reputation_db_conn", side_effect=lambda: sqlite3.connect(db_path)), \
         patch("zoe.tools.caller_reputation.get_supabase_client", return_value=None):

        # Ensure schema
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE dev_callers (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                telegram_user_id TEXT NOT NULL,
                username TEXT,
                total_calls INTEGER DEFAULT 0,
                successful_calls INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                best_multiplier REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                UNIQUE(project_id, telegram_user_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE dev_token_calls (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                caller_id TEXT NOT NULL,
                contract_address TEXT NOT NULL,
                token_name TEXT,
                call_price REAL NOT NULL,
                ath_price REAL DEFAULT 0.0,
                ath_multiplier REAL DEFAULT 1.0,
                status TEXT DEFAULT 'tracking',
                called_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

        record = record_token_call(
            project_id="proj_test_rep",
            telegram_user_id="998877",
            contract_address="DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            username="@cryptoking",
            token_name="Bonk",
            call_price=0.000025,
        )

        assert record is not None
        assert record["project_id"] == "proj_test_rep"
        assert record["contract_address"] == "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
        assert record["call_price"] == 0.000025
        assert record["ath_multiplier"] == 1.0
        assert record["status"] == "tracking"

        # Verify callers record
        vconn = sqlite3.connect(db_path)
        cur = vconn.cursor()
        cur.execute("SELECT username, total_calls, best_multiplier FROM dev_callers WHERE telegram_user_id = '998877'")
        caller_row = cur.fetchone()
        assert caller_row is not None
        assert caller_row[0] == "cryptoking"
        assert caller_row[1] == 1
        assert caller_row[2] == 1.0

        # Verify token_calls record
        cur.execute("SELECT token_name, call_price, ath_price FROM dev_token_calls WHERE contract_address = 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263'")
        call_row = cur.fetchone()
        assert call_row is not None
        assert call_row[0] == "Bonk"
        assert call_row[1] == 0.000025
        assert call_row[2] == 0.000025
        vconn.close()


def test_leaderboard_formatting(tmp_path):
    """Test leaderboard formatting orders by best_multiplier descending."""
    db_path = str(tmp_path / "test_leaderboard.db")

    with patch("zoe.tools.caller_reputation.get_reputation_db_conn", side_effect=lambda: sqlite3.connect(db_path)), \
         patch("zoe.tools.caller_reputation.get_supabase_client", return_value=None):

        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE dev_callers (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                telegram_user_id TEXT NOT NULL,
                username TEXT,
                total_calls INTEGER DEFAULT 0,
                successful_calls INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                best_multiplier REAL DEFAULT 1.0,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO dev_callers (id, project_id, telegram_user_id, username, total_calls, successful_calls, win_rate, best_multiplier, created_at)
            VALUES 
            ('c1', 'proj_alpha', '101', 'trader_bob', 12, 5, 41.7, 2.1, '2026-11-17T00:00:00Z'),
            ('c2', 'proj_alpha', '102', 'crypto_queen', 5, 4, 80.0, 3.5, '2026-11-17T00:00:00Z'),
            ('c3', 'proj_alpha', '103', 'sol_sniper', 20, 10, 50.0, 1.8, '2026-11-17T00:00:00Z')
            """
        )
        conn.commit()
        conn.close()

        text = get_leaderboard_text("proj_alpha", limit=5)

        assert "🏆 Top Callers in this Community" in text
        assert "1. @crypto_queen - 3.5x (5 calls)" in text
        assert "2. @trader_bob - 2.1x (12 calls)" in text
        assert "3. @sol_sniper - 1.8x (20 calls)" in text
        assert "Only verified on-chain calls are tracked." in text


def test_update_caller_ath(tmp_path):
    """Test background ATH price monitor updates call multiplier and caller win rate."""
    async def _run():
        db_path = str(tmp_path / "test_ath.db")

        with patch("zoe.tools.caller_reputation.get_reputation_db_conn", side_effect=lambda: sqlite3.connect(db_path)), \
             patch("zoe.tools.caller_reputation.get_supabase_client", return_value=None), \
             patch("zoe.tools.caller_reputation.fetch_dexscreener_market_data", return_value={"found": True, "price_usd": 3.00}):

            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                CREATE TABLE dev_callers (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    telegram_user_id TEXT NOT NULL,
                    username TEXT,
                    total_calls INTEGER DEFAULT 0,
                    successful_calls INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0.0,
                    best_multiplier REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE dev_token_calls (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    caller_id TEXT NOT NULL,
                    contract_address TEXT NOT NULL,
                    token_name TEXT,
                    call_price REAL NOT NULL,
                    ath_price REAL DEFAULT 0.0,
                    ath_multiplier REAL DEFAULT 1.0,
                    status TEXT DEFAULT 'tracking',
                    called_at TEXT NOT NULL
                )
                """
            )
            # Caller called token at $1.00
            conn.execute(
                "INSERT INTO dev_callers (id, project_id, telegram_user_id, username, total_calls, successful_calls, win_rate, best_multiplier, created_at) VALUES (?, ?, ?, ?, 1, 0, 0.0, 1.0, ?)",
                ("caller_1", "proj_gamma", "user_gamma_1", "moon_caller", "2026-11-17T00:00:00Z"),
            )
            conn.execute(
                "INSERT INTO dev_token_calls (id, project_id, caller_id, contract_address, token_name, call_price, ath_price, ath_multiplier, status, called_at) VALUES (?, ?, ?, ?, ?, 1.00, 1.00, 1.0, 'tracking', ?)",
                ("call_1", "proj_gamma", "caller_1", "TokenCA_Gamma", "GammaCoin", "2026-11-17T00:00:00Z"),
            )
            conn.commit()
            conn.close()

            # Current price mocked as $3.00 -> 3.0x multiplier!
            updated = await update_ath_for_calls()

            assert len(updated) == 1
            assert updated[0]["ath_price"] == 3.00
            assert updated[0]["ath_multiplier"] == 3.0

            # Verify dev_token_calls updated
            vconn = sqlite3.connect(db_path)
            cur = vconn.cursor()
            cur.execute("SELECT ath_price, ath_multiplier FROM dev_token_calls WHERE id = 'call_1'")
            row_call = cur.fetchone()
            assert row_call[0] == 3.00
            assert row_call[1] == 3.0

            # Verify dev_callers updated win_rate (> 1.5x is a win) and best_multiplier
            cur.execute("SELECT successful_calls, win_rate, best_multiplier FROM dev_callers WHERE id = 'caller_1'")
            row_caller = cur.fetchone()
            assert row_caller[0] == 1
            assert row_caller[1] == 100.0
            assert row_caller[2] == 3.0
            vconn.close()

    asyncio.run(_run())
