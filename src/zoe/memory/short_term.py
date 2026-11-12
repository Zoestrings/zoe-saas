"""Short-term community conversation context window."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from zoe.clock.clock import format_timestamp, now
from zoe.db.connections import open_community_memory_db
from zoe.utils.logging import get_logger

logger = get_logger("zoe.memory.short_term")


def record_community_message(
    project_id: str,
    group_id: str,
    telegram_message_id: int,
    pseudonymous_user_id: str,
    content: str,
    received_at: Optional[Union[str, datetime]] = None,
    db_path: Optional[Union[str, Path]] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """Record an incoming community discussion message into community_memory.db."""
    should_close = False
    if conn is None:
        effective_db = Path(db_path) if db_path else Path("data/community_memory/community_memory.db")
        conn = open_community_memory_db(effective_db)
        should_close = True

    if received_at is None:
        rec_str = format_timestamp(now())
    elif isinstance(received_at, datetime):
        rec_str = format_timestamp(received_at)
    else:
        rec_str = str(received_at)

    try:
        cur = conn.execute(
            """
            INSERT INTO community_messages (
                project_id, group_id, telegram_message_id, pseudonymous_user_id,
                content, received_at, summarized_at
            ) VALUES (?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                project_id,
                group_id,
                telegram_message_id,
                pseudonymous_user_id,
                content,
                rec_str,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        if should_close:
            conn.close()


def get_recent_context(
    project_id: str,
    group_id: str,
    limit: int = 10,
    db_path: Optional[Union[str, Path]] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> List[str]:
    """Retrieve the most recent `limit` messages from community_messages for this group.

    Returned in chronological order (oldest to newest among the recent window).
    Returns only message text content strings without raw identifiers.
    """
    should_close = False
    if conn is None:
        effective_db = Path(db_path) if db_path else Path("data/community_memory/community_memory.db")
        conn = open_community_memory_db(effective_db)
        should_close = True
    try:
        cur = conn.execute(
            """
            SELECT content FROM (
                SELECT content, received_at, id
                FROM community_messages
                WHERE project_id = ? AND group_id = ?
                ORDER BY received_at DESC, id DESC
                LIMIT ?
            ) ORDER BY received_at ASC, id ASC
            """,
            (project_id, group_id, limit),
        )
        rows = cur.fetchall()
        return [row[0] for row in rows]
    finally:
        if should_close:
            conn.close()


def get_recent_conversation_history(
    project_id: str,
    group_id: str,
    limit: int = 6,
    db_path: Optional[Union[str, Path]] = None,
    exclude_message_id: Optional[int] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> List[str]:
    """Retrieve recent conversation turns (user and Zoe) formatted as:
    ['User: ...', 'Zoe: ...'] in chronological order.
    """
    should_close = False
    if conn is None:
        effective_db = Path(db_path) if db_path else Path("data/community_memory/community_memory.db")
        conn = open_community_memory_db(effective_db)
        should_close = True
    try:
        if exclude_message_id is not None:
            cur = conn.execute(
                """
                SELECT pseudonymous_user_id, content FROM (
                    SELECT pseudonymous_user_id, content, received_at, id
                    FROM community_messages
                    WHERE project_id = ? AND group_id = ? AND telegram_message_id != ?
                    ORDER BY id DESC
                    LIMIT ?
                ) ORDER BY id ASC
                """,
                (project_id, group_id, exclude_message_id, limit),
            )
        else:
            cur = conn.execute(
                """
                SELECT pseudonymous_user_id, content FROM (
                    SELECT pseudonymous_user_id, content, received_at, id
                    FROM community_messages
                    WHERE project_id = ? AND group_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                ) ORDER BY id ASC
                """,
                (project_id, group_id, limit),
            )
        rows = cur.fetchall()
        turns: List[str] = []
        for pseudo_id, content in rows:
            speaker = "Zoe" if pseudo_id == "zoe" else "User"
            turns.append(f"{speaker}: {content.strip()}")
        return turns
    finally:
        if should_close:
            conn.close()


def get_most_recent_group_message(
    project_id: str,
    target_group_id: Optional[str] = None,
    conn_op: Optional[sqlite3.Connection] = None,
    conn_mem: Optional[sqlite3.Connection] = None,
    op_db_path: Optional[Union[str, Path]] = None,
    mem_db_path: Optional[Union[str, Path]] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent user message from the community group for cross-chat awareness."""
    # 1. First, check inbox_messages in operational database
    close_op = False
    if conn_op is None and op_db_path:
        from zoe.db.connections import open_operational_db
        conn_op = open_operational_db(op_db_path)
        close_op = True

    if conn_op is not None:
        try:
            if target_group_id and str(target_group_id).strip():
                cur = conn_op.execute(
                    """
                    SELECT id, text, pseudonymous_user_id, group_id, created_at
                    FROM inbox_messages
                    WHERE project_id = ?
                      AND (group_id = ? OR group_id LIKE '-%')
                      AND pseudonymous_user_id != 'zoe'
                      AND text NOT LIKE '/%'
                    ORDER BY (CASE WHEN group_id = ? THEN 1 ELSE 0 END) DESC, id DESC
                    LIMIT 1
                    """,
                    (project_id, str(target_group_id), str(target_group_id)),
                )
            else:
                cur = conn_op.execute(
                    """
                    SELECT id, text, pseudonymous_user_id, group_id, created_at
                    FROM inbox_messages
                    WHERE project_id = ?
                      AND group_id LIKE '-%'
                      AND pseudonymous_user_id != 'zoe'
                      AND text NOT LIKE '/%'
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (project_id,),
                )
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "text": row[1],
                    "user_id": row[2],
                    "group_id": row[3],
                    "timestamp": row[4],
                }
        except Exception as exc:
            logger.warning("Error querying inbox_messages for cross-chat message: %s", exc)
        finally:
            if close_op:
                conn_op.close()

    # 2. Fallback: check community_messages in memory database
    close_mem = False
    if conn_mem is None:
        effective_db = Path(mem_db_path) if mem_db_path else Path("data/community_memory/community_memory.db")
        conn_mem = open_community_memory_db(effective_db)
        close_mem = True

    try:
        if target_group_id and str(target_group_id).strip():
            cur = conn_mem.execute(
                """
                SELECT id, content, pseudonymous_user_id, group_id, received_at
                FROM community_messages
                WHERE project_id = ?
                  AND (group_id = ? OR group_id LIKE '-%')
                  AND pseudonymous_user_id != 'zoe'
                  AND content NOT LIKE '/%'
                ORDER BY (CASE WHEN group_id = ? THEN 1 ELSE 0 END) DESC, id DESC
                LIMIT 1
                """,
                (project_id, str(target_group_id), str(target_group_id)),
            )
        else:
            cur = conn_mem.execute(
                """
                SELECT id, content, pseudonymous_user_id, group_id, received_at
                FROM community_messages
                WHERE project_id = ?
                  AND group_id LIKE '-%'
                  AND pseudonymous_user_id != 'zoe'
                  AND content NOT LIKE '/%'
                ORDER BY id DESC
                LIMIT 1
                """,
                (project_id,),
            )
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "text": row[1],
                "user_id": row[2],
                "group_id": row[3],
                "timestamp": row[4],
            }
    except Exception as exc:
        logger.warning("Error querying community_messages for cross-chat message: %s", exc)
    finally:
        if close_mem:
            conn_mem.close()

    return None


def get_recent_group_messages(
    project_id: str,
    target_group_id: Optional[str] = None,
    limit: int = 5,
    conn_op: Optional[sqlite3.Connection] = None,
    conn_mem: Optional[sqlite3.Connection] = None,
    op_db_path: Optional[Union[str, Path]] = None,
    mem_db_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Retrieve the most recent `limit` group messages from community_messages or inbox_messages for cross-chat awareness."""
    messages: List[Dict[str, Any]] = []

    # 1. Query community_messages in community_memory database
    close_mem = False
    if conn_mem is None:
        effective_db = Path(mem_db_path) if mem_db_path else Path("data/community_memory/community_memory.db")
        if effective_db.exists():
            conn_mem = open_community_memory_db(effective_db)
            close_mem = True

    if conn_mem is not None:
        try:
            if target_group_id and str(target_group_id).strip():
                cur = conn_mem.execute(
                    """
                    SELECT id, content, pseudonymous_user_id, group_id, received_at FROM (
                        SELECT id, content, pseudonymous_user_id, group_id, received_at
                        FROM community_messages
                        WHERE project_id = ?
                          AND (group_id = ? OR group_id LIKE '-%')
                          AND content NOT LIKE '/%'
                        ORDER BY id DESC
                        LIMIT ?
                    ) ORDER BY id ASC
                    """,
                    (project_id, str(target_group_id), limit),
                )
            else:
                cur = conn_mem.execute(
                    """
                    SELECT id, content, pseudonymous_user_id, group_id, received_at FROM (
                        SELECT id, content, pseudonymous_user_id, group_id, received_at
                        FROM community_messages
                        WHERE project_id = ?
                          AND group_id LIKE '-%'
                          AND content NOT LIKE '/%'
                        ORDER BY id DESC
                        LIMIT ?
                    ) ORDER BY id ASC
                    """,
                    (project_id, limit),
                )
            rows = cur.fetchall()
            for r in rows:
                messages.append({
                    "id": r[0],
                    "text": r[1],
                    "user_id": r[2],
                    "group_id": r[3],
                    "timestamp": r[4],
                })
        except Exception as exc:
            logger.warning("Error querying community_messages for recent group messages: %s", exc)
        finally:
            if close_mem:
                conn_mem.close()

    if messages:
        return messages

    # 2. Fallback: Query inbox_messages in operational database
    close_op = False
    if conn_op is None and op_db_path:
        from zoe.db.connections import open_operational_db
        effective_op = Path(op_db_path)
        if effective_op.exists():
            conn_op = open_operational_db(effective_op)
            close_op = True

    if conn_op is not None:
        try:
            if target_group_id and str(target_group_id).strip():
                cur = conn_op.execute(
                    """
                    SELECT id, text, pseudonymous_user_id, group_id, message_timestamp FROM (
                        SELECT id, text, pseudonymous_user_id, group_id, message_timestamp
                        FROM inbox_messages
                        WHERE project_id = ?
                          AND (group_id = ? OR group_id LIKE '-%')
                          AND text NOT LIKE '/%'
                        ORDER BY id DESC
                        LIMIT ?
                    ) ORDER BY id ASC
                    """,
                    (project_id, str(target_group_id), limit),
                )
            else:
                cur = conn_op.execute(
                    """
                    SELECT id, text, pseudonymous_user_id, group_id, message_timestamp FROM (
                        SELECT id, text, pseudonymous_user_id, group_id, message_timestamp
                        FROM inbox_messages
                        WHERE project_id = ?
                          AND group_id LIKE '-%'
                          AND text NOT LIKE '/%'
                        ORDER BY id DESC
                        LIMIT ?
                    ) ORDER BY id ASC
                    """,
                    (project_id, limit),
                )
            rows = cur.fetchall()
            for r in rows:
                messages.append({
                    "id": r[0],
                    "text": r[1],
                    "user_id": r[2],
                    "group_id": r[3],
                    "timestamp": r[4],
                })
        except Exception as exc:
            logger.warning("Error querying inbox_messages for recent group messages: %s", exc)
        finally:
            if close_op:
                conn_op.close()

    return messages



