import pytest
from pathlib import Path
from zoe.db.connections import (
    open_operational_db,
    open_official_knowledge_db,
    open_community_memory_db,
)


@pytest.mark.automated
def test_pragma_journal_mode_all_db(tmp_path: Path) -> None:
    op_path = tmp_path / "op.db"
    kb_path = tmp_path / "kb.db"
    mem_path = tmp_path / "mem.db"

    conn_op = open_operational_db(op_path)
    conn_kb = open_official_knowledge_db(kb_path)
    conn_mem = open_community_memory_db(mem_path)

    try:
        cur_op = conn_op.execute("PRAGMA journal_mode")
        assert cur_op.fetchone()[0].lower() == "wal"

        cur_kb = conn_kb.execute("PRAGMA journal_mode")
        assert cur_kb.fetchone()[0].lower() == "wal"

        cur_mem = conn_mem.execute("PRAGMA journal_mode")
        assert cur_mem.fetchone()[0].lower() == "wal"
    finally:
        conn_op.close()
        conn_kb.close()
        conn_mem.close()

