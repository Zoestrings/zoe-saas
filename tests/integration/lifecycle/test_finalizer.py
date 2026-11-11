from datetime import timedelta
from pathlib import Path
import pytest
import sqlite3

from zoe.clock.clock import format_timestamp, now
from zoe.db.connections import open_operational_db
from zoe.finalizer.sweep import sweep_finalizer
from zoe.inbox.inbox_service import ensure_project_registered

PROJECT_ID = "finalizer_proj"
GROUP_ID = "-1001234567890"


def setup_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "finalizer_test.db"
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
    ensure_project_registered(conn, PROJECT_ID)
    return conn


def insert_inbox(
    conn: sqlite3.Connection,
    update_id: int,
    state: str = "response_sent",
    age_seconds: int = 60,
) -> int:
    ts = format_timestamp(now() - timedelta(seconds=age_seconds))
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, ?, ?, 'pseudo', 'text', ?, ?, ?, ?)
        RETURNING id
        """,
        (PROJECT_ID, update_id, GROUP_ID, update_id, ts, state, ts, ts),
    )
    inbox_id = cur.fetchone()[0]
    conn.commit()
    return inbox_id


def insert_outbox(
    conn: sqlite3.Connection,
    inbox_id: int,
    state: str = "sent",
    simulated: int = 0,
) -> int:
    ts = format_timestamp(now())
    tg_id = 99999 if state == "sent" else None
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO outbox_messages (
            project_id, inbox_message_id, group_id, text, simulated,
            state, telegram_message_id, created_at, state_changed_at
        ) VALUES (?, ?, ?, 'outbox response', ?, ?, ?, ?, ?)
        RETURNING id
        """,
        (PROJECT_ID, inbox_id, GROUP_ID, simulated, state, tg_id, ts, ts),
    )
    outbox_id = cur.fetchone()[0]
    conn.commit()
    return outbox_id


@pytest.mark.automated
def test_finalizer_reconciliation_missing_outbox(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    inbox_id = insert_inbox(conn, update_id=101, state="response_sent", age_seconds=45)

    res = sweep_finalizer(conn, PROJECT_ID, threshold_seconds=30)
    assert res.completed_count == 0
    assert res.investigation_count == 1

    cur = conn.cursor()
    cur.execute(
        "SELECT state, investigation_reason FROM inbox_messages WHERE id = ?",
        (inbox_id,),
    )
    row = cur.fetchone()
    assert row[0] == "needs_investigation"
    assert row[1] is not None
    assert "Missing outbox message" in row[1]

    conn.close()


@pytest.mark.automated
def test_finalizer_reconciliation_valid(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    
    # 1. Real sent message
    inbox_real = insert_inbox(conn, update_id=201, state="response_sent", age_seconds=50)
    insert_outbox(conn, inbox_real, state="sent", simulated=0)

    # 2. Simulated delivered message
    inbox_sim = insert_inbox(conn, update_id=202, state="response_sent", age_seconds=50)
    insert_outbox(conn, inbox_sim, state="simulated_delivered", simulated=1)

    # 3. Message not older than threshold (e.g. 5 seconds old)
    inbox_recent = insert_inbox(conn, update_id=203, state="response_sent", age_seconds=5)
    insert_outbox(conn, inbox_recent, state="sent", simulated=0)

    res = sweep_finalizer(conn, PROJECT_ID, threshold_seconds=30)
    assert res.completed_count == 2
    assert res.investigation_count == 0

    cur = conn.cursor()
    cur.execute("SELECT state FROM inbox_messages WHERE id = ?", (inbox_real,))
    assert cur.fetchone()[0] == "completed"

    cur.execute("SELECT state FROM inbox_messages WHERE id = ?", (inbox_sim,))
    assert cur.fetchone()[0] == "completed"

    # Recent row should remain response_sent
    cur.execute("SELECT state FROM inbox_messages WHERE id = ?", (inbox_recent,))
    assert cur.fetchone()[0] == "response_sent"

    conn.close()


@pytest.mark.automated
def test_finalizer_reconciliation_invalid_outbox_state(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    inbox_id = insert_inbox(conn, update_id=301, state="response_sent", age_seconds=40)
    # Outbox message in pending state
    insert_outbox(conn, inbox_id, state="pending", simulated=0)

    res = sweep_finalizer(conn, PROJECT_ID, threshold_seconds=30)
    assert res.completed_count == 0
    assert res.investigation_count == 1

    cur = conn.cursor()
    cur.execute("SELECT state, investigation_reason FROM inbox_messages WHERE id = ?", (inbox_id,))
    st, reason = cur.fetchone()
    assert st == "needs_investigation"
    assert "pending" in reason

    conn.close()

