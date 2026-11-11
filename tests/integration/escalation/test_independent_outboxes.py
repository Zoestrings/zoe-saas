from pathlib import Path
import pytest
from zoe.db.connections import open_operational_db
from zoe.escalation.handler import handle_escalation


@pytest.fixture
def op_db(tmp_path: Path):
    db_path = tmp_path / "operational.db"
    conn = open_operational_db(db_path)
    sql = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_operational.sql").read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.execute("INSERT INTO projects (project_id, name, telegram_group_id, config_json, created_at, active) VALUES ('p1', 'Test', '-1001', '{}', '2026-01-01 00:00:00', 1)")
    conn.commit()
    return conn


@pytest.mark.automated
def test_independent_outboxes(op_db) -> None:
    """Delivering a message in outbox_messages has no effect on escalations or moderator_notifications."""
    # 1. Create an escalation
    cur = op_db.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at
        ) VALUES (
            'p1', 1, '-1001', 777, 'user_esc',
            'Wallet hacked!', '2026-11-05 12:00:00', 'processing', '2026-11-05 12:00:00', '2026-11-05 12:00:00'
        )
        """
    )
    inbox_id_esc = cur.lastrowid

    # 2. Create a separate normal inbox message with outbox message
    cur.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at
        ) VALUES (
            'p1', 2, '-1001', 778, 'user_normal',
            'How do I stake?', '2026-11-05 12:00:00', 'response_pending', '2026-11-05 12:00:00', '2026-11-05 12:00:00'
        )
        """
    )
    inbox_id_normal = cur.lastrowid

    cur.execute(
        """
        INSERT INTO outbox_messages (
            project_id, inbox_message_id, group_id, text, simulated,
            state, state_changed_at, created_at
        ) VALUES ('p1', ?, '-1001', 'Staking guide answer', 1, 'pending', '2026-11-05 12:00:00', '2026-11-05 12:00:00')
        """,
        (inbox_id_normal,),
    )
    outbox_id = cur.lastrowid
    op_db.commit()

    # Create the escalation for inbox_id_esc
    esc_res = handle_escalation(
        inbox_row=inbox_id_esc,
        db_conns={"operational": op_db},
    )
    assert esc_res.escalated
    escalation_id = esc_res.escalation_id
    notif_id = esc_res.notification_id

    # Simulate delivering the community outbox message
    cur.execute(
        "UPDATE outbox_messages SET state = 'sending', state_changed_at = '2026-11-05 12:01:00' WHERE id = ?",
        (outbox_id,),
    )
    cur.execute(
        "UPDATE outbox_messages SET state = 'simulated_delivered', state_changed_at = '2026-11-05 12:01:01' WHERE id = ?",
        (outbox_id,),
    )
    op_db.commit()

    # Verify that the escalation and moderator_notifications are UNTOUCHED
    cur.execute("SELECT notification_status FROM escalations WHERE id = ?", (escalation_id,))
    esc_status = cur.fetchone()[0]
    assert esc_status == "simulated"
    assert esc_status != "delivered"

    cur.execute("SELECT state FROM moderator_notifications WHERE id = ?", (notif_id,))
    mod_state = cur.fetchone()[0]
    assert mod_state == "pending"
    assert mod_state != "simulated_delivered"

