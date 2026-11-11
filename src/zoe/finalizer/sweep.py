from dataclasses import dataclass
from datetime import timedelta
import sqlite3
from typing import List

from zoe.clock.clock import format_timestamp, now
from zoe.inbox.lifecycle import transition
from zoe.utils.logging import get_logger

logger = get_logger("zoe.finalizer.sweep")


@dataclass(frozen=True)
class FinalizerSweepResult:
    completed_count: int
    investigation_count: int


def sweep_finalizer(
    conn: sqlite3.Connection,
    project_id: str,
    threshold_seconds: int = 30,
) -> FinalizerSweepResult:
    """Sweep response_sent inbox messages older than threshold_seconds.

    Reconciles with outbox_messages:
    - Exactly 1 outbox row with state in ('sent', 'simulated_delivered') -> completed
    - Missing, multiple, or invalid state outbox row -> needs_investigation
    """
    cutoff_dt = now() - timedelta(seconds=threshold_seconds)
    cutoff_str = format_timestamp(cutoff_dt)

    cur = conn.cursor()
    cur.execute(
        """
        SELECT id FROM inbox_messages
        WHERE project_id = ?
          AND state = 'response_sent'
          AND state_changed_at <= ?
        ORDER BY id ASC
        """,
        (project_id, cutoff_str),
    )
    candidate_ids = [r[0] for r in cur.fetchall()]

    completed_count = 0
    investigation_count = 0

    for inbox_id in candidate_ids:
        cur.execute(
            "SELECT id, state FROM outbox_messages WHERE inbox_message_id = ?",
            (inbox_id,),
        )
        outbox_rows = cur.fetchall()

        conn.execute("BEGIN IMMEDIATE")
        try:
            if len(outbox_rows) == 1 and outbox_rows[0][1] in {"sent", "simulated_delivered"}:
                transition(
                    conn,
                    inbox_id,
                    "completed",
                    expected_current_state="response_sent",
                )
                completed_count += 1
            elif len(outbox_rows) == 0:
                logger.warning(f"Finalizer reconciliation failed for inbox {inbox_id}: missing outbox message")
                transition(
                    conn,
                    inbox_id,
                    "needs_investigation",
                    expected_current_state="response_sent",
                    investigation_reason="Missing outbox message row for response_sent message",
                )
                investigation_count += 1
            elif len(outbox_rows) > 1:
                logger.warning(
                    f"Finalizer reconciliation anomaly for inbox {inbox_id}: multiple outbox messages ({len(outbox_rows)})"
                )
                transition(
                    conn,
                    inbox_id,
                    "needs_investigation",
                    expected_current_state="response_sent",
                    investigation_reason=f"Multiple outbox rows ({len(outbox_rows)}) found",
                )
                investigation_count += 1
            else:
                outbox_state = outbox_rows[0][1]
                logger.warning(
                    f"Finalizer reconciliation failed for inbox {inbox_id}: outbox in state '{outbox_state}'"
                )
                transition(
                    conn,
                    inbox_id,
                    "needs_investigation",
                    expected_current_state="response_sent",
                    investigation_reason=f"Outbox message is in invalid state '{outbox_state}'",
                )
                investigation_count += 1

            conn.commit()
        except Exception:
            conn.rollback()
            raise

    return FinalizerSweepResult(
        completed_count=completed_count,
        investigation_count=investigation_count,
    )

