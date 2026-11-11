import sqlite3
from typing import Any, Dict, Optional, Set, Tuple

from zoe.clock.clock import format_timestamp, now
from zoe.utils.errors import InvalidTransitionError
from zoe.utils.logging import get_logger

logger = get_logger("zoe.inbox.lifecycle")

# Exact transition matrix per Spec §8.3
ALLOWED_INBOX_TRANSITIONS: Set[Tuple[str, str]] = {
    ("message_persisted", "processing"),
    ("failed", "processing"),
    ("processing", "no_response_required"),
    ("processing", "response_pending"),
    ("processing", "failed"),
    ("processing", "dead_letter"),
    ("processing", "needs_investigation"),
    ("processing", "escalated"),
    ("response_pending", "response_sent"),
    ("response_pending", "failed"),
    ("response_sent", "completed"),
    ("response_sent", "needs_investigation"),
    ("escalated", "completed"),
    ("escalated", "needs_investigation"),
}


def validate_transition(current_state: str, new_state: str) -> None:
    """Validate that transitioning from current_state to new_state is permitted."""
    if (current_state, new_state) not in ALLOWED_INBOX_TRANSITIONS:
        raise InvalidTransitionError(
            f"Invalid transition from '{current_state}' to '{new_state}'"
        )


def transition(
    conn: sqlite3.Connection,
    inbox_id: int,
    new_state: str,
    expected_current_state: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Transition an inbox message to a new state and record state_changed_at timestamp.

    If expected_current_state is provided, it verifies and guards against race conditions.
    """
    cur = conn.cursor()
    cur.execute("SELECT state FROM inbox_messages WHERE id = ?", (inbox_id,))
    row = cur.fetchone()
    if row is None:
        raise ValueError(f"Inbox message {inbox_id} does not exist.")

    current_state = row[0]
    if expected_current_state and current_state != expected_current_state:
        raise InvalidTransitionError(
            f"Expected state '{expected_current_state}', but message is currently '{current_state}'"
        )

    validate_transition(current_state, new_state)

    now_str = format_timestamp(now())
    updates = ["state = ?", "state_changed_at = ?"]
    params = [new_state, now_str]

    for k, v in kwargs.items():
        updates.append(f"{k} = ?")
        params.append(v)

    params.append(inbox_id)
    sql = f"UPDATE inbox_messages SET {', '.join(updates)} WHERE id = ?"
    cur.execute(sql, params)

