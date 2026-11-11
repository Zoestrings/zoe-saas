"""Unit tests for the Proactive Sentiment Radar (JARVIS Mode)."""

from pathlib import Path
import sqlite3
import faiss
import numpy as np
import pytest

from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.llm.mock import MockLLMClient
from zoe.memory.short_term import record_community_message
from zoe.worker.pipeline import process_message, trigger_proactive_intervention

PROJECT_ID = "p1"
GROUP_ID = "-100999"


class MockEmbeddingModel:
    """Fast in-memory mock embedding model matching indexed vectors with high similarity."""

    def __init__(self, high_similarity: bool = True, dim: int = 384):
        self.high_similarity = high_similarity
        self.dim = dim

    def encode(self, texts, normalize_embeddings: bool = True):
        n = len(texts)
        if self.high_similarity:
            arr = np.ones((n, self.dim), dtype=np.float32)
        else:
            arr = np.zeros((n, self.dim), dtype=np.float32)
            arr[:, 0] = 1.0
        if normalize_embeddings:
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            arr = arr / norms
        return arr


@pytest.fixture
def radar_env(tmp_path: Path):
    """Set up operational, knowledge, and memory databases with indexed documents."""
    # 1. Operational DB
    op_path = tmp_path / "operational.db"
    conn_op = open_operational_db(op_path)
    sql_op = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_operational.sql").read_text(encoding="utf-8")
    conn_op.executescript(sql_op)
    conn_op.execute(
        "INSERT INTO projects (project_id, name, telegram_group_id, config_json, created_at, active) "
        "VALUES ('p1', 'Hummingbird Test', '-100999', '{\"token_address\": \"EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf\"}', '2026-01-01 00:00:00', 1)"
    )
    conn_op.commit()

    # 2. Knowledge DB
    kb_path = tmp_path / "official_knowledge.db"
    conn_kb = open_official_knowledge_db(kb_path)
    sql_kb = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_knowledge.sql").read_text(encoding="utf-8")
    conn_kb.executescript(sql_kb)

    conn_kb.execute(
        """
        INSERT INTO official_documents (id, project_id, filename, source_url, ingested_at, quarantined)
        VALUES (1, 'p1', 'liquidity_info.txt', 'https://hummingbirdco.io', '2026-01-01 00:00:00', 0)
        """
    )
    conn_kb.execute(
        """
        INSERT INTO official_chunks (id, doc_id, project_id, chunk_index, content, token_count, faiss_vector_id)
        VALUES (
            1, 1, 'p1', 0,
            'Hummingbird maintains verified liquidity pools on Raydium. Smart contracts are fully audited and secure.',
            20, 1
        )
        """
    )
    conn_kb.commit()

    # 3. FAISS index
    index_dir = tmp_path / "indexes"
    index_dir.mkdir(parents=True, exist_ok=True)
    idx = faiss.IndexFlatIP(384)
    v = np.ones((1, 384), dtype=np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    idx.add(v)
    faiss.write_index(idx, str(index_dir / "knowledge.index"))

    # 4. Community Memory DB
    mem_path = tmp_path / "community_memory.db"
    conn_mem = open_community_memory_db(mem_path)
    sql_mem = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_community_memory.sql").read_text(encoding="utf-8")
    conn_mem.executescript(sql_mem)
    conn_mem.commit()

    conns = {
        "operational": conn_op,
        "knowledge": conn_kb,
        "memory": conn_mem,
    }

    yield conns, op_path, kb_path, mem_path, index_dir, tmp_path

    conn_op.close()
    conn_kb.close()
    conn_mem.close()


def test_proactive_intervention_queues_to_outbox_when_panicked_without_user_prompt(radar_env):
    """Assert that the proactive trigger successfully queues a message to outbox without a user prompt."""
    conns, op_path, kb_path, mem_path, index_dir, tmp_path = radar_env
    conn_op = conns["operational"]

    # 1. Feed community memory 5 panic messages
    panic_messages = [
        "I got hacked!",
        "The price is crashing hard!",
        "Total scam, the dev dumped!",
        "Is this project dead? The liquidity is dropping!",
        "Sell now before it goes to zero!",
    ]
    for i, msg in enumerate(panic_messages, start=1):
        record_community_message(
            project_id=PROJECT_ID,
            group_id=GROUP_ID,
            telegram_message_id=i,
            pseudonymous_user_id=f"user_{i}",
            content=msg,
            db_path=mem_path,
        )

    # 2. Trigger proactive intervention autonomously without user prompt
    outbox_id = trigger_proactive_intervention(
        project_id=PROJECT_ID,
        group_id=GROUP_ID,
        db_conns=conns,
        op_db_path=op_path,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        index_dir=index_dir,
        model=MockEmbeddingModel(high_similarity=True),
        simulated=True,
    )

    # 3. Assert outbox message queued successfully
    assert outbox_id is not None
    assert outbox_id > 0

    # 4. Verify outbox message state and content
    cur = conn_op.execute("SELECT id, text, state, simulated, reply_to_message_id FROM outbox_messages WHERE id = ?", (outbox_id,))
    row = cur.fetchone()
    assert row is not None
    assert row[2] == "pending"
    assert row[3] == 1  # simulated
    assert row[4] is None  # broadcast to group without specific reply
    assert "liquidity" in row[1].lower() or "detecting some concern" in row[1].lower()


def test_proactive_intervention_ignores_calm_chat(radar_env):
    """Assert that normal calm conversation does not trigger proactive intervention."""
    conns, op_path, kb_path, mem_path, index_dir, tmp_path = radar_env
    conn_op = conns["operational"]

    # Feed community memory calm messages
    calm_messages = [
        "gm everyone",
        "working on my node setup",
        "sun is shining today",
        "nice project docs",
        "all good here",
    ]
    for i, msg in enumerate(calm_messages, start=1):
        record_community_message(
            project_id=PROJECT_ID,
            group_id=GROUP_ID,
            telegram_message_id=i,
            pseudonymous_user_id=f"user_{i}",
            content=msg,
            db_path=mem_path,
        )

    outbox_id = trigger_proactive_intervention(
        project_id=PROJECT_ID,
        group_id=GROUP_ID,
        db_conns=conns,
        op_db_path=op_path,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        index_dir=index_dir,
        model=MockEmbeddingModel(high_similarity=True),
    )

    assert outbox_id is None

    # Verify no message was queued
    cur = conn_op.execute("SELECT COUNT(*) FROM outbox_messages")
    assert cur.fetchone()[0] == 0


def test_process_message_intercepts_unaddressed_fud_and_responds(radar_env):
    """Assert that process_message overrides decision to respond proactively when chat is panicked."""
    conns, op_path, kb_path, mem_path, index_dir, tmp_path = radar_env
    conn_op = conns["operational"]

    # Feed prior panic messages in memory
    prior_fud = [
        "Total scam!",
        "The dev dumped his tokens!",
        "Liquidity is dropping fast!",
    ]
    for i, msg in enumerate(prior_fud, start=1):
        record_community_message(
            project_id=PROJECT_ID,
            group_id=GROUP_ID,
            telegram_message_id=i,
            pseudonymous_user_id=f"user_{i}",
            content=msg,
            db_path=mem_path,
        )

    # An incoming message that does NOT address Zoe directly and is casual (would normally remain silent)
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES ('p1', 101, '-100999', 501, 'user_x', 'lol rip this project dev dumped', NULL, 0, '2026-11-05 12:00:00', 'message_persisted', '2026-11-05 12:00:00', '2026-11-05 12:00:00')
        """
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        op_db_path=op_path,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        index_dir=index_dir,
        model=MockEmbeddingModel(high_similarity=True),
        simulated=True,
    )

    # Proactive radar stepped in
    assert result.responded is True
    assert result.decision.decision == "respond"
    assert "proactive_fud_intervention" in result.decision.reason
    assert result.outbox_id is not None


def test_direct_question_without_mention_triggers_response(radar_env):
    """Assert that a direct question (e.g. 'what is the token address') responds without an @mention."""
    conns, op_path, kb_path, mem_path, index_dir, tmp_path = radar_env
    conn_op = conns["operational"]

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES ('p1', 102, '-100999', 502, 'user_y', 'what is the token address', NULL, 0, '2026-11-05 12:00:00', 'message_persisted', '2026-11-05 12:00:00', '2026-11-05 12:00:00')
        """
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        op_db_path=op_path,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        index_dir=index_dir,
        model=MockEmbeddingModel(high_similarity=True),
        simulated=True,
    )

    # Must respond to direct question without being tagged
    assert result.responded is True
    assert result.decision.decision == "respond"
    assert result.decision.reason == "direct_question_answered"
    assert result.outbox_id is not None


def test_proactive_cooldown_suppresses_rapid_second_intervention(radar_env):
    """Assert that a second proactive intervention within 10 minutes is suppressed by cooldown."""
    conns, op_path, kb_path, mem_path, index_dir, tmp_path = radar_env

    # 1. Feed panic messages
    for i, msg in enumerate(["Scam!", "Dev dumped!", "Liquidity dropping!", "Hacked!", "Crash!"], start=1):
        record_community_message(
            project_id=PROJECT_ID,
            group_id=GROUP_ID,
            telegram_message_id=i,
            pseudonymous_user_id=f"u_{i}",
            content=msg,
            db_path=mem_path,
        )

    # 2. First intervention succeeds
    first_id = trigger_proactive_intervention(
        project_id=PROJECT_ID,
        group_id=GROUP_ID,
        db_conns=conns,
        op_db_path=op_path,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        index_dir=index_dir,
        model=MockEmbeddingModel(high_similarity=True),
        simulated=True,
    )
    assert first_id is not None

    # 3. Second intervention immediately after is suppressed by the 10-minute cooldown
    second_id = trigger_proactive_intervention(
        project_id=PROJECT_ID,
        group_id=GROUP_ID,
        db_conns=conns,
        op_db_path=op_path,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        index_dir=index_dir,
        model=MockEmbeddingModel(high_similarity=True),
        simulated=True,
    )
    assert second_id is None

