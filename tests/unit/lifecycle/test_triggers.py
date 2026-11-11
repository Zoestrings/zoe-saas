from pathlib import Path
import pytest
import sqlite3

from zoe.db.connections import open_operational_db
from zoe.inbox.inbox_service import ensure_project_registered

PROJECT_ID = "trigger_proj"


def setup_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "trigger_test.db"
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


def insert_test_inbox(conn: sqlite3.Connection, msg_id: int) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, '-100', ?, 'pseudo', 'text', '2026-11-05 00:00:00', 'message_persisted', '2026-11-05 00:00:00', '2026-11-05 00:00:00')
        RETURNING id
        """,
        (PROJECT_ID, msg_id, msg_id),
    )
    inbox_id = cur.fetchone()[0]
    conn.commit()
    return inbox_id


@pytest.mark.automated
def test_trigger_enforcement_sent_requires_real(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    inbox_id = insert_test_inbox(conn, 100)
    cur = conn.cursor()

    # Insert a simulated sending outbox message
    cur.execute(
        """
        INSERT INTO outbox_messages (
            project_id, inbox_message_id, group_id, text, simulated, state, state_changed_at, created_at
        ) VALUES (?, ?, '-100', 'hello', 1, 'sending', '2026-11-05 00:00:00', '2026-11-05 00:00:00')
        RETURNING id
        """,
        (PROJECT_ID, inbox_id),
    )
    outbox_id = cur.fetchone()[0]
    conn.commit()

    # Direct SQL UPDATE setting state='sent' when simulated=1 must be rejected by trigger
    with pytest.raises(sqlite3.IntegrityError) as exc_info:
        cur.execute(
            "UPDATE outbox_messages SET state = 'sent' WHERE id = ?",
            (outbox_id,),
        )
    assert "state sent requires simulated=0" in str(exc_info.value)

    # Direct INSERT of state='sent' with simulated=1 must also be rejected
    inbox_id2 = insert_test_inbox(conn, 101)
    with pytest.raises(sqlite3.IntegrityError) as exc_info:
        cur.execute(
            """
            INSERT INTO outbox_messages (
                project_id, inbox_message_id, group_id, text, simulated, state, state_changed_at, created_at
            ) VALUES (?, ?, '-100', 'hello', 1, 'sent', '2026-11-05 00:00:00', '2026-11-05 00:00:00')
            """,
            (PROJECT_ID, inbox_id2),
        )
    assert "state sent requires simulated=0" in str(exc_info.value)

    conn.close()


@pytest.mark.automated
def test_trigger_simulated_flag_write_once(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    inbox_id = insert_test_inbox(conn, 200)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO outbox_messages (
            project_id, inbox_message_id, group_id, text, simulated, state, state_changed_at, created_at
        ) VALUES (?, ?, '-100', 'msg', 1, 'pending', '2026-11-05 00:00:00', '2026-11-05 00:00:00')
        RETURNING id
        """,
        (PROJECT_ID, inbox_id),
    )
    outbox_id = cur.fetchone()[0]
    conn.commit()

    # Modifying simulated flag must be rejected by trigger
    with pytest.raises(sqlite3.IntegrityError) as exc_info:
        cur.execute(
            "UPDATE outbox_messages SET simulated = 0 WHERE id = ?",
            (outbox_id,),
        )
    assert "simulated flag is write-once" in str(exc_info.value)

    conn.close()


@pytest.mark.automated
def test_trigger_simulated_delivered_requires_simulated(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    inbox_id = insert_test_inbox(conn, 300)
    cur = conn.cursor()

    # Non-simulated (real) message in sending state
    cur.execute(
        """
        INSERT INTO outbox_messages (
            project_id, inbox_message_id, group_id, text, simulated, state, state_changed_at, created_at
        ) VALUES (?, ?, '-100', 'msg', 0, 'sending', '2026-11-05 00:00:00', '2026-11-05 00:00:00')
        RETURNING id
        """,
        (PROJECT_ID, inbox_id),
    )
    outbox_id = cur.fetchone()[0]
    conn.commit()

    # Cannot set simulated_delivered when simulated=0
    with pytest.raises(sqlite3.IntegrityError) as exc_info:
        cur.execute(
            "UPDATE outbox_messages SET state = 'simulated_delivered' WHERE id = ?",
            (outbox_id,),
        )
    assert "state simulated_delivered requires simulated=1" in str(exc_info.value)

    conn.close()


@pytest.mark.automated
def test_trigger_inbox_attempt_cap(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    inbox_id = insert_test_inbox(conn, 400)
    cur = conn.cursor()

    with pytest.raises(sqlite3.IntegrityError) as exc_info:
        cur.execute(
            "UPDATE inbox_messages SET attempt_count = 6 WHERE id = ?",
            (inbox_id,),
        )
    assert "attempt_count cannot exceed 5" in str(exc_info.value) or "CHECK" in str(exc_info.value)

    conn.close()

