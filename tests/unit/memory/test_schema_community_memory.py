import pytest
from pathlib import Path
from zoe.db.connections import open_community_memory_db


@pytest.mark.automated
def test_schema_community_memory_applies(tmp_path: Path) -> None:
    db_path = tmp_path / "community_memory.db"
    conn = open_community_memory_db(db_path)

    schema_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "zoe"
        / "db"
        / "schema_community_memory.sql"
    )

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    conn.executescript(sql)
    conn.commit()

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = {row[0] for row in cur.fetchall()}
    conn.close()

    expected_tables = {
        "community_messages",
        "community_memory_summaries",
    }

    assert tables == expected_tables, f"Expected {expected_tables}, got {tables}"

