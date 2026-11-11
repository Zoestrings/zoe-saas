"""Unit tests verifying short-term conversational memory, natural greetings, and follow-up flow."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import pytest

from zoe.conversation.classifier import classify_message
from zoe.conversation.prompt_builder import DEFAULT_ZOE_IDENTITY_PROMPT, build_prompt
from zoe.conversation.router import route_intent
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
from zoe.participation.decision import should_respond
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.pipeline import process_message

PROJECT_ID = "p_flow"
GROUP_ID = "-100777"


@pytest.fixture
def flow_env(tmp_path: Path):
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
        VALUES (?, 'Flow Test', ?, '{"token_address": "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf", "participation": {"respond_to_casual": true}}', '2026-01-01 00:00:00', 1)
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


def test_get_recent_conversation_history(flow_env):
    """Verify get_recent_conversation_history returns attributed user and Zoe turns."""
    mem_path = flow_env["mem_path"]

    record_community_message(
        project_id=PROJECT_ID,
        group_id=GROUP_ID,
        telegram_message_id=1,
        pseudonymous_user_id="user_alice",
        content="hey",
        received_at="2026-11-08 10:00:00",
        db_path=mem_path,
    )
    record_community_message(
        project_id=PROJECT_ID,
        group_id=GROUP_ID,
        telegram_message_id=0,
        pseudonymous_user_id="zoe",
        content="Hey! How is it going? Need an update on Hummingbird, or just checking in?",
        received_at="2026-11-08 10:00:01",
        db_path=mem_path,
    )
    record_community_message(
        project_id=PROJECT_ID,
        group_id=GROUP_ID,
        telegram_message_id=2,
        pseudonymous_user_id="user_alice",
        content="what is the price of fly?",
        received_at="2026-11-08 10:00:05",
        db_path=mem_path,
    )
    record_community_message(
        project_id=PROJECT_ID,
        group_id=GROUP_ID,
        telegram_message_id=0,
        pseudonymous_user_id="zoe",
        content="The current price of $FLY is $0.0024 USD with $93,712 in liquidity.",
        received_at="2026-11-08 10:00:06",
        db_path=mem_path,
    )

    history = get_recent_conversation_history(
        project_id=PROJECT_ID,
        group_id=GROUP_ID,
        limit=6,
        db_path=mem_path,
    )

    assert len(history) == 4
    assert history[0] == "User: hey"
    assert "Zoe: Hey! How is it going?" in history[1]
    assert history[2] == "User: what is the price of fly?"
    assert "Zoe: The current price of $FLY is $0.0024 USD" in history[3]


def test_prompt_builder_injects_conversation_history():
    """Verify build_prompt formats [CONVERSATION HISTORY] tag with attributed lines."""
    msg = NormalizedMessage(
        project_id="p1",
        telegram_update_id=10,
        group_id="-1001",
        telegram_message_id=10,
        pseudonymous_user_id="user_bob",
        text="really?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-08 10:00:10",
    )
    history = [
        "User: what is the price of hummingbird?",
        "Zoe: The current price of $FLY is $0.0024 USD with $93,712 in liquidity.",
    ]

    prompt = build_prompt(
        message=msg,
        community_context=[],
        official_chunks=[],
        conversation_history=history,
    )

    assert "[CONVERSATION HISTORY]" in prompt
    assert "User: what is the price of hummingbird?" in prompt
    assert "Zoe: The current price of $FLY is $0.0024 USD" in prompt
    assert "[USER INCOMING MESSAGE]\nUser: really?" in prompt


def test_follow_up_bypasses_group_cooldown(flow_env):
    """Verify follow-up questions respect the strict 20-second rate limit cooldown."""
    conn_op = flow_env["conns"]["operational"]
    t0 = datetime(2026, 11, 8, 10, 0, 0, tzinfo=timezone.utc)

    # User sends follow-up confirmation 3 seconds after Zoe spoke (< 20s cooldown)
    t_msg = t0 + timedelta(seconds=3)
    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=5,
        group_id=GROUP_ID,
        telegram_message_id=505,
        pseudonymous_user_id="user_alice",
        text="really?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp=t_msg.strftime("%Y-%m-%d %H:%M:%S"),
    )

    cls = classify_message(msg.text)
    assert cls.category == "direct_question"
    assert cls.reason == "follow_up_confirmation"

    dec = should_respond(
        message=msg,
        classification=cls,
        last_response_time=t0,
        current_time=t_msg,
        db_conn=conn_op,
        rate_limit_seconds=20.0,
    )

    # Under strict 20-second global rate limit lock: silenced by cooldown
    assert dec.should_respond is False
    assert dec.decision == "remain_silent"
    assert dec.reason == "rate_limit_cooldown"

    # After cooldown has elapsed (25 seconds later), responds with follow_up_answered
    t_after = t0 + timedelta(seconds=25)
    dec_after = should_respond(
        message=msg,
        classification=cls,
        last_response_time=t0,
        current_time=t_after,
        db_conn=conn_op,
        rate_limit_seconds=20.0,
    )
    assert dec_after.should_respond is True
    assert dec_after.decision == "respond"
    assert dec_after.reason == "follow_up_answered"


def test_multi_turn_conversational_flow_end_to_end(flow_env):
    """Simulate exact conversation:
    1. User: 'hey' -> Zoe greets warmly without robotic phrases.
    2. User: 'what is the price of fly?' -> Zoe replies with price.
    3. User: 'really?' within 3 seconds -> Zoe understands follow-up context and confirms confidently.
    """
    conns = flow_env["conns"]
    conn_op = conns["operational"]
    conn_mem = conns["memory"]
    conn_mem.execute("DELETE FROM community_messages")
    conn_mem.commit()
    mem_path = flow_env["mem_path"]
    llm_client = MockLLMClient()

    # --- Turn 1: Casual greeting 'hey' ---
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 1, ?, 101, 'user_1', 'hey', 0, 'message_persisted', '2026-11-08 10:00:00', '2026-11-08 10:00:00', '2026-11-08 10:00:00')
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
    assert res_1.decision.reason == "casual_answered"
    assert "Hey!" in res_1.response_text
    assert "I don't have a physical space" not in res_1.response_text
    assert "I am an AI" not in res_1.response_text

    # --- Turn 2: User asks for token price ---
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 2, ?, 102, 'user_1', 'what is the price of fly?', 0, 'message_persisted', '2026-11-08 10:00:25', '2026-11-08 10:00:25', '2026-11-08 10:00:25')
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
    assert "$FLY" in res_2.response_text or "price" in res_2.response_text.lower()

    # --- Turn 3: User follows up with 'really?' after cooldown has elapsed ---
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 3, ?, 103, 'user_1', 'really?', 0, 'message_persisted', '2026-11-08 10:00:50', '2026-11-08 10:00:50', '2026-11-08 10:00:50')
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

    # Must respond to follow-up without being silenced
    assert res_3.responded is True
    assert res_3.decision.decision == "respond"
    assert res_3.decision.reason == "follow_up_answered"
    assert "Yes, really!" in res_3.response_text

    # Verify that the LLM was given [CONVERSATION HISTORY] containing the previous turns
    last_call = llm_client.calls[-1]
    prompt_sent = last_call["user_prompt"]
    assert "[CONVERSATION HISTORY]" in prompt_sent
    assert "what is the price of fly?" in prompt_sent
    assert "[USER INCOMING MESSAGE]\nUser: really?" in prompt_sent
