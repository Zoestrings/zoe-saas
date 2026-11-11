"""Integration tests auditing source citations from official documents."""

from pathlib import Path
import pytest

from zoe.conversation.prompt_builder import DEFAULT_ZOE_IDENTITY_PROMPT
from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.knowledge.ingestion import ingest_document
from zoe.knowledge.model import get_embedding_model
from zoe.llm.mock import MockLLMClient
from zoe.worker.pipeline import process_message

PROJECT_ID = "p_citations"
GROUP_ID = "-100778"


@pytest.fixture(scope="module")
def shared_model():
    """Load embedding model once for citation testing."""
    return get_embedding_model("all-MiniLM-L6-v2")


@pytest.fixture
def citation_env(tmp_path: Path, shared_model):
    """Set up test environment with verified official knowledge and FAISS index."""
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
        VALUES (?, 'Citation Test', ?, '{"token_address": "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf", "participation": {"respond_to_casual": true}}', '2026-01-01 00:00:00', 1)
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
    conn_kb.close()

    index_dir = tmp_path / "indexes"
    doc_file = tmp_path / "staking_guide.txt"
    doc_file.write_text(
        "Hummingbird protocol specifies a 14-day unbonding period for staked tokens.",
        encoding="utf-8",
    )

    ingest_document(
        filepath=doc_file,
        project_id=PROJECT_ID,
        db_path=kb_path,
        index_dir=index_dir,
        model=shared_model,
    )

    mem_path = tmp_path / "community_memory.db"
    conn_mem = open_community_memory_db(mem_path)
    sql_mem = (
        Path(__file__).resolve().parent.parent.parent
        / "src/zoe/db/schema_community_memory.sql"
    ).read_text(encoding="utf-8")
    conn_mem.executescript(sql_mem)

    conns = {
        "operational": conn_op,
        "memory": conn_mem,
    }

    yield {
        "conns": conns,
        "op_path": op_path,
        "kb_path": kb_path,
        "mem_path": mem_path,
        "index_dir": index_dir,
        "tmp_path": tmp_path,
        "model": shared_model,
    }

    conn_op.close()
    conn_mem.close()


def test_source_citation_includes_official_phrase(citation_env):
    """Verify that when answering from official knowledge, Zoe includes the phrase 'official'."""
    conns = citation_env["conns"]
    conn_op = conns["operational"]
    kb_path = citation_env["kb_path"]
    mem_path = citation_env["mem_path"]
    index_dir = citation_env["index_dir"]
    model = citation_env["model"]

    query = "What is the unbonding period?"

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES (?, 1, ?, 980, 'user_staker', ?, 0, 'message_persisted', '2026-11-09 12:20:00', '2026-11-09 12:20:00', '2026-11-09 12:20:00')
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
        index_dir=index_dir,
        model=model,
        simulated=True,
    )

    assert result.responded is True
    # Response must cite official records/documents
    assert "official" in result.response_text.lower()
    assert "unbonding" in result.response_text.lower() or "14-day" in result.response_text.lower()


def test_prompt_retains_jarvis_persona_and_web3_slang():
    """Verify prompt builder instructions retain JARVIS persona, Web3 slang, and citations."""
    prompt = DEFAULT_ZOE_IDENTITY_PROMPT
    assert "JARVIS" in prompt
    assert "GM" in prompt
    assert "WAGMI" in prompt
    assert "FUD" in prompt
    assert "official" in prompt.lower()
    assert "[CONVERSATION HISTORY]" in prompt or "CONVERSATION HISTORY" in prompt or "Conversational Flow" in prompt
