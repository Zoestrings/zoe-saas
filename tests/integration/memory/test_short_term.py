import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoe.clock.clock import format_timestamp
from zoe.db.connections import open_community_memory_db
from zoe.memory.short_term import get_recent_context, record_community_message


@pytest.fixture
def memory_db(tmp_path: Path):
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
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    return db_path


@pytest.mark.automated
def test_short_term_context_returns_ten_messages_ordered_by_time(memory_db: Path) -> None:
    """Verify get_recent_context returns exactly 10 messages ordered chronologically."""
    project_id = "test_project"
    group_id = "-100123"

    base_time = datetime(2026, 11, 1, 10, 0, 0, tzinfo=timezone.utc)

    # Insert 15 messages with distinct timestamps
    for i in range(1, 16):
        msg_time = base_time + timedelta(minutes=i)
        record_community_message(
            project_id=project_id,
            group_id=group_id,
            telegram_message_id=1000 + i,
            pseudonymous_user_id=f"user_{i}",
            content=f"Message number {i}",
            received_at=msg_time,
            db_path=memory_db,
        )

    # Also insert messages for a different group and project to test isolation
    record_community_message(
        project_id="other_project",
        group_id=group_id,
        telegram_message_id=9999,
        pseudonymous_user_id="other_user",
        content="Other project message",
        received_at=base_time + timedelta(minutes=20),
        db_path=memory_db,
    )
    record_community_message(
        project_id=project_id,
        group_id="-999999",
        telegram_message_id=9998,
        pseudonymous_user_id="other_user_2",
        content="Other group message",
        received_at=base_time + timedelta(minutes=21),
        db_path=memory_db,
    )

    # Call get_recent_context with default limit=10
    recent = get_recent_context(
        project_id=project_id,
        group_id=group_id,
        limit=10,
        db_path=memory_db,
    )

    # 1. Exactly 10 messages
    assert len(recent) == 10, f"Expected 10 messages, got {len(recent)}"

    # 2. Chronological order (oldest to newest: messages 6 to 15)
    expected = [f"Message number {i}" for i in range(6, 16)]
    assert recent == expected, f"Expected {expected}, got {recent}"

    # 3. Only text strings, no metadata or identifiers
    for item in recent:
        assert isinstance(item, str)
        assert "user_" not in item
        assert "100" not in item  # telegram_message_id is not in content

