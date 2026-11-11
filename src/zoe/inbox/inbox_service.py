from dataclasses import dataclass
import sqlite3
from typing import List

from zoe.clock.clock import format_timestamp, now
from zoe.telegram.normalizer import NormalizedMessage
from zoe.utils.logging import get_logger

logger = get_logger("zoe.inbox.service")


@dataclass(frozen=True)
class PersistResult:
    inserted_count: int
    skipped_duplicate_count: int
    final_offset: int


def ensure_project_registered(
    conn: sqlite3.Connection,
    project_id: str,
    name: str = "Zoe Project",
    telegram_group_id: str = "-1001234567890",
    config_json: str = "{}",
) -> None:
    """Ensure parent row in projects table exists for foreign key constraints."""
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO projects (project_id, name, telegram_group_id, config_json, created_at, active)
        VALUES (?, ?, ?, ?, ?, 1)
        """,
        (project_id, name, telegram_group_id, config_json, format_timestamp(now())),
    )
    conn.commit()


def init_polling_state(conn: sqlite3.Connection, project_id: str) -> None:
    """Initialize polling_state for a project if not already present."""
    ensure_project_registered(conn, project_id)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO polling_state (project_id, last_persisted_update_id, next_offset, updated_at)
        VALUES (?, 0, 1, ?)
        """,
        (project_id, format_timestamp(now())),
    )
    conn.commit()


def persist_batch(
    conn: sqlite3.Connection,
    project_id: str,
    normalized_messages: List[NormalizedMessage],
    last_update_id_in_batch: int,
) -> PersistResult:
    """Persist a batch of normalized messages, update receipts, and advance polling_state

    in a single atomic BEGIN IMMEDIATE transaction.
    """
    ensure_project_registered(conn, project_id)

    inserted_count = 0
    skipped_duplicate_count = 0
    now_str = format_timestamp(now())

    # Begin immediate transaction to lock database against concurrent writers
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.cursor()

        for msg in normalized_messages:
            # 1. Insert into inbox_messages
            cur.execute(
                """
                INSERT OR IGNORE INTO inbox_messages (
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
                    state_changed_at,
                    attempt_count,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'message_persisted', ?, 0, ?)
                """,
                (
                    msg.project_id,
                    msg.telegram_update_id,
                    msg.group_id,
                    msg.telegram_message_id,
                    msg.pseudonymous_user_id,
                    msg.text,
                    msg.reply_to_message_id,
                    1 if msg.is_forward else 0,
                    msg.timestamp,
                    now_str,
                    now_str,
                ),
            )

            if cur.rowcount > 0:
                inserted_count += 1
            else:
                skipped_duplicate_count += 1

            # 2. Insert into update_receipts
            cur.execute(
                """
                INSERT OR IGNORE INTO update_receipts (
                    project_id,
                    telegram_update_id,
                    received_at,
                    processing_status
                ) VALUES (?, ?, ?, 'persisted')
                """,
                (msg.project_id, msg.telegram_update_id, now_str),
            )

        # 3. Advance polling state if there were updates processed in this batch
        if last_update_id_in_batch > 0:
            next_offset = last_update_id_in_batch + 1
            cur.execute(
                """
                INSERT INTO polling_state (project_id, last_persisted_update_id, next_offset, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    last_persisted_update_id = excluded.last_persisted_update_id,
                    next_offset = excluded.next_offset,
                    updated_at = excluded.updated_at
                """,
                (project_id, last_update_id_in_batch, next_offset, now_str),
            )
            final_offset = next_offset
        else:
            # Fetch current next_offset
            cur.execute("SELECT next_offset FROM polling_state WHERE project_id = ?", (project_id,))
            row = cur.fetchone()
            final_offset = row[0] if row else 1

        conn.commit()
        return PersistResult(
            inserted_count=inserted_count,
            skipped_duplicate_count=skipped_duplicate_count,
            final_offset=final_offset,
        )

    except Exception:
        conn.rollback()
        raise

