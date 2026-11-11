from datetime import timedelta
import sqlite3
from typing import Any, Dict, Optional

from zoe.clock.clock import format_timestamp, now
from zoe.inbox.lifecycle import transition
from zoe.utils.logging import get_logger

logger = get_logger("zoe.worker.claim")

# Backoff schedule: 30s, 1m, 5m, 15m
BACKOFF_DELAYS = {
    1: 30,
    2: 60,
    3: 300,
    4: 900,
}


def calculate_next_attempt_at(attempt_count: int) -> Optional[str]:
    """Calculate next_attempt_at using backoff sequence (30s, 1m, 5m, 15m).

    Returns None if retries are exhausted (attempt_count >= 5).
    """
    if attempt_count >= 5:
        return None
    delay_sec = BACKOFF_DELAYS.get(attempt_count, 900)
    target_dt = now() + timedelta(seconds=delay_sec)
    return format_timestamp(target_dt)


def claim_next_inbox_row(
    conn: sqlite3.Connection,
    project_id: str,
    worker_id: str,
    lease_duration_seconds: int = 300,
) -> Optional[Dict[str, Any]]:
    """Atomically claim the next claimable inbox row inside a BEGIN IMMEDIATE transaction.

    Claimable rows are:
    - state == 'message_persisted' and attempt_count < 5
    - state == 'failed' with next_attempt_at <= now and attempt_count < 5
    - state == 'processing' with expired lease and attempt_count < 5
    """
    now_dt = now()
    now_str = format_timestamp(now_dt)
    lease_expires = format_timestamp(now_dt + timedelta(seconds=lease_duration_seconds))

    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.cursor()

        # Find eligible claimable ID
        cur.execute(
            """
            SELECT id FROM inbox_messages
            WHERE project_id = ?
              AND (
                state = 'message_persisted'
                OR (state = 'failed' AND (next_attempt_at IS NULL OR next_attempt_at <= ?))
                OR (state = 'processing' AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?)
              )
              AND attempt_count < 5
            ORDER BY id ASC
            LIMIT 1
            """,
            (project_id, now_str, now_str),
        )
        row = cur.fetchone()
        if row is None:
            conn.commit()
            return None

        inbox_id = row[0]

        # Atomically update and claim the row
        cur.execute(
            """
            UPDATE inbox_messages
            SET state = 'processing',
                state_changed_at = ?,
                lease_owner = ?,
                lease_expires_at = ?,
                attempt_count = attempt_count + 1
            WHERE id = ?
            RETURNING
                id,
                project_id,
                telegram_update_id,
                group_id,
                telegram_message_id,
                pseudonymous_user_id,
                text,
                reply_to_message_id,
                is_forward,
                message_timestamp,
                state,
                attempt_count,
                lease_owner,
                lease_expires_at
            """,
            (now_str, worker_id, lease_expires, inbox_id),
        )
        claimed_row = cur.fetchone()
        conn.commit()

        if claimed_row:
            col_names = [d[0] for d in cur.description]
            return dict(zip(col_names, claimed_row))
        return None

    except Exception:
        conn.rollback()
        raise


def record_worker_failure(
    conn: sqlite3.Connection,
    inbox_id: int,
    failure_reason: str,
) -> str:
    """Record a failure for an inbox message. If attempt_count reaches 5,

    transitions to dead_letter; otherwise sets next_attempt_at with backoff.
    Returns resulting state ('failed' or 'dead_letter').
    """
    cur = conn.cursor()
    cur.execute("SELECT attempt_count FROM inbox_messages WHERE id = ?", (inbox_id,))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Inbox message {inbox_id} not found.")

    attempt_count = row[0]
    if attempt_count >= 5:
        transition(
            conn,
            inbox_id,
            "dead_letter",
            expected_current_state="processing",
            failure_reason=failure_reason,
            lease_owner=None,
            lease_expires_at=None,
        )
        return "dead_letter"
    else:
        next_attempt = calculate_next_attempt_at(attempt_count)
        transition(
            conn,
            inbox_id,
            "failed",
            expected_current_state="processing",
            failure_reason=failure_reason,
            next_attempt_at=next_attempt,
            lease_owner=None,
            lease_expires_at=None,
        )
        return "failed"

