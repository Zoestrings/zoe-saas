"""Unit tests verifying Zoe V2: Modular Genius features, routing, and 8GB safe constraints."""

from pathlib import Path
import pytest

from zoe.conversation.router import extract_detected_ca, route_intent
from zoe.conversation.sentiment import (
    check_group_panic_buffer,
    classify_sentiment_heuristics,
    record_group_message,
)
from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.llm.mock import MockLLMClient
from zoe.llm.providers.groq_provider import GroqProvider
from zoe.tools.crypto_intel import format_ca_analysis
from zoe.worker.pipeline import process_message

PROJECT_ID = "p_modular_v2"
GROUP_ID = "-100555"


def test_groq_provider_default_model_is_70b():
    """Verify GroqProvider default model is upgraded to llama-3.3-70b-versatile."""
    provider = GroqProvider(api_key="gsk_test_mock_key")
    assert provider.model == "llama-3.3-70b-versatile"


def test_router_ca_detection_and_general_knowledge():
    """Verify routing for Solana CAs, EVM CAs, coding, and general knowledge."""
    # 1. Solana CA
    sol_ca = "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf"
    assert extract_detected_ca(sol_ca) == sol_ca
    assert route_intent(sol_ca) == "ca_detection"
    assert route_intent(f"Check this token: {sol_ca}") == "ca_detection"

    # 2. EVM CA
    evm_ca = "0x71C84166b3A747153e32d1440C7338837F7bbE79"
    assert extract_detected_ca(evm_ca) == evm_ca
    assert route_intent(evm_ca) == "ca_detection"

    # 3. General Knowledge / Coding
    assert route_intent("write a python script to say hello") == "general_knowledge"
    assert route_intent("How do I write a Python loop?") == "general_knowledge"
    assert route_intent("Explain smart contracts") == "general_knowledge"

    # 4. Project-Specific inquiry routes to knowledge
    assert route_intent("what is Hummingbird all about?") == "knowledge"
    assert route_intent("what is the token utility of $FLY?") == "knowledge"


def test_crypto_intel_jarvis_formatting():
    """Verify format_ca_analysis outputs the JARVIS-style analysis string."""
    sample_intel = {
        "ca": "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf",
        "name": "Hummingbird ($FLY)",
        "price": "$0.0024",
        "liquidity": "$93,712.00",
    }
    formatted = format_ca_analysis(sample_intel)
    assert "I've analyzed that contract address." in formatted
    assert "Token: Hummingbird ($FLY)" in formatted
    assert "Price: $0.0024" in formatted
    assert "Liquidity: $93,712.00" in formatted
    assert "DYOR, stay safe." in formatted


def test_community_sentiment_3_of_5_panic_buffer():
    """Verify local buffer triggers proactive intervention when 3 of 5 messages contain panic keywords."""
    test_group = "grp_radar_test"
    record_group_message(test_group, "Hey guys good morning")
    record_group_message(test_group, "Price is dipping a bit")
    record_group_message(test_group, "ngl this looks like a rug")
    record_group_message(test_group, "Is this a scam??")
    record_group_message(test_group, "devs dumping their tokens")

    # 3 out of 5 contain "rug", "scam", "dump"
    assert check_group_panic_buffer(test_group) is True

    messages = [
        "Hey guys good morning",
        "Price is dipping a bit",
        "ngl this looks like a rug",
        "Is this a scam??",
        "devs dumping their tokens",
    ]
    sentiment = classify_sentiment_heuristics(messages)
    assert sentiment == "panicked/fud"


@pytest.fixture
def modular_env(tmp_path: Path):
    """Set up test databases for pipeline integration."""
    op_path = tmp_path / "operational.db"
    conn_op = open_operational_db(op_path)
    sql_op = (
        Path(__file__).resolve().parent.parent.parent
        / "src/zoe/db/schema_operational.sql"
    ).read_text(encoding="utf-8")
    conn_op.executescript(sql_op)

    conn_op.execute(
        """
        INSERT INTO projects (project_id, name, telegram_group_id, config_json, created_at, active)
        VALUES (?, 'Modular Test', ?, '{"modules": {"crypto_intelligence": true, "community_intelligence": true, "community_manager": true}}', '2026-01-01 00:00:00', 1)
        """,
        (PROJECT_ID, GROUP_ID),
    )
    conn_op.commit()

    kb_path = tmp_path / "official_knowledge.db"
    conn_kb = open_official_knowledge_db(kb_path)
    sql_kb = (
        Path(__file__).resolve().parent.parent.parent
        / "src/zoe/db/schema_knowledge.sql"
    ).read_text(encoding="utf-8")
    conn_kb.executescript(sql_kb)

    mem_path = tmp_path / "community_memory.db"
    conn_mem = open_community_memory_db(mem_path)
    sql_mem = (
        Path(__file__).resolve().parent.parent.parent
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
        "tmp_path": tmp_path,
    }

    conn_op.close()
    conn_kb.close()
    conn_mem.close()


def test_general_knowledge_pipeline_execution(modular_env):
    """Verify general coding question routes to general_knowledge and answers without Accuracy Guard block."""
    conns = modular_env["conns"]
    conn_op = conns["operational"]
    mem_path = modular_env["mem_path"]

    query = "write a python script to say hello"

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 1, ?, 701, 'coder_1', ?, 0, 'message_persisted', '2026-11-09 13:00:00', '2026-11-09 13:00:00', '2026-11-09 13:00:00')
        """,
        (PROJECT_ID, GROUP_ID, query),
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
    assert "print('Hello, world!')" in result.response_text
    assert "I don't have that in my official documents yet" not in result.response_text


def test_ca_detection_pipeline_execution(modular_env, monkeypatch):
    """Verify pasting a contract address routes to ca_detection and returns DexScreener analysis."""
    conns = modular_env["conns"]
    conn_op = conns["operational"]
    mem_path = modular_env["mem_path"]

    sol_ca = "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf"

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 2, ?, 702, 'degen_trader', ?, 0, 'message_persisted', '2026-11-09 13:05:00', '2026-11-09 13:05:00', '2026-11-09 13:05:00')
        """,
        (PROJECT_ID, GROUP_ID, sol_ca),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    # Mock sync CA lookup
    def mock_analyze(ca: str) -> str:
        return f"I've analyzed that contract address. Token: Hummingbird ($FLY). Price: $0.0024. Liquidity: $93,712.00. DYOR, stay safe."

    monkeypatch.setattr("zoe.tools.crypto_intel.analyze_contract_address_sync", mock_analyze)

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        mem_db_path=mem_path,
        simulated=True,
    )

    assert result.responded is True
    assert "I've analyzed that contract address." in result.response_text
    assert "Hummingbird ($FLY)" in result.response_text
    assert "DYOR, stay safe." in result.response_text

