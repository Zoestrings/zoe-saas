"""Live delivery verification test suite for Stage 8."""

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
import sqlite3
from typing import Any, Dict

from zoe.conversation.classifier import ClassificationResult
from zoe.db.connections import open_operational_db
from zoe.escalation.delivery import deliver_notification
from zoe.escalation.handler import handle_escalation
from zoe.inbox.inbox_service import ensure_project_registered
from zoe.outbox.service import drain_outbox, enqueue_response
from zoe.participation.decision import should_respond
from zoe.settings import load_project_config, load_project_secrets
from zoe.telegram.adapter import PTBTelegramAdapter
from zoe.telegram.mock_adapter import MockTelegramAdapter
from zoe.telegram.normalizer import NormalizedMessage

PROJECT_ID = "live_test"


def setup_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "live_verification.db"
    conn = open_operational_db(db_path)
    schema_path = (
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "zoe"
        / "db"
        / "schema_operational.sql"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    ensure_project_registered(conn, PROJECT_ID)
    return conn


def insert_processing_inbox(conn: sqlite3.Connection, update_id: int, group_id: str, text: str = "Test message") -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, ?, ?, 'pseudo_user_test', ?, '2026-11-05 12:00:00', 'processing', '2026-11-05 12:00:00', '2026-11-05 12:00:00')
        RETURNING id
        """,
        (PROJECT_ID, update_id, group_id, update_id, text),
    )
    inbox_id = cur.fetchone()[0]
    conn.commit()
    return inbox_id


def get_live_adapter_or_skip():
    """Retrieve PTBTelegramAdapter if valid bot token and real chat IDs are present, else skip."""
    secrets = load_project_secrets(PROJECT_ID)
    bot_token = secrets.get("bot_token")
    if not bot_token or "YOUR" in bot_token:
        pytest.skip("Valid bot_token not found in config/secrets/live_test.secrets.yaml")

    config = load_project_config(PROJECT_ID)
    group_id = str(config.get("telegram", {}).get("group_id", ""))
    if not group_id or group_id.startswith("-100..."):
        pytest.skip("Live Telegram group_id not configured in config/projects/live_test.yaml")

    return PTBTelegramAdapter(bot_token), group_id, config.get("escalation", {}).get("moderator_group_id")


@pytest.mark.live_verification
def test_live_send_normal_and_reply(tmp_path: Path):
    """Verify live message sending to Telegram community group.
    
    Ensures message_id is returned from Telegram API and state transitions:
    outbox: pending -> sending -> sent (simulated=0)
    inbox: response_pending -> response_sent
    """
    adapter, group_id, _ = get_live_adapter_or_skip()
    conn = setup_db(tmp_path)
    inbox_id = insert_processing_inbox(conn, update_id=901, group_id=group_id, text="Hello Zoe live test")

    try:
        from zoe.llm.factory import get_llm_client
        llm = get_llm_client(PROJECT_ID)
        response_text = llm.generate(
            system_prompt="You are Zoe, a friendly, intelligent AI assistant.",
            user_prompt="Say a warm hello to the zoehackx community, introduce yourself briefly as Zoe, and tell a quick one-line tech or crypto joke! Keep it short and friendly.",
        )
    except Exception:
        response_text = "Hello everyone! 👋 I'm Zoe, your AI assistant. Happy to be here with the community!"

    outbox_id = enqueue_response(
        conn,
        project_id=PROJECT_ID,
        inbox_message_id=inbox_id,
        group_id=group_id,
        text=response_text,
        simulated=False,
    )

    delivered = asyncio.run(drain_outbox(conn, PROJECT_ID, adapter))
    assert delivered == 1

    cur = conn.cursor()
    cur.execute(
        "SELECT state, simulated, telegram_message_id, sent_at FROM outbox_messages WHERE id = ?",
        (outbox_id,),
    )
    st, sim, tg_id, sent_at = cur.fetchone()
    assert st == "sent"
    assert sim == 0
    assert tg_id is not None and tg_id > 0
    assert sent_at is not None

    # Verify inbox transitioned
    cur.execute("SELECT state FROM inbox_messages WHERE id = ?", (inbox_id,))
    assert cur.fetchone()[0] == "response_sent"
    conn.close()


@pytest.mark.live_verification
def test_live_send_moderator_notification(tmp_path: Path):
    """Verify live moderator notification sending.
    
    Ensures notification is sent to moderator group, state transitions to 'sent',
    escalation notification_status becomes 'delivered', but resolution_status
    strictly remains 'unresolved' (delivery is NOT acknowledgement).
    """
    adapter, _, mod_group_id = get_live_adapter_or_skip()
    config = load_project_config(PROJECT_ID)
    if not config.get("telegram", {}).get("live_send_moderator_notifications_enabled", False):
        pytest.skip("Moderator live notifications disabled in config/projects/live_test.yaml")
    if not mod_group_id or mod_group_id.startswith("-100..."):
        pytest.skip("Live moderator_group_id not configured in config/projects/live_test.yaml")

    conn = setup_db(tmp_path)
    inbox_id = insert_processing_inbox(
        conn, update_id=902, group_id="-100dummy", text="Someone hacked my account private key!"
    )

    # Trigger escalation with simulated=False
    esc_result = handle_escalation(
        inbox_row=inbox_id,
        severity="critical",
        reason="compromised_credentials",
        db_conns={"operational": conn},
        channel_id=mod_group_id,
        simulated=False,
    )

    assert esc_result.escalation_id is not None
    assert esc_result.notification_id is not None

    cur = conn.cursor()
    cur.execute(
        "SELECT state, simulated FROM moderator_notifications WHERE id = ?",
        (esc_result.notification_id,),
    )
    st, sim = cur.fetchone()
    assert st == "pending"
    assert sim == 0

    # Deliver via real adapter
    delivery_res = deliver_notification(
        notification_row=esc_result.notification_id,
        db_conn=conn,
        adapter=adapter,
    )

    assert delivery_res["state"] == "sent"
    assert delivery_res["notification_status"] == "delivered"
    assert delivery_res["telegram_message_id"] is not None and delivery_res["telegram_message_id"] > 0

    # Verify escalation row in database
    cur.execute(
        "SELECT notification_status, resolution_status FROM escalations WHERE id = ?",
        (esc_result.escalation_id,),
    )
    notif_st, res_st = cur.fetchone()
    assert notif_st == "delivered"
    # CRITICAL: Delivery does NOT mean acknowledged / resolved
    assert res_st == "unresolved"

    conn.close()


@pytest.mark.automated
def test_enforce_20s_rate_limit(tmp_path: Path):
    """Verify that a second message within the 20s cooldown is strictly blocked."""
    conn = setup_db(tmp_path)
    t0 = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)

    msg1 = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=1,
        group_id="-1001",
        telegram_message_id=1,
        pseudonymous_user_id="u1",
        text="zoe what is this project?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-05 12:00:00",
    )
    cls1 = ClassificationResult(category="direct_question", confidence=0.95, reason="direct_question")

    # First message: allowed
    d1 = should_respond(
        message=msg1,
        classification=cls1,
        last_response_time=None,
        current_time=t0,
        db_conn=conn,
    )
    assert d1.should_respond is True

    # Second message 5s later (within 20s cooldown): blocked
    t1 = t0 + timedelta(seconds=5)
    msg2 = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=2,
        group_id="-1001",
        telegram_message_id=2,
        pseudonymous_user_id="u2",
        text="zoe hello guys",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-05 12:00:05",
    )
    cls2 = ClassificationResult(category="casual", confidence=0.8, reason="casual")

    d2 = should_respond(
        message=msg2,
        classification=cls2,
        last_response_time=t0,
        current_time=t1,
        db_conn=conn,
    )
    assert d2.should_respond is False
    assert d2.reason == "rate_limit_cooldown"

    # Third message 25s later: allowed
    t2 = t0 + timedelta(seconds=25)
    msg3 = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=3,
        group_id="-1001",
        telegram_message_id=3,
        pseudonymous_user_id="u3",
        text="zoe how do I stake?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-05 12:00:25",
    )
    cls3 = ClassificationResult(category="direct_question", confidence=0.9, reason="direct_question")

    d3 = should_respond(
        message=msg3,
        classification=cls3,
        last_response_time=t0,
        current_time=t2,
        db_conn=conn,
    )
    assert d3.should_respond is True

    conn.close()


@pytest.mark.automated
def test_live_delivery_state_transitions_mock(tmp_path: Path):
    """Automated verification of live send state transitions and triggers using mock adapter.
    
    Verifies that with simulated=False:
    - outbox transitions to 'sent' and sets telegram_message_id
    - moderator_notifications transitions to 'sent' and sets telegram_message_id
    - escalations transitions notification_status to 'delivered' and preserves resolution_status='unresolved'
    """
    conn = setup_db(tmp_path)
    inbox_id = insert_processing_inbox(conn, update_id=1, group_id="-1001")
    adapter = MockTelegramAdapter()

    # 1. Outbox live send
    outbox_id = enqueue_response(
        conn,
        project_id=PROJECT_ID,
        inbox_message_id=inbox_id,
        group_id="-1001",
        text="Live outbox response",
        simulated=False,
    )
    delivered = asyncio.run(drain_outbox(conn, PROJECT_ID, adapter))
    assert delivered == 1

    cur = conn.cursor()
    cur.execute("SELECT state, simulated, telegram_message_id FROM outbox_messages WHERE id = ?", (outbox_id,))
    st, sim, tg_id = cur.fetchone()
    assert st == "sent"
    assert sim == 0
    assert tg_id == 1

    # 2. Moderator notification live send
    inbox_esc_id = insert_processing_inbox(conn, update_id=2, group_id="-1001", text="hacked account")
    esc_result = handle_escalation(
        inbox_row=inbox_esc_id,
        severity="critical",
        reason="compromised_credentials",
        db_conns={"operational": conn},
        channel_id="-100mod",
        simulated=False,
    )
    assert esc_result.notification_id is not None

    deliv_res = deliver_notification(
        notification_row=esc_result.notification_id,
        db_conn=conn,
        adapter=adapter,
    )
    assert deliv_res["state"] == "sent"
    assert deliv_res["notification_status"] == "delivered"

    cur.execute(
        "SELECT notification_status, resolution_status FROM escalations WHERE id = ?",
        (esc_result.escalation_id,),
    )
    notif_st, res_st = cur.fetchone()
    assert notif_st == "delivered"
    assert res_st == "unresolved"

    conn.close()
