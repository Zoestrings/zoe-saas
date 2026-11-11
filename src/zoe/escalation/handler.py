"""Escalation handler creating escalation records and moderator notifications atomically."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from typing import Any, Dict, Optional, Union

from zoe.clock.clock import format_timestamp, now, parse_timestamp
from zoe.db.connections import open_operational_db
from zoe.inbox.lifecycle import transition
from zoe.utils.logging import get_logger

logger = get_logger("zoe.escalation.handler")


@dataclass(frozen=True)
class EscalationResult:
    escalated: bool
    escalation_id: Optional[int] = None
    notification_id: Optional[int] = None
    severity: Optional[str] = None
    reason: Optional[str] = None


def determine_severity(text: str, reason: str = "") -> str:
    """Determine escalation severity per Spec §10.3:

    Critical: compromised wallet, stolen funds, private keys, active hack.
    Normal: general complaints, admin request, unfulfilled support.
    """
    combined = f"{text} {reason}".lower()
    critical_terms = [
        "compromised",
        "hacked",
        "stolen",
        "lost funds",
        "funds lost",
        "seed phrase leaked",
        "private key leaked",
        "exploit",
    ]
    high_terms = [
        "scam",
        "phishing",
        "fake admin",
        "impersonator",
    ]
    if any(term in combined for term in critical_terms):
        return "critical"
    if any(term in combined for term in high_terms):
        return "high"
    return "normal"


def handle_escalation(
    inbox_row: Union[int, Dict[str, Any]],
    severity: Optional[str] = None,
    reason: Optional[str] = None,
    db_conns: Optional[Dict[str, sqlite3.Connection]] = None,
    op_db_path: Optional[Union[str, Path]] = None,
    channel_id: Optional[str] = None,
    current_time: Optional[datetime] = None,
    simulated: bool = True,
) -> EscalationResult:
    """Handle escalation inside a single BEGIN IMMEDIATE transaction.

    Inserts into escalations (notification_status='simulated', resolution_status='unresolved')
    and moderator_notifications (simulated=1, state='pending').
    Enforces 1 escalation per user per hour rate limit.
    Transitions inbox row to 'escalated'.
    """
    conn = db_conns.get("operational") if db_conns else None
    close_conn = False
    if conn is None:
        conn = open_operational_db(op_db_path or "data/operational/operational.db")
        close_conn = True

    now_dt = current_time or now()

    try:
        # Load inbox details if inbox_id passed
        cur = conn.cursor()
        if isinstance(inbox_row, int):
            cur.execute(
                """
                SELECT id, project_id, group_id, telegram_message_id, pseudonymous_user_id, text
                FROM inbox_messages WHERE id = ?
                """,
                (inbox_row,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Inbox message {inbox_row} not found")
            inbox_id, project_id, group_id, msg_id, pseudo_id, text = row
        else:
            inbox_id = inbox_row["id"]
            project_id = inbox_row["project_id"]
            group_id = inbox_row["group_id"]
            msg_id = inbox_row["telegram_message_id"]
            pseudo_id = inbox_row["pseudonymous_user_id"]
            text = inbox_row["text"]

        eff_severity = severity or determine_severity(text, reason or "")
        eff_reason = reason or "User escalation triggered"

        # Rate Limit Check: Max 1 escalation per user per hour per project
        cutoff_dt = now_dt - timedelta(hours=1)
        cutoff_str = format_timestamp(cutoff_dt)
        cur.execute(
            """
            SELECT id, created_at FROM escalations
            WHERE project_id = ? AND pseudonymous_user_id = ?
              AND created_at >= ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (project_id, pseudo_id, cutoff_str),
        )
        prev_esc = cur.fetchone()
        if prev_esc:
            logger.warning("User %s rate-limited for escalation (previous at %s)", pseudo_id, prev_esc[1])
            return EscalationResult(
                escalated=False,
                reason="rate_limit_exceeded",
            )

        # Single BEGIN IMMEDIATE transaction
        conn.execute("BEGIN IMMEDIATE")
        try:
            created_str = format_timestamp(now_dt)
            initial_notif_status = "simulated" if simulated else "pending"
            sim_flag = 1 if simulated else 0

            # 1. Insert escalation record
            cur.execute(
                """
                INSERT INTO escalations (
                    project_id, inbox_message_id, group_id, telegram_message_id,
                    pseudonymous_user_id, severity, reason, notification_status,
                    resolution_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'unresolved', ?)
                """,
                (
                    project_id,
                    inbox_id,
                    group_id,
                    msg_id,
                    pseudo_id,
                    eff_severity,
                    eff_reason,
                    initial_notif_status,
                    created_str,
                ),
            )
            escalation_id = cur.lastrowid

            # 2. Insert moderator notification
            notif_channel = channel_id or f"-100_mod_{project_id}"
            notif_text = (
                f"🚨 [ESCALATION - {eff_severity.upper()}]\n"
                f"Project: {project_id}\n"
                f"Group: {group_id}\n"
                f"Message ID: {msg_id}\n"
                f"User: {pseudo_id[:12]}...\n"
                f"Reason: {eff_reason}\n"
                f"Text: \"{text}\""
            )
            cur.execute(
                """
                INSERT INTO moderator_notifications (
                    project_id, escalation_id, channel_id, text, simulated,
                    state, state_changed_at, created_at
                ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    project_id,
                    escalation_id,
                    notif_channel,
                    notif_text,
                    sim_flag,
                    created_str,
                    created_str,
                ),
            )
            notification_id = cur.lastrowid

            # 3. Transition inbox row to 'escalated'
            transition(conn, inbox_id, "escalated")

            conn.commit()
            logger.info(
                "Created escalation %s and notification %s for inbox %s",
                escalation_id,
                notification_id,
                inbox_id,
            )
            return EscalationResult(
                escalated=True,
                escalation_id=escalation_id,
                notification_id=notification_id,
                severity=eff_severity,
                reason=eff_reason,
            )
        except Exception:
            conn.rollback()
            raise

    finally:
        if close_conn:
            conn.close()

