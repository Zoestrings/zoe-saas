import shutil
from pathlib import Path
import sqlite3
import pytest

from zoe.db.connections import ensure_databases_initialized, open_operational_db, open_official_knowledge_db, open_community_memory_db
from zoe.inbox.inbox_service import ensure_project_registered
from scripts.run_all_bots import ensure_knowledge_indexes
from zoe.knowledge.retriever import search
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.pipeline import process_message


def test_ensure_databases_initialized(tmp_path: Path):
    """Test that ensure_databases_initialized creates SQLite files and applies schemas on fresh directories."""
    data_dir = tmp_path / "data"
    ensure_databases_initialized(data_dir)

    op_db = data_dir / "operational" / "operational.db"
    kb_db = data_dir / "official_knowledge" / "official_knowledge.db"
    mem_db = data_dir / "community_memory" / "community_memory.db"

    assert op_db.exists()
    assert kb_db.exists()
    assert mem_db.exists()

    conn = sqlite3.connect(op_db)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    assert "inbox_messages" in tables
    assert "outbox_messages" in tables
    conn.close()

    conn_kb = sqlite3.connect(kb_db)
    cur_kb = conn_kb.execute("SELECT name FROM sqlite_master WHERE type='table'")
    kb_tables = [r[0] for r in cur_kb.fetchall()]
    assert "official_documents" in kb_tables
    assert "official_chunks" in kb_tables
    conn_kb.close()

    conn_mem = sqlite3.connect(mem_db)
    cur_mem = conn_mem.execute("SELECT name FROM sqlite_master WHERE type='table'")
    mem_tables = [r[0] for r in cur_mem.fetchall()]
    assert "community_messages" in tables or "community_messages" in mem_tables
    conn_mem.close()


def test_rag_founder_retrieval():
    """Verify that RAG retrieves Captain Robbie Olson for One Love founder query."""
    results = search(
        project_id="onelove",
        query="Who is the founder of the project?",
        top_k=3,
    )
    assert len(results) > 0
    combined_content = " ".join(r.content for r in results).lower()
    assert "robbie olson" in combined_content or "robert olson" in combined_content


def test_web_search_forced_off_for_project_question():
    """Verify that project_question does NOT execute web_search_fn when RAG fails."""
    called_web_search = []

    def mock_web_search(query: str):
        called_web_search.append(query)
        return [{"title": "Irrelevant", "body": "Ray Kroc founder", "href": "https://example.com"}]

    conn_op = open_operational_db(":memory:")
    conn_kb = open_official_knowledge_db(":memory:")
    conn_mem = open_community_memory_db(":memory:")
    conns = {"operational": conn_op, "knowledge": conn_kb, "community_memory": conn_mem}

    ensure_project_registered(conn_op, "onelove", name="One Love", telegram_group_id="-10012345")
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'processing', datetime('now'), datetime('now'))
        """,
        ("onelove", 1, "-10012345", 999, "user_123", "Who is the founder of this unindexed sub-branch?", None, 0, "2026-11-12 10:00:00"),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    res = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        web_search_fn=mock_web_search,
        intent="knowledge",
        enforce_accuracy_guard=True,
    )

    # Web search should NOT have been invoked for a project_question
    assert len(called_web_search) == 0, f"Web search was called unexpectedly: {called_web_search}"


def test_links_command():
    """Verify that /links command returns the official social links with inline buttons."""
    conn_op = open_operational_db(":memory:")
    conn_kb = open_official_knowledge_db(":memory:")
    conn_mem = open_community_memory_db(":memory:")
    conns = {"operational": conn_op, "knowledge": conn_kb, "community_memory": conn_mem}

    ensure_project_registered(conn_op, "onelove", name="One Love", telegram_group_id="-10012345")
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'processing', datetime('now'), datetime('now'))
        """,
        ("onelove", 2, "-10012345", 1000, "user_123", "/links", None, 0, "2026-11-12 10:00:00"),
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    res = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
    )

    cur_out = conn_op.execute("SELECT text, inline_keyboard_json FROM outbox_messages WHERE project_id = 'onelove'")
    row = cur_out.fetchone()
    assert row is not None
    out_text, out_keyboard = row[0], row[1]
    assert "https://x.com/thecaptrobbie?s=11" in out_text
    assert "https://t.me/ONELOVECoinCrew" in out_text
    assert "https://www.tiktok.com/@captain.robbie" in out_text
    assert "https://x.com/thecaptrobbie?s=11" in out_keyboard
    assert "https://t.me/ONELOVECoinCrew" in out_keyboard
    assert "https://www.tiktok.com/@captain.robbie" in out_keyboard
