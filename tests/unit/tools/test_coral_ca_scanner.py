"""Unit tests for Coral-beating CA scanner, risk reports, inline keyboard buttons, and menu commands."""

import json
from pathlib import Path
from typing import Any, Dict
import pytest

from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.outbox.service import drain_outbox, enqueue_response
from zoe.telegram.mock_adapter import MockTelegramAdapter
from zoe.tools.crypto_intel import (
    format_token_intel_response,
    generate_ca_inline_keyboard,
    get_token_intel_sync,
)
from zoe.worker.pipeline import process_message

PROJECT_ID = "p_coral_test"
GROUP_ID = "-100777"


def test_no_caution_warning_even_with_thin_liquidity():
    """Verify caution warning is completely removed even with thin liquidity."""
    intel_thin = {
        "found": True,
        "ca": "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon",
        "name": "One Love Sailing Coin",
        "symbol": "ONELOVE",
        "price": "0.0049",
        "market_cap": "49000",
        "liquidity": "48.20",
        "volume_24h": "120.00",
    }
    resp = format_token_intel_response(intel_thin)
    assert "⚠️ Caution: Thin Liquidity" not in resp
    assert "Caution" not in resp
    assert "🪙 One Love Sailing Coin (ONELOVE) · SOLANA" in resp


def test_normal_liquidity_no_caution_warning():
    """Verify liquidity >= $1000 does NOT flag thin liquidity."""
    intel_healthy = {
        "found": True,
        "ca": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
        "name": "Jupiter",
        "symbol": "JUP",
        "price": "1.15",
        "market_cap": "1500000000",
        "liquidity": "42000000.00",
        "volume_24h": "18000000.00",
    }
    resp = format_token_intel_response(intel_healthy)
    assert "⚠️ Caution: Thin Liquidity" not in resp
    assert "🪙 Jupiter (JUP) · SOLANA" in resp


def test_strict_ca_scanner_formatting_test_a_no_conversational_fluff():
    """Test A: Trigger a CA scan. Assert the output string does NOT contain conversational fluff."""
    intel = {
        "found": True,
        "ca": "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon",
        "name": "One Love Sailing Coin",
        "symbol": "ONELOVE",
        "price": "0.0049",
        "market_cap": "49000",
        "liquidity": "48.20",
        "volume_24h": "120.00",
    }
    resp = format_token_intel_response(intel)
    assert "Here's the live intel" not in resp
    assert "Would you like me to check" not in resp
    assert "Always DYOR" not in resp
    assert "Token:" not in resp


def test_strict_ca_scanner_formatting_test_b_starts_and_ends_strictly():
    """Test B: Assert the output string starts with 🪙 and ends with 24h Volume."""
    intel = {
        "found": True,
        "ca": "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon",
        "name": "One Love Sailing Coin",
        "symbol": "ONELOVE",
        "price": "0.0049",
        "market_cap": "49000",
        "liquidity": "48.20",
        "volume_24h": "120.00",
    }
    resp = format_token_intel_response(intel)
    assert resp.startswith("🪙")
    lines = resp.splitlines()
    assert lines[-1].startswith("📊 24h Volume:")
    assert lines[1].startswith("CA:")
    assert lines[2].startswith("💰 Price:")
    assert lines[3].startswith("🌐 Market Cap:")
    assert lines[4].startswith("💧 Liquidity:")


def test_solana_inline_keyboard_generation():
    """Verify Solana CA creates Chart, Solscan, and Jupiter swap buttons."""
    ca = "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon"
    intel = {
        "raw_pair": {
            "chainId": "solana",
            "url": f"https://dexscreener.com/solana/{ca}",
            "info": {
                "websites": [{"url": "https://www.onelovesailingcoin.com"}],
            },
        }
    }
    kb = generate_ca_inline_keyboard(ca, intel)
    assert len(kb) >= 2

    # Row 1: Chart & Explorer
    row0_texts = [btn["text"] for btn in kb[0]]
    assert "📈 Chart" in row0_texts
    assert "🔍 Solscan" in row0_texts
    assert kb[0][0]["url"] == f"https://dexscreener.com/solana/{ca}"
    assert kb[0][1]["url"] == f"https://solscan.io/token/{ca}"

    # Row 2: Buy on Jupiter & Website
    row1_texts = [btn["text"] for btn in kb[1]]
    assert "⚡ Buy on Jupiter" in row1_texts
    assert "🌐 Website" in row1_texts
    assert kb[1][0]["url"] == f"https://jup.ag/swap/SOL-{ca}"
    assert kb[1][1]["url"] == "https://www.onelovesailingcoin.com"


def test_evm_inline_keyboard_generation():
    """Verify EVM 0x... address generates Etherscan and Uniswap buttons."""
    ca = "0x71C84166b3A747153e32d1440C7338837F7bbE79"
    intel = {
        "raw_pair": {
            "chainId": "ethereum",
            "url": f"https://dexscreener.com/ethereum/{ca}",
        }
    }
    kb = generate_ca_inline_keyboard(ca, intel)
    assert len(kb) >= 2

    row0_texts = [btn["text"] for btn in kb[0]]
    assert "📈 Chart" in row0_texts
    assert "🔍 Etherscan" in row0_texts
    assert kb[0][1]["url"] == f"https://etherscan.io/token/{ca}"

    row1_texts = [btn["text"] for btn in kb[1]]
    assert "⚡ Buy on Uniswap" in row1_texts
    assert kb[1][0]["url"] == f"https://app.uniswap.org/#/swap?outputCurrency={ca}"


@pytest.fixture
def coral_env(tmp_path: Path):
    op_path = tmp_path / "operational.db"
    conn_op = open_operational_db(op_path)
    sql_op = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src/zoe/db/schema_operational.sql"
    ).read_text(encoding="utf-8")
    conn_op.executescript(sql_op)

    conn_op.execute(
        """
        INSERT INTO projects (project_id, name, telegram_group_id, config_json, created_at, active)
        VALUES (?, 'Coral Test Project', ?, '{"token_address": "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon", "modules": {"crypto_intelligence": true}}', '2026-01-01 00:00:00', 1)
        """,
        (PROJECT_ID, GROUP_ID),
    )
    conn_op.commit()

    kb_path = tmp_path / "official_knowledge.db"
    conn_kb = open_official_knowledge_db(kb_path)
    sql_kb = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src/zoe/db/schema_knowledge.sql"
    ).read_text(encoding="utf-8")
    conn_kb.executescript(sql_kb)

    mem_path = tmp_path / "community_memory.db"
    conn_mem = open_community_memory_db(mem_path)
    sql_mem = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src/zoe/db/schema_community_memory.sql"
    ).read_text(encoding="utf-8")
    conn_mem.executescript(sql_mem)

    conns = {
        "operational": conn_op,
        "knowledge": conn_kb,
        "memory": conn_mem,
    }

    yield {
        "conns": conns,
        "op_path": op_path,
        "mem_path": mem_path,
    }

    conn_op.close()
    conn_kb.close()
    conn_mem.close()


@pytest.mark.anyio
async def test_drain_outbox_delivers_inline_keyboard(coral_env):
    """Verify drain_outbox correctly passes inline_keyboard to adapter."""
    conn_op = coral_env["conns"]["operational"]
    adapter = MockTelegramAdapter()

    # Enqueue message with inline keyboard
    test_kb = [
        [{"text": "📈 Chart", "url": "https://dexscreener.com/solana/test"}],
        [{"text": "⚡ Buy on Jupiter", "url": "https://jup.ag/swap/SOL-test"}],
    ]

    # Create dummy inbox message
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 201, ?, 701, 'trader_1', 'dummy', 0, 'processing', '2026-11-09 14:00:00', '2026-11-09 14:00:00', '2026-11-09 14:00:00')
        """,
        (PROJECT_ID, GROUP_ID),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    outbox_id = enqueue_response(
        conn=conn_op,
        project_id=PROJECT_ID,
        inbox_message_id=inbox_id,
        group_id=GROUP_ID,
        text="🪙 One Love · SOLANA",
        inline_keyboard=test_kb,
    )
    assert outbox_id > 0

    # Drain outbox
    delivered = await drain_outbox(
        conn=conn_op,
        project_id=PROJECT_ID,
        adapter=adapter,
    )
    assert delivered == 1
    assert len(adapter.sent_messages) == 1
    sent_msg = adapter.sent_messages[0]
    assert sent_msg["text"] == "🪙 One Love · SOLANA"
    assert sent_msg.get("inline_keyboard") == test_kb


def test_commands_credits_and_add_credits(coral_env):
    """Verify /credits and /add_credits command responses."""
    conns = coral_env["conns"]
    conn_op = conns["operational"]
    mem_path = coral_env["mem_path"]

    for cmd, expected_substring in [
        ("/credits", "balance is unlimited"),
        ("/add_credits", "membership includes full access"),
    ]:
        cur = conn_op.execute(
            """
            INSERT INTO inbox_messages (
                project_id, telegram_update_id, group_id, telegram_message_id,
                pseudonymous_user_id, text, is_forward, state, state_changed_at,
                created_at, message_timestamp
            ) VALUES (?, ?, ?, ?, 'user_menu', ?, 0, 'message_persisted', '2026-11-09 14:00:00', '2026-11-09 14:00:00', '2026-11-09 14:00:00')
            """,
            (PROJECT_ID, 300 + len(cmd), GROUP_ID, 800 + len(cmd), cmd),
        )
        inbox_id = cur.lastrowid
        conn_op.commit()

        result = process_message(
            inbox_row=inbox_id,
            db_conns=conns,
            mem_db_path=mem_path,
            simulated=True,
        )
        assert result.responded is True
        assert expected_substring in result.response_text

