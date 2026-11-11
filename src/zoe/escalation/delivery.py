"""Delivery handler for moderator notifications supporting both Sink Mode and Live Delivery."""

import asyncio
import inspect
from pathlib import Path
import sqlite3
from typing import Any, Dict, Optional, Union

from zoe.clock.clock import format_timestamp, now
from zoe.db.connections import open_operational_db
from zoe.utils.logging import get_logger

logger = get_logger("zoe.escalation.delivery")


async def deliver_moderator_notification_async(
    notification_row: Union[int, Dict[str, Any]],
    db_conn: Optional[sqlite3.Connection] = None,
    op_db_path: Optional[Union[str, Path]] = None,
    adapter: Optional[Any] = None,
    telegram_message_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute delivery for a moderator notification.

    If simulated == 1:
        moderator_notifications: pending -> sending -> simulated_delivered
        escalations: notification_status -> 'simulated'

    If simulated == 0:
        moderator_notifications: pending -> sending -> sent (with telegram_message_id)
        escalations: notification_status -> 'delivered'
        escalations.resolution_status remains 'unresolved' (delivery is NOT resolution)
    """
    conn = db_conn or open_operational_db(op_db_path or "data/operational/operational.db")
    close_conn = db_conn is None

    try:
        cur = conn.cursor()
        notif_id = notification_row if isinstance(notification_row, int) else notification_row["id"]

        cur.execute(
            """
            SELECT id, escalation_id, channel_id, text, state, simulated
            FROM moderator_notifications
            WHERE id = ?
            """,
            (notif_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Moderator notification {notif_id} not found")

        notif_id, escalation_id, channel_id, text, current_state, simulated = row

        # Step 1: pending -> sending
        t1 = format_timestamp(now())
        cur.execute(
            """
            UPDATE moderator_notifications
            SET state = 'sending', state_changed_at = ?
            WHERE id = ? AND state = 'pending'
            """,
            (t1, notif_id),
        )

        sent_tg_id = telegram_message_id

        if simulated == 1:
            # Step 2 (simulated): sending -> simulated_delivered
            t2 = format_timestamp(now())
            cur.execute(
                """
                UPDATE moderator_notifications
                SET state = 'simulated_delivered', state_changed_at = ?, sent_at = ?
                WHERE id = ? AND state = 'sending'
                """,
                (t2, t2, notif_id),
            )

            # Step 3 (simulated): Update escalation notification_status='simulated'
            cur.execute(
                """
                UPDATE escalations
                SET notification_status = 'simulated'
                WHERE id = ?
                """,
                (escalation_id,),
            )
            final_state = "simulated_delivered"
            final_notif_status = "simulated"

        else:
            # Step 2 (live): Send through adapter if provided
            if adapter is not None:
                if inspect.iscoroutinefunction(adapter.send_message):
                    resp = await adapter.send_message(chat_id=channel_id, text=text)
                else:
                    resp = adapter.send_message(chat_id=channel_id, text=text)
                sent_tg_id = resp.get("message_id") if isinstance(resp, dict) else resp

            t2 = format_timestamp(now())
            cur.execute(
                """
                UPDATE moderator_notifications
                SET state = 'sent', state_changed_at = ?, sent_at = ?, telegram_message_id = ?
                WHERE id = ? AND state = 'sending'
                """,
                (t2, t2, sent_tg_id, notif_id),
            )

            # Step 3 (live): Update escalation notification_status='delivered'
            cur.execute(
                """
                UPDATE escalations
                SET notification_status = 'delivered'
                WHERE id = ?
                """,
                (escalation_id,),
            )
            final_state = "sent"
            final_notif_status = "delivered"

        conn.commit()
        logger.info(
            "Delivered moderator notification %s for escalation %s (state: %s, notif_status: %s)",
            notif_id,
            escalation_id,
            final_state,
            final_notif_status,
        )

        return {
            "notification_id": notif_id,
            "escalation_id": escalation_id,
            "state": final_state,
            "notification_status": final_notif_status,
            "telegram_message_id": sent_tg_id,
        }
    finally:
        if close_conn:
            conn.close()


def deliver_notification(
    notification_row: Union[int, Dict[str, Any]],
    db_conn: Optional[sqlite3.Connection] = None,
    op_db_path: Optional[Union[str, Path]] = None,
    adapter: Optional[Any] = None,
    telegram_message_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Synchronous entrypoint for delivering a notification."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    coro = deliver_moderator_notification_async(
        notification_row=notification_row,
        db_conn=db_conn,
        op_db_path=op_db_path,
        adapter=adapter,
        telegram_message_id=telegram_message_id,
    )

    if loop and loop.is_running():
        # If already running in a loop (e.g. within an async test)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)
