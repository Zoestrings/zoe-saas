"""Official knowledge ingestion, chunking, and indexing."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, List, Optional, Tuple, Union

import faiss
import numpy as np

from zoe.clock.clock import format_timestamp, now
from zoe.db.connections import open_official_knowledge_db
from zoe.knowledge.model import get_embedding_model
from zoe.knowledge.screening import screen_chunk
from zoe.utils.logging import get_logger

logger = get_logger("zoe.knowledge.ingestion")


def clean_decoded_text(text: str) -> str:
    """Remove weird spacing around slashes, hyphens, currency symbols, and punctuation.
    
    Fixes tokenizer and OCR artifacts such as:
    - 's / y' -> 's/y'
    - '500 - ton' -> '500-ton'
    - '$ onelove' -> '$onelove'
    - 'One Love ²' -> 'One Love²'
    - 'records , .' -> 'records.'
    """
    if not text:
        return ""
    # Slashes between words/numbers: 's / y' -> 's/y', 'and / or' -> 'and/or'
    text = re.sub(r"([A-Za-z0-9_])\s*/\s*([A-Za-z0-9_])", r"\1/\2", text)
    # Hyphens between words/numbers: '500 - ton' -> '500-ton', 'pump - and - dump' -> 'pump-and-dump'
    text = re.sub(r"([A-Za-z0-9_])\s*-\s*([A-Za-z0-9_])", r"\1-\2", text)
    # Space after currency symbols: '$ ONELOVE' -> '$ONELOVE', '$ 50' -> '$50'
    text = re.sub(r"(\$|€|£)\s+([A-Za-z0-9_])", r"\1\2", text)
    # Space before superscripts and special units: 'One Love ²' -> 'One Love²'
    text = re.sub(r"\s+([²³°%])", r"\1", text)
    # Commas followed by dots or broken punctuation spacing: 'records , .' -> 'records.'
    text = re.sub(r"\s*,\s*\.", ".", text)
    text = re.sub(r"\s+([,.:;?!])", r"\1", text)
    # Multiple whitespace to single space
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


@dataclass
class IngestResult:
    doc_id: int
    filename: str
    chunk_count: int
    quarantined: bool
    quarantine_reason: Optional[str] = None


def chunk_text(
    text: str,
    tokenizer: Any,
    chunk_size: int = 200,
    overlap: int = 35,
    min_chunk_size: int = 180,
) -> List[Tuple[str, int]]:
    """Tokenize and split text into chunks targeting 180-220 tokens with 30-40 token overlap."""
    text = clean_decoded_text(text)
    tokens = tokenizer.encode(text, add_special_tokens=False)
    n = len(tokens)
    if n == 0:
        return []

    # If document fits within max chunk bounds (<= 220)
    if n <= chunk_size + 20:
        chunk_str = clean_decoded_text(tokenizer.decode(tokens, skip_special_tokens=True).strip())
        return [(chunk_str, n)] if chunk_str else []

    stride = chunk_size - overlap
    chunks: List[Tuple[str, int]] = []
    start = 0

    while start < n:
        end = min(start + chunk_size, n)
        # If tail fragment is smaller than min_chunk_size and document is large enough,
        # adjust start backwards to ensure final chunk satisfies token count bounds.
        if (n - start) < min_chunk_size and start > 0 and n >= chunk_size:
            start = max(0, n - chunk_size)
            chunk_tokens = tokens[start:n]
            chunk_str = clean_decoded_text(tokenizer.decode(chunk_tokens, skip_special_tokens=True).strip())
            if chunk_str:
                chunks.append((chunk_str, len(chunk_tokens)))
            break

        chunk_tokens = tokens[start:end]
        chunk_str = clean_decoded_text(tokenizer.decode(chunk_tokens, skip_special_tokens=True).strip())
        if chunk_str:
            chunks.append((chunk_str, len(chunk_tokens)))

        if end == n:
            break

        start += stride

    return chunks


def rebuild_faiss_index(
    project_id: str,
    conn: Any,
    index_dir: Optional[Union[str, Path]] = None,
    model: Optional[Any] = None,
) -> Path:
    """Rebuild FAISS index for all non-quarantined chunks of a given project_id."""
    if model is None:
        model = get_embedding_model()

    base_dir = Path(index_dir) if index_dir else Path("data/indexes")
    index_path = base_dir / project_id / "index.faiss"
    index_path.parent.mkdir(parents=True, exist_ok=True)

    cur = conn.execute(
        """
        SELECT c.id, c.content
        FROM official_chunks c
        JOIN official_documents d ON c.doc_id = d.id
        WHERE c.project_id = ? AND d.quarantined = 0
        ORDER BY c.id ASC
        """,
        (project_id,),
    )
    rows = cur.fetchall()

    dimension = 384
    base_index = faiss.IndexFlatIP(dimension)
    index = faiss.IndexIDMap2(base_index)

    if rows:
        chunk_ids = np.array([r[0] for r in rows], dtype=np.int64)
        chunk_texts = [r[1] for r in rows]
        embeddings = model.encode(chunk_texts, normalize_embeddings=True)
        index.add_with_ids(embeddings.astype(np.float32), chunk_ids)

    faiss.write_index(index, str(index_path))
    logger.info("Rebuilt FAISS index for project %s at %s with %s chunks", project_id, str(index_path), len(rows))
    return index_path


def ingest_document(
    filepath: Union[str, Path],
    project_id: str,
    db_path: Optional[Union[str, Path]] = None,
    index_dir: Optional[Union[str, Path]] = None,
    source_url: Optional[str] = None,
    model: Optional[Any] = None,
) -> IngestResult:
    """Ingest a text document into official knowledge, screening for prompt injection and indexing in FAISS."""
    target_path = Path(filepath)
    if not target_path.exists():
        raise FileNotFoundError(f"Document file not found: {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        text = f.read()

    filename = target_path.name
    if model is None:
        model = get_embedding_model()

    tokenizer = model.tokenizer
    chunks = chunk_text(text, tokenizer)

    quarantined = False
    quarantine_reason = None
    for chunk_content, _ in chunks:
        if screen_chunk(chunk_content):
            quarantined = True
            quarantine_reason = "Prompt injection detected in chunk content"
            break

    effective_db = Path(db_path) if db_path else Path("data/official_knowledge/official_knowledge.db")
    conn = open_official_knowledge_db(effective_db)

    try:
        conn.execute(
            "DELETE FROM official_documents WHERE project_id = ? AND filename = ?",
            (project_id, filename),
        )

        ingested_timestamp = format_timestamp(now())
        cur = conn.execute(
            """
            INSERT INTO official_documents (
                project_id, filename, source_url, ingested_at, quarantined, quarantine_reason
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                filename,
                source_url,
                ingested_timestamp,
                1 if quarantined else 0,
                quarantine_reason,
            ),
        )
        doc_id = cur.lastrowid

        for idx, (chunk_content, token_count) in enumerate(chunks):
            cleaned_content = clean_decoded_text(chunk_content)
            chunk_cur = conn.execute(
                """
                INSERT INTO official_chunks (
                    doc_id, project_id, chunk_index, content, token_count, faiss_vector_id
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (doc_id, project_id, idx, cleaned_content, token_count, -1),
            )
            chunk_id = chunk_cur.lastrowid
            conn.execute(
                "UPDATE official_chunks SET faiss_vector_id = ? WHERE id = ?",
                (chunk_id, chunk_id),
            )

        conn.commit()

        rebuild_faiss_index(project_id, conn, index_dir=index_dir, model=model)

        return IngestResult(
            doc_id=doc_id,
            filename=filename,
            chunk_count=len(chunks),
            quarantined=quarantined,
            quarantine_reason=quarantine_reason,
        )
    finally:
        conn.close()

