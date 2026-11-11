from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from zoe.db.connections import open_operational_db
from zoe.escalation.handler import handle_escalation


@pytest.fixture
def op_db(tmp_path: Path):
    db_path = tmp_path / "operational.db"
    conn = open_operational_db(db_path)
    schema_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "zoe"
        / "db"
        / "schema_operational.sql"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.execute(
        "INSERT INTO projects (project_id, name, telegram_group_id, config_json, created_at, active) VALUES ('p1', 'Test', '-1001', '{}', '2026-01-01 00:00:00', 1)"
    )
    conn.commit()
    return conn


@pytest.mark.automated
def test_one_escalation_per_user_per_hour(op_db) -> None:
    t0 = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)

    # Insert inbox row 1 for user_A
    cur = op_db.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at
        ) VALUES (
            'p1', 1, '-1001', 101, 'user_A',
            'Compromised wallet help!', '2026-11-05 12:00:00', 'processing', '2026-11-05 12:00:00', '2026-11-05 12:00:00'
        )
        """
    )
    inbox_id_1 = cur.lastrowid
    op_db.commit()

    # First escalation by user_A succeeds
    res1 = handle_escalation(
        inbox_row=inbox_id_1,
        db_conns={"operational": op_db},
        current_time=t0,
    )
    assert res1.escalated
    assert res1.escalation_id is not None
    assert res1.severity == "critical"

    # Insert inbox row 2 for user_A 15 minutes later (< 1 hour)
    cur = op_db.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at
        ) VALUES (
            'p1', 2, '-1001', 102, 'user_A',
            'Another urgent alert!', '2026-11-05 12:15:00', 'processing', '2026-11-05 12:15:00', '2026-11-05 12:15:00'
        )
        """
    )
    inbox_id_2 = cur.lastrowid
    op_db.commit()

    # Second escalation by user_A within 1 hour is rate limited
    t_15m = t0 + timedelta(minutes=15)
    res2 = handle_escalation(
        inbox_row=inbox_id_2,
        db_conns={"operational": op_db},
        current_time=t_15m,
    )
    assert not res2.escalated
    assert res2.reason == "rate_limit_exceeded"

    # Insert inbox row 3 for user_B at the same time: should succeed
    cur = op_db.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, message_timestamp, state, state_changed_at, created_at
        ) VALUES (
            'p1', 3, '-1001', 103, 'user_B',
            'Hacked wallet help!', '2026-11-05 12:15:00', 'processing', '2026-11-05 12:15:00', '2026-11-05 12:15:00'
        )
        """
    )
    inbox_id_3 = cur.lastrowid
    op_db.commit()

    res3 = handle_escalation(
        inbox_row=inbox_id_3,
        db_conns={"operational": op_db},
        current_time=t_15m,
    )
    assert res3.escalated
    assert res3.escalation_id is not None

