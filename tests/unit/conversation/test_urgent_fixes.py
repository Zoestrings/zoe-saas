"""Unit tests verifying Urgent Fixes: Glitchy Replies, Context Failure, and Strict Rate Limiting.

Tests:
- Test A: A message "@humanUser I know you are enjoying the bot" does NOT trigger a response from Zoe.
- Test B: A response is fully complete and does not end abruptly (min 300 tokens enforced, finished sentences).
- Test C: Zoe cannot send two messages within 20 seconds.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from zoe.conversation.classifier import ClassificationResult, classify_message
from zoe.conversation.intent import detect_intent, is_tagging_other_human
from zoe.conversation.prompt_builder import DEFAULT_ZOE_IDENTITY_PROMPT
from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.llm.mock import MockLLMClient
from zoe.llm.providers.groq_provider import GroqProvider
from zoe.participation.decision import should_respond
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.pipeline import process_message

PROJECT_ID = "p_urgent_fix"
GROUP_ID = "-100999"


@pytest.fixture
def urgent_env(tmp_path: Path):
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
        VALUES (?, 'Urgent Test', ?, '{"modules": {"crypto_intelligence": true, "community_intelligence": true, "community_manager": true}}', '2026-01-01 00:00:00', 1)
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


# Test A: A message "@humanUser I know you are enjoying the bot" does NOT trigger a response from Zoe
def test_human_to_human_tag_does_not_trigger_response(urgent_env):
    """Verify messages tagging other human community members classify as casual_chat and remain silent."""
    conns = urgent_env["conns"]
    conn_op = conns["operational"]
    mem_path = urgent_env["mem_path"]

    raw_text = "@humanUser I know you are enjoying the bot"

    # 1. Detection verifies human tagging
    assert is_tagging_other_human(raw_text) is True

    # 2. Intent classifier routes to casual_chat
    intent_res = detect_intent(raw_text)
    assert intent_res.intent == "casual_chat"

    # 3. Decision engine enforces strict silence for human-to-human conversational chat
    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=1,
        group_id=GROUP_ID,
        telegram_message_id=101,
        pseudonymous_user_id="alice",
        text=raw_text,
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-09 15:00:00",
    )
    cls = classify_message(raw_text)
    dec = should_respond(msg, cls, db_conn=conn_op)

    assert dec.should_respond is False
    assert dec.decision == "remain_silent"
    assert dec.reason == "casual_unaddressed"

    # 4. Pipeline execution leaves outbox empty and returns responded=False
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 1, ?, 101, 'alice', ?, 0, 'message_persisted', '2026-11-09 15:00:00', '2026-11-09 15:00:00', '2026-11-09 15:00:00')
        """,
        (PROJECT_ID, GROUP_ID, raw_text),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    res = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        mem_db_path=mem_path,
        simulated=True,
    )
    assert res.responded is False
    assert res.decision.decision == "remain_silent"


# Test B: A response is fully complete and does not end abruptly
def test_response_max_tokens_enforced_and_no_over_apology(monkeypatch):
    """Verify GroqProvider enforces max_tokens>=300 and prompt builder bans over-apologies."""
    # 1. GroqProvider enforces at least 300 tokens in payload
    captured_payload = {}

    class MockGroqResponse:
        status_code = 200

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "GM! Everything is running smoothly and all systems are verified."
                        }
                    }
                ]
            }

        def raise_for_status(self):
            pass

    def mock_post(url, json=None, headers=None, **kwargs):
        captured_payload.update(json)
        return MockGroqResponse()

    provider = GroqProvider(api_key="gsk_test")
    monkeypatch.setattr("httpx.Client.post", lambda self, url, **kwargs: mock_post(url, **kwargs))

    # Even if caller passes a small max_tokens (e.g. 100 or 150), provider enforces >= 300
    res = provider.generate(
        system_prompt="You are Zoe.",
        user_prompt="Status update please",
        max_tokens=150,
    )
    assert captured_payload.get("max_tokens") >= 300
    assert res.endswith(".") or res.endswith("!") or res.endswith("?")

    # 2. Over-apologizing ban in prompt identity
    assert "No Over-Apologizing" in DEFAULT_ZOE_IDENTITY_PROMPT
    assert "Do not apologize for being slow" in DEFAULT_ZOE_IDENTITY_PROMPT
    assert "Do not start your responses with 'I hear you' or 'I'm sorry'" in DEFAULT_ZOE_IDENTITY_PROMPT


# Test C: Zoe cannot send two messages within 20 seconds
def test_zoe_cannot_send_two_messages_within_twenty_seconds(urgent_env):
    """Verify strict global 20-second rate limit lock prevents double-texting."""
    conns = urgent_env["conns"]
    conn_op = conns["operational"]

    t0 = datetime(2026, 11, 9, 15, 0, 0, tzinfo=timezone.utc)

    # 10 seconds later (< 20s): Zoe must be silenced regardless of message or intent
    t_10s = t0 + timedelta(seconds=10)

    test_queries = [
        "What is the price of the token?",  # price query
        "really?",                          # follow-up reaction
        "0x71C84166b3A747153e32d1440C7338837F7bbE79",  # CA detection
        "What is Hummingbird all about?",  # direct question
    ]

    for q in test_queries:
        msg = NormalizedMessage(
            project_id=PROJECT_ID,
            telegram_update_id=2,
            group_id=GROUP_ID,
            telegram_message_id=202,
            pseudonymous_user_id="bob",
            text=q,
            reply_to_message_id=None,
            is_forward=False,
            timestamp=t_10s.strftime("%Y-%m-%d %H:%M:%S"),
        )
        cls = classify_message(q)
        dec = should_respond(
            message=msg,
            classification=cls,
            last_response_time=t0,
            current_time=t_10s,
            db_conn=conn_op,
            rate_limit_seconds=20.0,
        )

        assert dec.should_respond is False
        assert dec.decision == "remain_silent"
        assert dec.reason == "rate_limit_cooldown"
        assert dec.cooldown_remaining_seconds == 10.0

    # 22 seconds later (> 20s): Rate limit has cleared, response allowed
    t_22s = t0 + timedelta(seconds=22)
    msg_allowed = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=3,
        group_id=GROUP_ID,
        telegram_message_id=203,
        pseudonymous_user_id="bob",
        text="What is Hummingbird all about?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp=t_22s.strftime("%Y-%m-%d %H:%M:%S"),
    )
    cls_allowed = classify_message(msg_allowed.text)
    dec_allowed = should_respond(
        message=msg_allowed,
        classification=cls_allowed,
        last_response_time=t0,
        current_time=t_22s,
        db_conn=conn_op,
        rate_limit_seconds=20.0,
    )
    assert dec_allowed.should_respond is True
    assert dec_allowed.decision == "respond"

