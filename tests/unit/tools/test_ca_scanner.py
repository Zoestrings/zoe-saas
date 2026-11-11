"""Unit tests verifying Module 2: Crypto Intelligence (CA Scanner).

Tests:
- Test A: EVM address (0x...) routes to "crypto_intelligence" and fetches data.
- Test B: Solana address routes correctly.
- Test C: Random non-CA string does not trigger tool.
- Test D: Mock DexScreener API to return data and assert pipeline enqueues formatted response.
"""

from pathlib import Path
from typing import Any, Dict
import pytest

from zoe.conversation.intent import detect_contract_address, detect_intent
from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.tools.crypto_intel import (
    format_token_intel_response,
    get_token_intel,
    get_token_intel_sync,
)
from zoe.worker.pipeline import process_message

PROJECT_ID = "p_ca_scanner_test"
GROUP_ID = "-100888"


# Test A: EVM address (0x...) routes to "crypto_intelligence" and fetches data
def test_evm_address_routes_and_fetches_data(monkeypatch):
    """Verify EVM address routes to crypto_intelligence and fetches metadata."""
    evm_ca = "0x71C84166b3A747153e32d1440C7338837F7bbE79"

    # 1. Detection
    detected = detect_contract_address(f"Look at this token: {evm_ca}")
    assert detected == evm_ca

    # 2. Intent Routing
    intent_res = detect_intent(f"Check CA: {evm_ca}")
    assert intent_res.intent == "crypto_intelligence"
    assert intent_res.confidence == 1.0

    # 3. Data Fetch with Mocked DexScreener API response
    class MockResponse:
        status_code = 200

        def json(self):
            return {
                "pairs": [
                    {
                        "baseToken": {"name": "Ethereum Alpha", "symbol": "EALPHA"},
                        "priceUsd": "12.34",
                        "liquidity": {"usd": 500000.0},
                        "volume": {"h24": 150000.0},
                    }
                ]
            }

    monkeypatch.setattr("httpx.Client.get", lambda self, url, **kwargs: MockResponse())

    intel = get_token_intel_sync(evm_ca)
    assert intel["found"] is True
    assert intel["name"] == "Ethereum Alpha"
    assert intel["symbol"] == "EALPHA"
    assert intel["price"] == "12.34"
    assert float(intel["liquidity"]) == 500000.0
    assert float(intel["volume_24h"]) == 150000.0


# Test B: Solana address routes correctly
def test_solana_address_routes_correctly():
    """Verify Solana Base58 address routes to crypto_intelligence."""
    sol_ca = "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf"

    # 1. Detection
    detected = detect_contract_address(sol_ca)
    assert detected == sol_ca

    # 2. Intent Routing
    intent_res = detect_intent(sol_ca)
    assert intent_res.intent == "crypto_intelligence"
    assert intent_res.confidence == 1.0


# Test C: Random non-CA string does not trigger tool
def test_random_string_does_not_trigger_ca_scanner():
    """Verify casual text, questions, and non-CA strings do not trigger crypto_intelligence."""
    queries = [
        "What is the weather today?",
        "Hey everyone how are you doing",
        "0x123",
        "who watched the football game yesterday",
        "gm fam wagmi",
    ]

    for q in queries:
        detected = detect_contract_address(q)
        assert detected is None
        intent_res = detect_intent(q)
        assert intent_res.intent != "crypto_intelligence"


# Test D: Mock DexScreener API to return data and assert pipeline enqueues formatted response
@pytest.fixture
def ca_env(tmp_path: Path):
    """Set up operational, knowledge, and memory databases for CA pipeline test."""
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
        VALUES (?, 'CA Test Project', ?, '{"modules": {"crypto_intelligence": true, "community_intelligence": true, "community_manager": true}}', '2026-01-01 00:00:00', 1)
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
        "kb_path": kb_path,
        "mem_path": mem_path,
    }

    conn_op.close()
    conn_kb.close()
    conn_mem.close()


def test_mock_dexscreener_pipeline_enqueues_formatted_response(ca_env, monkeypatch):
    """Verify DexScreener API mock returns structured response directly to outbox without LLM."""
    conns = ca_env["conns"]
    conn_op = conns["operational"]
    mem_path = ca_env["mem_path"]

    sol_ca = "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN"

    # Insert incoming message with Solana CA
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 101, ?, 901, 'trader_dex', ?, 0, 'message_persisted', '2026-11-09 14:00:00', '2026-11-09 14:00:00', '2026-11-09 14:00:00')
        """,
        (PROJECT_ID, GROUP_ID, f"Check this new coin: {sol_ca}"),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    # Mock DexScreener API via httpx.Client.get
    class MockDexResponse:
        status_code = 200

        def json(self):
            return {
                "pairs": [
                    {
                        "baseToken": {"name": "Jupiter", "symbol": "JUP"},
                        "priceUsd": "1.15",
                        "liquidity": {"usd": 42000000.0},
                        "volume": {"h24": 18500000.0},
                    }
                ]
            }

    monkeypatch.setattr("httpx.Client.get", lambda self, url, **kwargs: MockDexResponse())

    # Run pipeline
    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        mem_db_path=mem_path,
        simulated=True,
    )

    # Assertions
    assert result.responded is True
    assert result.response_text is not None

    resp = result.response_text
    assert "Here's the live intel" not in resp
    assert "Would you like me to check" not in resp
    assert "Always DYOR" not in resp
    assert resp.startswith("🪙")
    assert "CA: " in resp
    assert "Price: $1.15" in resp
    assert "Liquidity: $42,000,000.00" in resp
    assert "24h Volume: $18,500,000.00" in resp
    assert resp.splitlines()[-1].startswith("📊 24h Volume:")
    assert "**" not in resp  # Strict plain text formatting

    # Verify message enqueued into outbox_messages table
    cur_outbox = conn_op.execute(
        "SELECT id, text, state FROM outbox_messages WHERE project_id = ? AND group_id = ?",
        (PROJECT_ID, GROUP_ID),
    )
    outbox_row = cur_outbox.fetchone()
    assert outbox_row is not None
    assert outbox_row[1] == resp
    assert outbox_row[2] in ("pending", "queued")
