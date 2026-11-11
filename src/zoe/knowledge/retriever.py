"""Official knowledge retriever querying FAISS and SQLite."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Union

import faiss
import numpy as np

from zoe.db.connections import open_official_knowledge_db
from zoe.knowledge.model import get_embedding_model
from zoe.utils.logging import get_logger

logger = get_logger("zoe.knowledge.retriever")


@dataclass
class RetrievedChunk:
    chunk_id: int
    doc_id: int
    project_id: str
    content: str
    score: float


async def search_async(
    project_id: str,
    query: str,
    top_k: int = 2,
    db_path: Optional[Union[str, Path]] = None,
    index_dir: Optional[Union[str, Path]] = None,
    model: Optional[Any] = None,
) -> List[RetrievedChunk]:
    """Asynchronous official knowledge search offloading embedding generation to a background thread."""
    if not query or not query.strip():
        return []

    base_dir = Path(index_dir) if index_dir else Path("data/indexes")
    index_path = base_dir / project_id / "index.faiss"

    if not index_path.exists():
        return []

    try:
        index = faiss.read_index(str(index_path))
    except Exception as e:
        logger.error("Failed to read FAISS index at %s: %s", str(index_path), str(e))
        return []

    if index.ntotal == 0:
        return []

    if model is None:
        model = get_embedding_model()

    # Offload the query embedding generation to a background thread to prevent event loop freeze
    query_vec = await asyncio.to_thread(model.encode, [query], normalize_embeddings=True)
    k = min(top_k * 2, index.ntotal)
    scores, ids = index.search(query_vec.astype(np.float32), k)

    found_scores = scores[0]
    found_ids = ids[0]

    effective_db = Path(db_path) if db_path else Path("data/official_knowledge/official_knowledge.db")
    conn = open_official_knowledge_db(effective_db)

    results: List[RetrievedChunk] = []
    try:
        for chunk_id, score in zip(found_ids, found_scores):
            if chunk_id == -1:
                continue

            cur = conn.execute(
                """
                SELECT c.id, c.doc_id, c.project_id, c.content, d.quarantined
                FROM official_chunks c
                JOIN official_documents d ON c.doc_id = d.id
                WHERE c.id = ? AND c.project_id = ?
                """,
                (int(chunk_id), project_id),
            )
            row = cur.fetchone()
            if row is not None:
                quarantined = row[4]
                if quarantined == 0:
                    results.append(
                        RetrievedChunk(
                            chunk_id=row[0],
                            doc_id=row[1],
                            project_id=row[2],
                            content=row[3],
                            score=float(score),
                        )
                    )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
    finally:
        conn.close()


def search(
    project_id: str,
    query: str,
    top_k: int = 2,
    db_path: Optional[Union[str, Path]] = None,
    index_dir: Optional[Union[str, Path]] = None,
    model: Optional[Any] = None,
) -> List[RetrievedChunk]:
    """Search official knowledge for project_id, strictly enforcing quarantine exclusion."""
    if not query or not query.strip():
        return []

    base_dir = Path(index_dir) if index_dir else Path("data/indexes")
    index_path = base_dir / project_id / "index.faiss"

    if not index_path.exists():
        return []

    try:
        index = faiss.read_index(str(index_path))
    except Exception as e:
        logger.error("Failed to read FAISS index at %s: %s", str(index_path), str(e))
        return []

    if index.ntotal == 0:
        return []

    if model is None:
        model = get_embedding_model()

    query_vec = model.encode([query], normalize_embeddings=True)
    k = min(top_k * 2, index.ntotal)
    scores, ids = index.search(query_vec.astype(np.float32), k)

    found_scores = scores[0]
    found_ids = ids[0]

    effective_db = Path(db_path) if db_path else Path("data/official_knowledge/official_knowledge.db")
    conn = open_official_knowledge_db(effective_db)

    results: List[RetrievedChunk] = []
    try:
        for chunk_id, score in zip(found_ids, found_scores):
            if chunk_id == -1:
                continue

            cur = conn.execute(
                """
                SELECT c.id, c.doc_id, c.project_id, c.content, d.quarantined
                FROM official_chunks c
                JOIN official_documents d ON c.doc_id = d.id
                WHERE c.id = ? AND c.project_id = ?
                """,
                (int(chunk_id), project_id),
            )
            row = cur.fetchone()
            if row is not None:
                quarantined = row[4]
                if quarantined == 0:
                    results.append(
                        RetrievedChunk(
                            chunk_id=row[0],
                            doc_id=row[1],
                            project_id=row[2],
                            content=row[3],
                            score=float(score),
                        )
                    )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
    finally:
        conn.close()

