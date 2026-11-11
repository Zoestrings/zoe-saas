import pytest
from pathlib import Path
from zoe.db.connections import open_operational_db


@pytest.mark.automated
def test_schema_applies(tmp_path: Path) -> None:
    db_path = tmp_path / "operational.db"
    conn = open_operational_db(db_path)

    schema_path = (
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "zoe"
        / "db"
        / "schema_operational.sql"
    )

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Applying schema must not raise any exception
    conn.executescript(sql)
    conn.commit()

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = {row[0] for row in cur.fetchall()}
    conn.close()

    expected_tables = {
        "projects",
        "polling_state",
        "update_receipts",
        "inbox_messages",
        "participation_log",
        "responses",
        "outbox_messages",
        "operator_audit",
        "escalations",
        "moderator_notifications",
    }

    assert tables == expected_tables, f"Expected exactly {expected_tables}, got {tables}"

