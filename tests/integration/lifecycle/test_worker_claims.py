from datetime import timedelta
from pathlib import Path
import pytest
import sqlite3

from zoe.clock.clock import FakeClock, format_timestamp, now, set_clock, Clock
from zoe.db.connections import open_operational_db
from zoe.inbox.inbox_service import ensure_project_registered
from zoe.worker.claim import (
    calculate_next_attempt_at,
    claim_next_inbox_row,
    record_worker_failure,
)

PROJECT_ID = "claim_proj"


def setup_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "claim_test.db"
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


def insert_inbox_msg(conn: sqlite3.Connection, update_id: int, attempt_count: int = 0, state: str = "message_persisted") -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at,
            attempt_count, created_at
        ) VALUES (?, ?, '-100', ?, 'pseudo', 'text', '2026-11-05 00:00:00', ?, '2026-11-05 00:00:00', ?, '2026-11-05 00:00:00')
        RETURNING id
        """,
        (PROJECT_ID, update_id, update_id, state, attempt_count),
    )
    row_id = cur.fetchone()[0]
    conn.commit()
    return row_id


@pytest.mark.automated
def test_atomic_claims(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    inbox_id = insert_inbox_msg(conn, 1)

    # Worker 1 claims
    claimed1 = claim_next_inbox_row(conn, PROJECT_ID, worker_id="worker_1")
    assert claimed1 is not None
    assert claimed1["id"] == inbox_id
    assert claimed1["lease_owner"] == "worker_1"
    assert claimed1["state"] == "processing"
    assert claimed1["attempt_count"] == 1

    # Worker 2 attempts to claim while lease is active
    claimed2 = claim_next_inbox_row(conn, PROJECT_ID, worker_id="worker_2")
    assert claimed2 is None  # Row is leased, cannot be claimed by worker 2

    conn.close()


@pytest.mark.automated
def test_retry_cap(tmp_path: Path) -> None:
    conn = setup_db(tmp_path)
    # Row with attempt_count=5 already reached max attempts
    insert_inbox_msg(conn, 2, attempt_count=5, state="failed")

    # Cannot be claimed
    claimed = claim_next_inbox_row(conn, PROJECT_ID, worker_id="worker_1")
    assert claimed is None

    # Test record_worker_failure transitions to dead_letter at 5 attempts
    inbox_id = insert_inbox_msg(conn, 3, attempt_count=4, state="message_persisted")
    # Claim will increment attempt to 5
    claimed = claim_next_inbox_row(conn, PROJECT_ID, worker_id="worker_1")
    assert claimed["attempt_count"] == 5

    resulting_state = record_worker_failure(conn, inbox_id, "Max attempts reached")
    assert resulting_state == "dead_letter"

    cur = conn.cursor()
    cur.execute("SELECT state, failure_reason FROM inbox_messages WHERE id = ?", (inbox_id,))
    st, reason = cur.fetchone()
    assert st == "dead_letter"
    assert "Max attempts" in reason

    conn.close()


@pytest.mark.automated
def test_backoff_calculation() -> None:
    fake_clock = FakeClock(now())
    set_clock(fake_clock)
    try:
        t0 = now()
        # 30s, 1m, 5m, 15m
        assert calculate_next_attempt_at(1) == format_timestamp(t0 + timedelta(seconds=30))
        assert calculate_next_attempt_at(2) == format_timestamp(t0 + timedelta(seconds=60))
        assert calculate_next_attempt_at(3) == format_timestamp(t0 + timedelta(seconds=300))
        assert calculate_next_attempt_at(4) == format_timestamp(t0 + timedelta(seconds=900))
        assert calculate_next_attempt_at(5) is None
    finally:
        set_clock(Clock())

