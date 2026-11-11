"""Rolling summarizer for community memory adhering to Spec §13.6.2 attribution rules."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, List, Optional, Union

from zoe.clock.clock import format_timestamp, now
from zoe.db.connections import open_community_memory_db
from zoe.llm.mock import MockLLMClient
from zoe.utils.logging import get_logger

logger = get_logger("zoe.memory.summarizer")

SUMMARIZER_SYSTEM_PROMPT = """You are the Zoe Community Memory Summarizer.
Your task is to summarize community conversations over a specific time window.

CRITICAL RULES:
1. INPUT ISOLATION: You only process community discussion messages. These represent unverified member discussions and community sentiments.
2. ATTRIBUTION RULE (Spec §13.6.2):
   - Never state community rumors, speculation, or unverified claims as established facts.
   - Always frame community claims with attribution phrasing such as:
     - "Several members discussed..."
     - "Community members speculated about..."
     - "Some users claimed..."
     - "A topic of discussion was an unverified report that..."
   - Forbid outputting definitive statements about unconfirmed events, partnerships, token listings, or releases.
3. Be concise, objective, and professional.
"""


def _to_timestamp_str(dt_or_str: Union[str, datetime]) -> str:
    if isinstance(dt_or_str, datetime):
        return format_timestamp(dt_or_str)
    return str(dt_or_str)


def summarize_interval(
    project_id: str,
    group_id: str,
    period_start: Union[str, datetime],
    period_end: Union[str, datetime],
    db_path: Optional[Union[str, Path]] = None,
    llm_client: Optional[Any] = None,
) -> str:
    """Summarize messages in [period_start, period_end] from community_messages.

    CRITICAL: Input is isolated strictly to community_messages.
    Attribution rules from Spec §13.6.2 are enforced via the summarizer system prompt.
    """
    effective_db = Path(db_path) if db_path else Path("data/community_memory/community_memory.db")
    start_str = _to_timestamp_str(period_start)
    end_str = _to_timestamp_str(period_end)

    conn = open_community_memory_db(effective_db)
    try:
        cur = conn.execute(
            """
            SELECT id, content, received_at
            FROM community_messages
            WHERE project_id = ? AND group_id = ?
              AND received_at >= ? AND received_at <= ?
            ORDER BY received_at ASC, id ASC
            """,
            (project_id, group_id, start_str, end_str),
        )
        rows = cur.fetchall()
        if not rows:
            logger.info("No community messages found for %s / %s in [%s, %s]", project_id, group_id, start_str, end_str)
            return ""

        msg_ids = [r[0] for r in rows]
        bullet_points = "\n".join(f"- {r[1]}" for r in rows)
        user_prompt = (
            f"Please summarize the following community messages from {start_str} to {end_str}:\n"
            f"{bullet_points}"
        )

        client = llm_client if llm_client is not None else MockLLMClient()
        summary_text = client.generate(
            system_prompt=SUMMARIZER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        created_str = format_timestamp(now())
        conn.execute(
            """
            INSERT INTO community_memory_summaries (
                project_id, group_id, summary_text, period_start, period_end, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, group_id, summary_text, start_str, end_str, created_str),
        )

        placeholders = ",".join("?" for _ in msg_ids)
        conn.execute(
            f"UPDATE community_messages SET summarized_at = ? WHERE id IN ({placeholders})",
            [created_str] + msg_ids,
        )

        conn.commit()
        logger.info(
            "Summarized %s messages for %s / %s in [%s, %s]",
            len(msg_ids),
            project_id,
            group_id,
            start_str,
            end_str,
        )
        return summary_text
    finally:
        conn.close()


def summarize_rolling_window(
    project_id: str,
    group_id: str,
    cutoff_days: int = 14,
    db_path: Optional[Union[str, Path]] = None,
    llm_client: Optional[Any] = None,
    current_time: Optional[datetime] = None,
) -> Optional[str]:
    """Find unsummarized messages older than cutoff_days, summarize them, and record the summary."""
    effective_db = Path(db_path) if db_path else Path("data/community_memory/community_memory.db")
    curr = current_time if current_time is not None else now()
    cutoff_dt = curr - timedelta(days=cutoff_days)
    cutoff_str = format_timestamp(cutoff_dt)

    conn = open_community_memory_db(effective_db)
    try:
        cur = conn.execute(
            """
            SELECT MIN(received_at), MAX(received_at)
            FROM community_messages
            WHERE project_id = ? AND group_id = ?
              AND summarized_at IS NULL
              AND received_at <= ?
            """,
            (project_id, group_id, cutoff_str),
        )
        row = cur.fetchone()
        if not row or row[0] is None:
            return None

        earliest_str, latest_str = row[0], row[1]
    finally:
        conn.close()

    return summarize_interval(
        project_id=project_id,
        group_id=group_id,
        period_start=earliest_str,
        period_end=latest_str,
        db_path=effective_db,
        llm_client=llm_client,
    )

