"""Unit tests verifying the Web3 JARVIS persona, slang handling, and proactive FUD intervention."""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import pytest

from zoe.conversation.classifier import classify_message
from zoe.conversation.prompt_builder import DEFAULT_ZOE_IDENTITY_PROMPT, build_prompt
from zoe.conversation.router import route_intent
from zoe.conversation.sentiment import analyze_group_sentiment_sync
from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.llm.mock import MockLLMClient
from zoe.memory.short_term import (
    get_recent_conversation_history,
    record_community_message,
)
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.pipeline import process_message

PROJECT_ID = "p_web3"
GROUP_ID = "-100888"


@pytest.fixture
def web3_env(tmp_path: Path):
    """Set up operational, knowledge, and memory databases for Web3 JARVIS testing."""
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
        VALUES (?, 'Web3 JARVIS Test', ?, '{"token_address": "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf", "participation": {"respond_to_casual": true}}', '2026-01-01 00:00:00', 1)
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
        "tmp_path": tmp_path,
    }

    conn_op.close()
    conn_kb.close()
    conn_mem.close()


def test_web3_classification_and_routing():
    """Verify Web3 phrases are properly classified and routed."""
    # GM
    cls_gm = classify_message("GM")
    assert cls_gm.category == "casual"

    # wen price update?
    cls_wen = classify_message("wen price update?")
    assert cls_wen.category == "direct_question"
    assert route_intent("wen price update?") == "api_call"

    # ngl this looks like a rug
    cls_fud = classify_message("ngl this looks like a rug")
    assert cls_fud.category in ("project_discussion", "casual")

    # sentiment radar detection
    sentiment = analyze_group_sentiment_sync(["ngl this looks like a rug"])
    assert sentiment == "panicked/fud"


def test_web3_jarvis_flow_simulation(web3_env):
    """Simulate the 3-step Web3 JARVIS interaction flow:
    1. User: 'GM' -> Zoe: 'GM! What's the play today?'
    2. User: 'wen price update?' -> Zoe: 'Just checked DexScreener, $FLY is at $0.0024 right now.'
    3. User: 'ngl this looks like a rug' -> Zoe proactively intervenes:
       'I hear the concern, but I've analyzed the official data: liquidity is $93k and locked. We're good.'
    """
    conns = web3_env["conns"]
    conn_op = conns["operational"]
    mem_path = web3_env["mem_path"]
    llm_client = MockLLMClient()

    # --- Step 1: User says "GM" ---
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 1, ?, 201, 'degen_1', 'GM', 0, 'message_persisted', '2026-11-08 09:00:00', '2026-11-08 09:00:00', '2026-11-08 09:00:00')
        """,
        (PROJECT_ID, GROUP_ID),
    )
    inbox_id_1 = cur.lastrowid
    conn_op.commit()

    res_1 = process_message(
        inbox_row=inbox_id_1,
        db_conns=conns,
        mem_db_path=mem_path,
        llm_client=llm_client,
        simulated=True,
    )

    assert res_1.responded is True
    assert res_1.decision.decision == "respond"
    assert "GM! What's the play today?" in res_1.response_text
    assert "**" not in res_1.response_text

    # --- Step 2: User asks "wen price update?" ---
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 2, ?, 202, 'degen_1', 'wen price update?', 0, 'message_persisted', '2026-11-08 09:00:25', '2026-11-08 09:00:25', '2026-11-08 09:00:25')
        """,
        (PROJECT_ID, GROUP_ID),
    )
    inbox_id_2 = cur.lastrowid
    conn_op.commit()

    res_2 = process_message(
        inbox_row=inbox_id_2,
        db_conns=conns,
        mem_db_path=mem_path,
        llm_client=llm_client,
        simulated=True,
    )

    assert res_2.responded is True
    assert res_2.decision.decision == "respond"
    assert "$FLY" in res_2.response_text
    assert "0.0024" in res_2.response_text
    assert "**" not in res_2.response_text

    # --- Step 3: User panics "ngl this looks like a rug" (not tagged) ---
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 3, ?, 203, 'degen_2', 'ngl this looks like a rug', 0, 'message_persisted', '2026-11-08 09:01:00', '2026-11-08 09:01:00', '2026-11-08 09:01:00')
        """,
        (PROJECT_ID, GROUP_ID),
    )
    inbox_id_3 = cur.lastrowid
    conn_op.commit()

    res_3 = process_message(
        inbox_row=inbox_id_3,
        db_conns=conns,
        mem_db_path=mem_path,
        llm_client=llm_client,
        simulated=True,
    )

    # Must proactively intervene without being tagged
    assert res_3.responded is True
    assert res_3.decision.decision == "respond"
    assert res_3.decision.reason == "proactive_fud_intervention"
    assert "liquidity is $93k and locked" in res_3.response_text
    assert "We're good" in res_3.response_text
    assert "**" not in res_3.response_text
