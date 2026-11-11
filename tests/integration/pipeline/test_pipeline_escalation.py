from pathlib import Path
import pytest
from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.worker.pipeline import process_message


@pytest.fixture
def pipeline_env(tmp_path: Path):
    op_path = tmp_path / "operational.db"
    conn_op = open_operational_db(op_path)
    sql_op = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_operational.sql").read_text(encoding="utf-8")
    conn_op.executescript(sql_op)
    conn_op.execute("INSERT INTO projects (project_id, name, telegram_group_id, config_json, created_at, active) VALUES ('p1', 'Test', '-100999', '{}', '2026-01-01 00:00:00', 1)")
    conn_op.commit()

    kb_path = tmp_path / "official_knowledge.db"
    conn_kb = open_official_knowledge_db(kb_path)
    sql_kb = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_knowledge.sql").read_text(encoding="utf-8")
    conn_kb.executescript(sql_kb)
    conn_kb.commit()

    mem_path = tmp_path / "community_memory.db"
    conn_mem = open_community_memory_db(mem_path)
    sql_mem = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_community_memory.sql").read_text(encoding="utf-8")
    conn_mem.executescript(sql_mem)
    conn_mem.commit()

    index_dir = tmp_path / "indexes"
    conns = {
        "operational": conn_op,
        "knowledge": conn_kb,
        "memory": conn_mem,
    }
    return conns, op_path, kb_path, mem_path, index_dir


@pytest.mark.automated
def test_pipeline_escalation_flow(pipeline_env) -> None:
    conns, op_path, kb_path, mem_path, index_dir = pipeline_env
    conn_op = conns["operational"]

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (
            'p1', 99, '-100999', 888, 'pseudo_esc_user',
            'Admin help! My wallet was hacked and drained!', NULL, 0,
            '2026-11-05 12:00:00', 'message_persisted', '2026-11-05 12:00:00', '2026-11-05 12:00:00'
        )
        """
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
    )

    # 1. Pipeline result
    assert not result.responded
    assert result.escalation_result is not None
    assert result.escalation_result.escalated
    assert result.escalation_result.severity == "critical"

    # 2. Inbox message transitioned to 'escalated'
    cur = conn_op.execute("SELECT state FROM inbox_messages WHERE id = ?", (inbox_id,))
    assert cur.fetchone()[0] == "escalated"

    # 3. Escalations table record
    cur = conn_op.execute(
        """
        SELECT id, severity, notification_status, resolution_status
        FROM escalations WHERE inbox_message_id = ?
        """,
        (inbox_id,),
    )
    esc_row = cur.fetchone()
    assert esc_row is not None
    assert esc_row[1] == "critical"
    assert esc_row[2] == "simulated"
    assert esc_row[3] == "unresolved"

    # 4. Moderator notification record
    cur = conn_op.execute(
        """
        SELECT id, simulated, state, text
        FROM moderator_notifications WHERE escalation_id = ?
        """,
        (esc_row[0],),
    )
    notif_row = cur.fetchone()
    assert notif_row is not None
    assert notif_row[1] == 1, "Moderator notification must have simulated=1"
    assert notif_row[2] == "pending"
    assert "[ESCALATION - CRITICAL]" in notif_row[3]

    # 5. Outbox messages: NO community outbox row created
    cur = conn_op.execute("SELECT COUNT(*) FROM outbox_messages WHERE inbox_message_id = ?", (inbox_id,))
    assert cur.fetchone()[0] == 0

