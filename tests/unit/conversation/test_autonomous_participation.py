"""Unit tests verifying Autonomous Participation Engine, conversational flow, and bug fixes."""

from datetime import datetime, timezone
from pathlib import Path
import pytest

from zoe.conversation.classifier import classify_message
from zoe.conversation.intent import detect_intent
from zoe.conversation.prompt_builder import DEFAULT_ZOE_IDENTITY_PROMPT, build_prompt
from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.llm.mock import MockLLMClient
from zoe.participation.decision import should_respond
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.pipeline import process_message

PROJECT_ID = "p_auto"
GROUP_ID = "-100888"


@pytest.fixture
def auto_env(tmp_path: Path):
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
        VALUES (?, 'Auto Test', ?, '{"token_address": "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf", "participation": {"rate_limit_seconds": 0.0}}', '2026-01-01 00:00:00', 1)
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


def mock_staking_search(query: str):
    return [
        {
            "title": "Hummingbird Staking Guide",
            "body": "You can stake your tokens through the official Hummingbird staking portal. The unbonding period is 14 days.",
            "href": "https://hummingbird.org/staking",
        }
    ]


@pytest.mark.automated
def test_test_a_autonomous_project_question_responds_without_tag(auto_env) -> None:
    """Test A (Autonomous): 'How do I stake my tokens?' -> Zoe replies without being tagged."""
    conns, op_path, kb_path, mem_path, index_dir = auto_env
    conn_op = conns["operational"]

    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=1,
        group_id=GROUP_ID,
        telegram_message_id=101,
        pseudonymous_user_id="user_alice",
        text="How do I stake my tokens?",  # NOT tagged
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-09 12:00:00",
    )

    # 1. Intent Detection
    intent_res = detect_intent(msg.text)
    assert intent_res.intent == "project_question"

    # 2. Decision Logic
    cls = classify_message(msg.text)
    dec = should_respond(message=msg, classification=cls, db_conn=conn_op)
    assert dec.should_respond is True
    assert dec.decision == "respond"
    assert dec.reason in ("autonomous_question_answered", "direct_question_answered")

    # 3. Pipeline execution
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
        web_search_fn=mock_staking_search,
    )
    assert res.responded is True
    assert "stake" in res.response_text.lower() or "staking" in res.response_text.lower()


@pytest.mark.automated
def test_test_b_flow_price_query_asks_followup(auto_env) -> None:
    """Test B (Flow): 'What is the price of fly?' -> Zoe replies and asks an engaging follow-up."""
    conns, op_path, kb_path, mem_path, index_dir = auto_env
    conn_op = conns["operational"]

    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=2,
        group_id=GROUP_ID,
        telegram_message_id=102,
        pseudonymous_user_id="user_bob",
        text="What is the price of fly?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-09 12:01:00",
    )

    cls = classify_message(msg.text)
    dec = should_respond(message=msg, classification=cls, db_conn=conn_op)
    assert dec.should_respond is True
    assert dec.decision == "respond"
    assert dec.reason == "strict_price_routing"

    # Process message and verify follow-up question in response
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
    # Follow-up engagement question
    assert "?" in res.response_text
    assert any(q in res.response_text.lower() for q in ["do you want me to", "would you like", "check", "volume"])


@pytest.mark.automated
def test_test_c_hallucination_fix_missed_message(auto_env) -> None:
    """Test C (Hallucination Fix): 'Why didn't you reply?' -> Zoe honestly says 'I missed that message'."""
    conns, op_path, kb_path, mem_path, index_dir = auto_env
    conn_op = conns["operational"]

    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=3,
        group_id=GROUP_ID,
        telegram_message_id=103,
        pseudonymous_user_id="user_charlie",
        text="Zoe why didn't you reply?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-09 12:02:00",
    )

    cls = classify_message(msg.text)
    dec = should_respond(message=msg, classification=cls, db_conn=conn_op)
    assert dec.should_respond is True
    assert dec.decision == "respond"

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
    assert "i missed that message" in res.response_text.lower()
    assert "apologies" in res.response_text.lower()
    # Confirm no hallucinated technical excuses
    assert "rate limit" not in res.response_text.lower()
    assert "server error" not in res.response_text.lower()


@pytest.mark.automated
def test_test_d_silence_on_members_talking(auto_env) -> None:
    """Test D (Silence): 'Who watched the match?' -> Zoe remains completely silent."""
    conns, op_path, kb_path, mem_path, index_dir = auto_env
    conn_op = conns["operational"]

    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=4,
        group_id=GROUP_ID,
        telegram_message_id=104,
        pseudonymous_user_id="user_dan",
        text="Who watched the match?",  # non-project chat between members
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-09 12:03:00",
    )

    intent_res = detect_intent(msg.text)
    assert intent_res.intent == "members_talking"

    cls = classify_message(msg.text)
    dec = should_respond(message=msg, classification=cls, db_conn=conn_op)
    assert dec.should_respond is False
    assert dec.decision == "remain_silent"
    assert dec.reason == "members_talking_silent"


@pytest.mark.automated
def test_prompt_safety_preserves_jarvis_persona_and_appends_rules() -> None:
    """Verify CRITICAL SAFETY RULE: Existing JARVIS persona & Web3 slang are preserved, new rules appended."""
    prompt = DEFAULT_ZOE_IDENTITY_PROMPT

    # 1. Preserved JARVIS & Web3 Persona
    assert "Web3 JARVIS" in prompt
    assert "Confident, witty, highly competent, slightly protective, and loyal like JARVIS" in prompt
    assert "GM, GN, WAGMI, FUD, wen, alpha, rug, DYOR, fr, ngl, degen" in prompt
    assert "NEVER say \"I am an AI\"" in prompt

    # 2. Appended Conversational Flow & Engagement Rule
    assert "10. Conversational Flow & Engagement:" in prompt
    assert "ask a follow-up question to keep the user engaged" in prompt

    # 3. Appended Honesty Rule
    assert "11. Absolute Honesty Regarding Delays:" in prompt
    assert "I missed that message, my apologies! Let me answer it now." in prompt

    # 4. Appended Plain Text Enforcement
    assert "12. Enforce Plain Text:" in prompt
    assert "Strictly NO Markdown" in prompt
