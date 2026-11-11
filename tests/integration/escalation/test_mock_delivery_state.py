from pathlib import Path
import pytest
from zoe.db.connections import open_operational_db
from zoe.escalation.delivery import deliver_notification
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
def test_mock_delivery_state_transitions(op_db) -> None:
    # Insert inbox message
    cur = op_db.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at
        ) VALUES (
            'p1', 1, '-1001', 555, 'user_test',
            'Wallet hacked!', '2026-11-05 12:00:00', 'processing', '2026-11-05 12:00:00', '2026-11-05 12:00:00'
        )
        """
    )
    inbox_id = cur.lastrowid
    op_db.commit()

    esc_res = handle_escalation(
        inbox_row=inbox_id,
        db_conns={"operational": op_db},
    )
    assert esc_res.escalated
    notif_id = esc_res.notification_id
    escalation_id = esc_res.escalation_id

    # Check initial state: pending and simulated=1
    cur = op_db.execute("SELECT state, simulated FROM moderator_notifications WHERE id = ?", (notif_id,))
    notif_row = cur.fetchone()
    assert notif_row[0] == "pending"
    assert notif_row[1] == 1

    # Execute mock delivery
    result = deliver_notification(notif_id, db_conn=op_db)
    assert result["state"] == "simulated_delivered"
    assert result["notification_status"] == "simulated"

    # Confirm in database: moderator_notifications is simulated_delivered
    cur = op_db.execute("SELECT state, sent_at FROM moderator_notifications WHERE id = ?", (notif_id,))
    final_notif = cur.fetchone()
    assert final_notif[0] == "simulated_delivered"
    assert final_notif[1] is not None

    # Confirm in database: escalations.notification_status is 'simulated' (NEVER 'delivered')
    cur = op_db.execute("SELECT notification_status FROM escalations WHERE id = ?", (escalation_id,))
    final_esc = cur.fetchone()
    assert final_esc[0] == "simulated"
    assert final_esc[0] != "delivered"

