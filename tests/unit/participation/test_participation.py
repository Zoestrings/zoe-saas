from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from zoe.conversation.classifier import ClassificationResult
from zoe.db.connections import open_operational_db
from zoe.participation.decision import should_respond
from zoe.telegram.normalizer import NormalizedMessage


@pytest.fixture
def op_db(tmp_path: Path):
    db_path = tmp_path / "operational.db"
    conn = open_operational_db(db_path)
    schema_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "zoe"
        / "db"
        / "schema_operational.sql"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.execute(
        "INSERT INTO projects (project_id, name, telegram_group_id, config_json, created_at, active) VALUES ('p1', 'Test', '-1001', '{}', '2026-01-01 00:00:00', 1)"
    )
    conn.commit()
    return conn


@pytest.mark.automated
def test_participation_casual_chat_silent(op_db) -> None:
    """Zoe remains silent during unaddressed casual chat."""
    msg = NormalizedMessage(
        project_id="p1",
        telegram_update_id=1,
        group_id="-1001",
        telegram_message_id=101,
        pseudonymous_user_id="u1",
        text="gm everyone!",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-05 12:00:00",
    )
    cls = ClassificationResult(category="casual", confidence=0.9, reason="casual")
    dec = should_respond(msg, cls, db_conn=op_db)

    assert not dec.should_respond
    assert dec.decision == "remain_silent"
    assert dec.reason == "casual_unaddressed"

    # Confirm logged to participation_log
    cur = op_db.execute("SELECT decision, reason_code FROM participation_log WHERE telegram_message_id = 101")
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "remain_silent"
    assert row[1] == "casual_unaddressed"


@pytest.mark.automated
def test_participation_direct_question_responds(op_db) -> None:
    """Zoe responds to direct questions."""
    msg = NormalizedMessage(
        project_id="p1",
        telegram_update_id=2,
        group_id="-1001",
        telegram_message_id=102,
        pseudonymous_user_id="u2",
        text="What is the unbonding period for staking?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-05 12:00:00",
    )
    cls = ClassificationResult(category="direct_question", confidence=0.95, reason="question")
    dec = should_respond(msg, cls, db_conn=op_db)

    assert dec.should_respond
    assert dec.decision == "respond"


@pytest.mark.automated
def test_participation_enforces_twenty_second_rate_limit(op_db) -> None:
    """Enforces per-group 20-second cooldown rate limit."""
    t0 = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)
    last_resp = t0

    msg = NormalizedMessage(
        project_id="p1",
        telegram_update_id=3,
        group_id="-1001",
        telegram_message_id=103,
        pseudonymous_user_id="u3",
        text="Where are the docs?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-05 12:00:10",
    )
    cls = ClassificationResult(category="direct_question", confidence=0.9, reason="question")

    # 10 seconds later (< 20s): must be silenced by rate limit
    t_attempt = t0 + timedelta(seconds=10)
    dec = should_respond(
        msg,
        cls,
        last_response_time=last_resp,
        current_time=t_attempt,
        db_conn=op_db,
    )
    assert not dec.should_respond
    assert dec.decision == "remain_silent"
    assert dec.reason == "rate_limit_cooldown"
    assert dec.cooldown_remaining_seconds == 10.0

    # 25 seconds later (> 20s): responds
    t_after = t0 + timedelta(seconds=25)
    dec2 = should_respond(
        msg,
        cls,
        last_response_time=last_resp,
        current_time=t_after,
        db_conn=op_db,
    )
    assert dec2.should_respond
    assert dec2.decision == "respond"


@pytest.mark.automated
def test_participation_responds_to_mentions_on_any_topic(op_db) -> None:
    """Zoe responds to any message directly tagging/mentioning her, even off-topic/casual."""
    msg = NormalizedMessage(
        project_id="p1",
        telegram_update_id=4,
        group_id="-1001",
        telegram_message_id=104,
        pseudonymous_user_id="u4",
        text="Hey @Zoe tell me a joke!",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-05 12:00:00",
    )
    cls = ClassificationResult(category="irrelevant", confidence=0.8, reason="off_topic")
    dec = should_respond(msg, cls, db_conn=op_db)

    assert dec.should_respond is True
    assert dec.decision == "respond"
    assert dec.reason == "general_chat_addressed"


@pytest.mark.automated
def test_participation_responds_to_replies_to_zoe(op_db) -> None:
    """Zoe responds to direct replies to her previous messages."""
    msg = NormalizedMessage(
        project_id="p1",
        telegram_update_id=5,
        group_id="-1001",
        telegram_message_id=105,
        pseudonymous_user_id="u5",
        text="what do you mean by that?",
        reply_to_message_id=99,
        is_forward=False,
        timestamp="2026-11-05 12:00:00",
    )
    cls = ClassificationResult(category="casual", confidence=0.75, reason="follow_up")
    dec = should_respond(msg, cls, recent_zoe_messages=[99], db_conn=op_db)

    assert dec.should_respond is True
    assert dec.decision == "respond"
    assert dec.reason == "casual_addressed"
