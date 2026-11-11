from datetime import timedelta
import json
import sqlite3
from typing import Any, Dict, List, Optional

from zoe.clock.clock import format_timestamp, now
from zoe.inbox.lifecycle import transition
from zoe.telegram.adapter import TelegramAdapter
from zoe.utils.logging import get_logger

logger = get_logger("zoe.outbox.service")

OUTBOX_BACKOFF_DELAYS = {
    1: 30,
    2: 60,
    3: 300,
    4: 900,
}


def enqueue_response(
    conn: sqlite3.Connection,
    project_id: str,
    inbox_message_id: int,
    group_id: str,
    text: str,
    reply_to_message_id: Optional[int] = None,
    simulated: bool = False,
    inline_keyboard: Optional[List[List[Dict[str, str]]]] = None,
) -> int:
    """Insert an outbox_messages row and transition inbox row to response_pending

    in a single atomic transaction.
    """
    now_str = format_timestamp(now())
    sim_flag = 1 if simulated else 0
    ik_json = json.dumps(inline_keyboard) if inline_keyboard else None

    conn.execute("BEGIN IMMEDIATE")
    try:
        # 1. Transition inbox row: processing -> response_pending
        transition(
            conn,
            inbox_message_id,
            "response_pending",
            expected_current_state="processing",
        )

        # 2. Insert outbox row
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO outbox_messages (
                project_id,
                inbox_message_id,
                group_id,
                reply_to_message_id,
                text,
                simulated,
                state,
                state_changed_at,
                attempt_count,
                created_at,
                inline_keyboard_json
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, 0, ?, ?)
            RETURNING id
            """,
            (
                project_id,
                inbox_message_id,
                group_id,
                reply_to_message_id,
                text,
                sim_flag,
                now_str,
                now_str,
                ik_json,
            ),
        )
        outbox_id = cur.fetchone()[0]
        conn.commit()
        return outbox_id

    except Exception:
        conn.rollback()
        raise


async def drain_outbox(
    conn: sqlite3.Connection,
    project_id: str,
    adapter: TelegramAdapter,
    worker_id: str = "outbox_drain",
    batch_size: int = 10,
) -> int:
    """Drain pending outbox messages: claim to sending, call adapter, update on delivery."""
    now_dt = now()
    now_str = format_timestamp(now_dt)
    lease_expires = format_timestamp(now_dt + timedelta(seconds=60))

    # Fetch candidate outbox messages
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, inbox_message_id, group_id, reply_to_message_id, text, simulated, attempt_count, inline_keyboard_json
        FROM outbox_messages
        WHERE project_id = ?
          AND (
            state = 'pending'
            OR (state = 'sending' AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?)
            OR (state = 'failed' AND (next_attempt_at IS NULL OR next_attempt_at <= ?))
          )
          AND attempt_count < 5
        ORDER BY id ASC
        LIMIT ?
        """,
        (project_id, now_str, now_str, batch_size),
    )
    rows = cur.fetchall()
    if not rows:
        return 0

    delivered_count = 0

    for row in rows:
        outbox_id, inbox_id, group_id, reply_to, text, simulated, attempt_count, ik_json = row
        new_attempt = attempt_count + 1

        # Claim to sending state
        conn.execute("BEGIN IMMEDIATE")
        try:
            cur.execute(
                """
                UPDATE outbox_messages
                SET state = 'sending',
                    state_changed_at = ?,
                    lease_owner = ?,
                    lease_expires_at = ?,
                    attempt_count = ?
                WHERE id = ?
                """,
                (format_timestamp(now()), worker_id, lease_expires, new_attempt, outbox_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            continue

        # Parse inline keyboard if present
        parsed_ik = None
        if ik_json:
            try:
                parsed_ik = json.loads(ik_json)
            except Exception:
                parsed_ik = None

        # Send via adapter
        try:
            resp = await adapter.send_message(
                chat_id=group_id,
                text=text,
                reply_to_message_id=reply_to,
                inline_keyboard=parsed_ik,
            )
            sent_time = format_timestamp(now())
            tg_msg_id = resp.get("message_id")

            # Immediately mark outbox message as sent upon Telegram's 200 OK response
            target_state = "simulated_delivered" if simulated == 1 else "sent"
            conn.execute("BEGIN IMMEDIATE")
            try:
                cur.execute(
                    """
                    UPDATE outbox_messages
                    SET state = ?,
                        state_changed_at = ?,
                        sent_at = ?,
                        telegram_message_id = ?,
                        lease_owner = NULL,
                        lease_expires_at = NULL
                    WHERE id = ?
                    """,
                    (target_state, sent_time, sent_time, tg_msg_id, outbox_id),
                )
                conn.commit()
                delivered_count += 1
            except Exception as commit_err:
                conn.rollback()
                logger.error("Failed to commit sent state for outbox %d: %s", outbox_id, commit_err)
                raise

            # Transition inbox message: response_pending -> response_sent
            # Protected in its own try/except so transition errors never roll back outbox 'sent' status
            try:
                conn.execute("BEGIN IMMEDIATE")
                transition(
                    conn,
                    inbox_id,
                    "response_sent",
                    expected_current_state="response_pending",
                )
                conn.commit()
            except Exception as trans_err:
                conn.rollback()
                logger.warning(
                    "Inbox transition to response_sent for msg %d was skipped/errored: %s",
                    inbox_id,
                    trans_err,
                )

        except Exception as exc:
            logger.error(f"Failed to deliver outbox message {outbox_id}: {exc}")
            conn.execute("BEGIN IMMEDIATE")
            try:
                fail_time = format_timestamp(now())
                if new_attempt >= 5:
                    cur.execute(
                        """
                        UPDATE outbox_messages
                        SET state = 'dead_letter',
                            state_changed_at = ?,
                            error_message = ?,
                            lease_owner = NULL,
                            lease_expires_at = NULL
                        WHERE id = ?
                        """,
                        (fail_time, str(exc), outbox_id),
                    )
                else:
                    delay = OUTBOX_BACKOFF_DELAYS.get(new_attempt, 900)
                    next_attempt_str = format_timestamp(now() + timedelta(seconds=delay))
                    cur.execute(
                        """
                        UPDATE outbox_messages
                        SET state = 'failed',
                            state_changed_at = ?,
                            next_attempt_at = ?,
                            error_message = ?,
                            lease_owner = NULL,
                            lease_expires_at = NULL
                        WHERE id = ?
                        """,
                        (fail_time, next_attempt_str, str(exc), outbox_id),
                    )
                conn.commit()
            except Exception:
                conn.rollback()

    return delivered_count

