import asyncio
from pathlib import Path
import pytest
import sqlite3

from zoe.db.connections import open_operational_db
from zoe.inbox.inbox_service import ensure_project_registered
from zoe.outbox.service import drain_outbox, enqueue_response
from zoe.telegram.mock_adapter import MockTelegramAdapter

PROJECT_ID = "outbox_proj"
GROUP_ID = "-1001234567890"


def setup_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "outbox_test.db"
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


def insert_processing_inbox(conn: sqlite3.Connection, update_id: int) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, ?, ?, 'pseudo', 'text', '2026-11-05 00:00:00', 'processing', '2026-11-05 00:00:00', '2026-11-05 00:00:00')
        RETURNING id
        """,
        (PROJECT_ID, update_id, GROUP_ID, update_id),
    )
    inbox_id = cur.fetchone()[0]
    conn.commit()
    return inbox_id


@pytest.mark.automated
def test_simulated_delivery(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    inbox_id = insert_processing_inbox(conn, 1)

    # Enqueue response with simulated=True
    outbox_id = enqueue_response(
        conn,
        project_id=PROJECT_ID,
        inbox_message_id=inbox_id,
        group_id=GROUP_ID,
        text="Simulated response",
        simulated=True,
    )

    cur = conn.cursor()
    cur.execute("SELECT state FROM inbox_messages WHERE id = ?", (inbox_id,))
    assert cur.fetchone()[0] == "response_pending"

    # Drain outbox
    adapter = MockTelegramAdapter()
    delivered = asyncio.run(drain_outbox(conn, PROJECT_ID, adapter))
    assert delivered == 1

    # Verify outbox records simulated_delivered and NEVER sent
    cur.execute("SELECT state, simulated FROM outbox_messages WHERE id = ?", (outbox_id,))
    st, sim = cur.fetchone()
    assert st == "simulated_delivered"
    assert sim == 1
    assert st != "sent"

    # Verify inbox transitioned to response_sent
    cur.execute("SELECT state FROM inbox_messages WHERE id = ?", (inbox_id,))
    assert cur.fetchone()[0] == "response_sent"

    conn.close()


@pytest.mark.automated
def test_real_delivery_records_sent(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    inbox_id = insert_processing_inbox(conn, 2)

    outbox_id = enqueue_response(
        conn,
        project_id=PROJECT_ID,
        inbox_message_id=inbox_id,
        group_id=GROUP_ID,
        text="Real delivery response",
        simulated=False,
    )

    adapter = MockTelegramAdapter()
    delivered = asyncio.run(drain_outbox(conn, PROJECT_ID, adapter))
    assert delivered == 1

    cur = conn.cursor()
    cur.execute("SELECT state, simulated, telegram_message_id FROM outbox_messages WHERE id = ?", (outbox_id,))
    st, sim, tg_id = cur.fetchone()
    assert st == "sent"
    assert sim == 0
    assert tg_id is not None

    cur.execute("SELECT state FROM inbox_messages WHERE id = ?", (inbox_id,))
    assert cur.fetchone()[0] == "response_sent"

    conn.close()

