from pathlib import Path
import pytest
import sqlite3

from zoe.db.connections import open_operational_db
from zoe.inbox.inbox_service import ensure_project_registered
from zoe.inbox.lifecycle import transition, validate_transition
from zoe.utils.errors import InvalidTransitionError

PROJECT_ID = "transition_proj"


def setup_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "trans.db"
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


@pytest.mark.automated
def test_invalid_transition(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, 1, '-100', 10, 'pseudo1', 'test', '2026-11-05 00:00:00', 'message_persisted', '2026-11-05 00:00:00', '2026-11-05 00:00:00')
        RETURNING id
        """,
        (PROJECT_ID,),
    )
    inbox_id = cur.fetchone()[0]
    conn.commit()

    # Direct jump from message_persisted to response_sent must raise InvalidTransitionError
    with pytest.raises(InvalidTransitionError):
        transition(conn, inbox_id, "response_sent")

    # In-memory validation check
    with pytest.raises(InvalidTransitionError):
        validate_transition("message_persisted", "response_sent")

    conn.close()


@pytest.mark.automated
def test_allowed_transitions_succeed(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, 2, '-100', 20, 'pseudo2', 'test', '2026-11-05 00:00:00', 'message_persisted', '2026-11-05 00:00:00', '2026-11-05 00:00:00')
        RETURNING id
        """,
        (PROJECT_ID,),
    )
    inbox_id = cur.fetchone()[0]
    conn.commit()

    # Step: message_persisted -> processing
    transition(conn, inbox_id, "processing")
    cur.execute("SELECT state FROM inbox_messages WHERE id = ?", (inbox_id,))
    assert cur.fetchone()[0] == "processing"

    # Step: processing -> no_response_required
    transition(conn, inbox_id, "no_response_required")
    cur.execute("SELECT state FROM inbox_messages WHERE id = ?", (inbox_id,))
    assert cur.fetchone()[0] == "no_response_required"

    conn.close()

