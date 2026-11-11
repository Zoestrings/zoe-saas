"""Interface separation between Community Memory and Official Knowledge."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from zoe.db.connections import open_community_memory_db, open_official_knowledge_db
from zoe.memory.short_term import get_recent_context


class CommunityMemoryView:
    """View interface for community memory data.

    STRUCTURAL ISOLATION GUARANTEE:
    This class and its underlying module interact strictly with community_memory.db.
    It has no code paths, methods, or imports referencing official_knowledge.db
    or official search systems.
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = Path(db_path) if db_path else Path("data/community_memory/community_memory.db")

    def get_recent_messages(self, project_id: str, group_id: str, limit: int = 10) -> List[str]:
        """Retrieve recent community discussion messages for short-term context."""
        return get_recent_context(
            project_id=project_id,
            group_id=group_id,
            limit=limit,
            db_path=self.db_path,
        )

    def get_latest_summaries(self, project_id: str, group_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve recent community summaries."""
        conn = open_community_memory_db(self.db_path)
        try:
            cur = conn.execute(
                """
                SELECT id, summary_text, period_start, period_end, created_at
                FROM community_memory_summaries
                WHERE project_id = ? AND group_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (project_id, group_id, limit),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "summary_text": r[1],
                    "period_start": r[2],
                    "period_end": r[3],
                    "created_at": r[4],
                }
                for r in rows
            ]
        finally:
            conn.close()


class OfficialKnowledgeView:
    """View interface for official knowledge data."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = Path(db_path) if db_path else Path("data/official_knowledge/official_knowledge.db")

    def get_official_documents(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieve list of official non-quarantined documents."""
        conn = open_official_knowledge_db(self.db_path)
        try:
            cur = conn.execute(
                """
                SELECT id, filename, source_url, ingested_at
                FROM official_documents
                WHERE project_id = ? AND quarantined = 0
                ORDER BY id ASC
                """,
                (project_id,),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "filename": r[1],
                    "source_url": r[2],
                    "ingested_at": r[3],
                }
                for r in rows
            ]
        finally:
            conn.close()
