import pytest
from pathlib import Path
from zoe.db.connections import open_official_knowledge_db


@pytest.mark.automated
def test_schema_knowledge_applies(tmp_path: Path) -> None:
    db_path = tmp_path / "knowledge.db"
    conn = open_official_knowledge_db(db_path)

    schema_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "zoe"
        / "db"
        / "schema_knowledge.sql"
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
        "official_documents",
        "official_chunks",
    }

    assert tables == expected_tables, f"Expected {expected_tables}, got {tables}"

