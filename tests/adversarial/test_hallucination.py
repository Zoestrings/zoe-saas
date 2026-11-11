"""Adversarial tests verifying RAG fidelity and Accuracy Guard protection against hallucinations."""

from pathlib import Path
import re
import pytest

from zoe.conversation.router import route_intent
from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.llm.mock import MockLLMClient
from zoe.worker.pipeline import process_message

PROJECT_ID = "p_hallucination"
GROUP_ID = "-100777"


@pytest.fixture
def rag_fidelity_env(tmp_path: Path):
    """Set up test environment where RAG knowledge does NOT contain unreleased token info."""
    op_path = tmp_path / "operational.db"
    conn_op = open_operational_db(op_path)
    sql_op = (
        Path(__file__).resolve().parent.parent.parent
        / "src/zoe/db/schema_operational.sql"
    ).read_text(encoding="utf-8")
    conn_op.executescript(sql_op)

    conn_op.execute(
        """
        INSERT INTO projects (project_id, name, telegram_group_id, config_json, created_at, active)
        VALUES (?, 'RAG Fidelity Test', ?, '{"token_address": "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf", "participation": {"respond_to_casual": true}}', '2026-01-01 00:00:00', 1)
        """,
        (PROJECT_ID, GROUP_ID),
    )
    conn_op.commit()

    kb_path = tmp_path / "official_knowledge.db"
    conn_kb = open_official_knowledge_db(kb_path)
    sql_kb = (
        Path(__file__).resolve().parent.parent.parent
        / "src/zoe/db/schema_knowledge.sql"
    ).read_text(encoding="utf-8")
    conn_kb.executescript(sql_kb)

    # Insert only standard unrelated docs into knowledge DB (nothing about unreleased tokens)
    conn_kb.execute(
        """
        INSERT INTO official_documents (id, project_id, filename, source_url, ingested_at, quarantined)
        VALUES (1, ?, 'hummingbird_info.txt', 'https://hummingbirdco.io', '2026-01-01 00:00:00', 0)
        """,
        (PROJECT_ID,),
    )
    conn_kb.execute(
        """
        INSERT INTO official_chunks (doc_id, project_id, chunk_index, content, token_count, faiss_vector_id)
        VALUES (1, ?, 0, 'Hummingbird is an autonomous decentralized advertising network on Solana.', 12, 0)
        """,
        (PROJECT_ID,),
    )
    conn_kb.commit()

    mem_path = tmp_path / "community_memory.db"
    conn_mem = open_community_memory_db(mem_path)
    sql_mem = (
        Path(__file__).resolve().parent.parent.parent
        / "src/zoe/db/schema_community_memory.sql"
    ).read_text(encoding="utf-8")
    conn_mem.executescript(sql_mem)

    conns = {
        "operational": conn_op,
        "knowledge": conn_kb,
        "memory": conn_mem,
    }

    yield {
        "conns": conns,
        "op_path": op_path,
        "kb_path": kb_path,
        "mem_path": mem_path,
        "tmp_path": tmp_path,
    }

    conn_op.close()
    conn_kb.close()
    conn_mem.close()


def test_hallucination_accuracy_guard_fallback(rag_fidelity_env):
    """Ask the pipeline:
    'What is the contract address for the new unreleased token?'
    
    Ensure this is NOT in the RAG docs.
    Assert:
    - Intent routes to knowledge
    - The pipeline returns the Accuracy Guard fallback ('I don't have that in my official documents yet')
    - Does NOT invent or hallucinate a contract address.
    """
    conns = rag_fidelity_env["conns"]
    conn_op = conns["operational"]
    kb_path = rag_fidelity_env["kb_path"]
    mem_path = rag_fidelity_env["mem_path"]

    query = "What is the contract address for the new unreleased token?"

    # 1. Verify router routes this to knowledge (not native DexScreener token)
    intent = route_intent(query)
    assert intent == "knowledge"

    # 2. Process message through pipeline with no external web results
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 1, ?, 950, 'user_inquisitive', ?, 0, 'message_persisted', '2026-11-09 12:10:00', '2026-11-09 12:10:00', '2026-11-09 12:10:00')
        """,
        (PROJECT_ID, GROUP_ID, query),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        web_search_fn=lambda q: [],  # No web results found
        enforce_accuracy_guard=True,
        simulated=True,
    )

    assert result.responded is True
    assert "I don't have that in my official documents yet" in result.response_text

    # Verify no fabricated contract address (EVM 0x... or Solana Base58 32-44 chars)
    solana_ca_regex = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
    evm_ca_regex = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
    assert not evm_ca_regex.search(result.response_text)
    assert not solana_ca_regex.search(result.response_text)
