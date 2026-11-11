"""Unit tests verifying Contextual Slang Matching and Natural Conversational Flow."""

from pathlib import Path
import pytest

from zoe.conversation.prompt_builder import DEFAULT_ZOE_IDENTITY_PROMPT, build_prompt
from zoe.conversation.router import route_intent
from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.llm.mock import MockLLMClient
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.pipeline import process_message

PROJECT_ID = "p_slang"
GROUP_ID = "-100999"


@pytest.fixture
def slang_env(tmp_path: Path):
    """Set up operational, knowledge, and memory databases."""
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
        VALUES (?, 'Slang Test', ?, '{"token_address": "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf", "participation": {"respond_to_casual": true, "rate_limit_seconds": 0.0}}', '2026-01-01 00:00:00', 1)
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
    conn_kb.commit()

    mem_path = tmp_path / "community_memory.db"
    conn_mem = open_community_memory_db(mem_path)
    sql_mem = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src/zoe/db/schema_community_memory.sql"
    ).read_text(encoding="utf-8")
    conn_mem.executescript(sql_mem)
    conn_mem.commit()

    index_dir = tmp_path / "indexes"
    index_dir.mkdir(parents=True, exist_ok=True)

    conns = {
        "operational": conn_op,
        "knowledge": conn_kb,
        "memory": conn_mem,
    }
    return conns, op_path, kb_path, mem_path, index_dir


@pytest.mark.automated
def test_test_a_serious_technical_question_drops_slang(slang_env) -> None:
    """Test A (Serious): 'How do I fix a smart contract vulnerability?' -> Professional, no WAGMI or GM."""
    conns, op_path, kb_path, mem_path, index_dir = slang_env
    conn_op = conns["operational"]

    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=1,
        group_id=GROUP_ID,
        telegram_message_id=201,
        pseudonymous_user_id="dev_user",
        text="How do I fix a smart contract vulnerability?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-09 12:00:00",
    )

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, 0, ?, 'message_persisted', ?, ?)
        """,
        (msg.project_id, msg.telegram_update_id, msg.group_id, msg.telegram_message_id,
         msg.pseudonymous_user_id, msg.text, msg.timestamp, msg.timestamp, msg.timestamp),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    res = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
    )

    assert res.responded is True
    reply = res.response_text
    # Must NOT contain inappropriate hype/greeting slang in a serious technical context
    assert "WAGMI" not in reply
    assert "GM" not in reply
    # Must sound technical and professional
    assert any(term in reply.lower() for term in ["vulnerability", "reentrancy", "audit", "guard", "testing"])
    # Must not contain robotic preambles
    assert not reply.lower().startswith("scanning")
    assert not reply.lower().startswith("processing")


@pytest.mark.automated
def test_test_b_hype_milestone_matches_energy_with_slang(slang_env) -> None:
    """Test B (Hype): 'We just 10x'd the liquidity!' -> Matches hype with LFG/WAGMI."""
    conns, op_path, kb_path, mem_path, index_dir = slang_env
    conn_op = conns["operational"]

    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=2,
        group_id=GROUP_ID,
        telegram_message_id=202,
        pseudonymous_user_id="bull_user",
        text="Zoe we just 10x'd the liquidity!",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-09 12:01:00",
    )

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, 0, ?, 'message_persisted', ?, ?)
        """,
        (msg.project_id, msg.telegram_update_id, msg.group_id, msg.telegram_message_id,
         msg.pseudonymous_user_id, msg.text, msg.timestamp, msg.timestamp, msg.timestamp),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    res = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
    )

    assert res.responded is True
    reply = res.response_text
    # Asserts response DOES contain appropriate hype slang
    assert "LFG" in reply or "WAGMI" in reply


@pytest.mark.automated
def test_test_c_greeting_starts_with_gm_not_wagmi(slang_env) -> None:
    """Test C (Greeting): 'GM' -> Starts with GM but does NOT end with WAGMI."""
    conns, op_path, kb_path, mem_path, index_dir = slang_env
    conn_op = conns["operational"]

    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=3,
        group_id=GROUP_ID,
        telegram_message_id=203,
        pseudonymous_user_id="early_bird",
        text="GM",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-09 12:02:00",
    )

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, 0, ?, 'message_persisted', ?, ?)
        """,
        (msg.project_id, msg.telegram_update_id, msg.group_id, msg.telegram_message_id,
         msg.pseudonymous_user_id, msg.text, msg.timestamp, msg.timestamp, msg.timestamp),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    res = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
    )

    assert res.responded is True
    reply = res.response_text
    assert reply.startswith("GM")
    assert not reply.endswith("WAGMI")
    assert "WAGMI" not in reply


@pytest.mark.automated
def test_system_prompt_enforces_contextual_slang_rules() -> None:
    """Verify system prompt enforces contextual slang and bans robotic preambles."""
    prompt = DEFAULT_ZOE_IDENTITY_PROMPT

    # Contextual slang rule
    assert "13. Contextual Slang Rules:" in prompt
    assert "Slang must strictly correspond to the context of the conversation." in prompt
    assert "Do NOT force slang into technical, troubleshooting, or serious responses." in prompt
    assert "Drop the slang entirely for serious topics." in prompt

    # Ban robotic preambles rule
    assert "14. Ban Robotic Preambles:" in prompt
    assert "Never use robotic system phrases like 'Scanning the request', 'Processing...', 'Executing...', or 'Fetching data...'. Answer naturally." in prompt

