import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoe.clock.clock import format_timestamp, parse_timestamp
from zoe.db.connections import open_community_memory_db
from zoe.llm.mock import MockLLMClient
from zoe.memory.short_term import record_community_message
from zoe.memory.summarizer import (
    SUMMARIZER_SYSTEM_PROMPT,
    summarize_interval,
    summarize_rolling_window,
)


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
def test_summarizer_attribution_rule(memory_db: Path) -> None:
    """Verify that rumors are framed with attribution and never stated as definitive facts."""
    project_id = "alpha_proj"
    group_id = "-100777"
    t0 = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Ingest a community rumor
    record_community_message(
        project_id=project_id,
        group_id=group_id,
        telegram_message_id=501,
        pseudonymous_user_id="anon_user",
        content="Partnership with X confirmed! Big announcement tomorrow!",
        received_at=t0,
        db_path=memory_db,
    )
    record_community_message(
        project_id=project_id,
        group_id=group_id,
        telegram_message_id=502,
        pseudonymous_user_id="anon_user_2",
        content="Can anyone confirm if the partnership is real?",
        received_at=t0 + timedelta(minutes=5),
        db_path=memory_db,
    )

    mock_client = MockLLMClient()
    summary = summarize_interval(
        project_id=project_id,
        group_id=group_id,
        period_start=t0 - timedelta(minutes=1),
        period_end=t0 + timedelta(minutes=10),
        db_path=memory_db,
        llm_client=mock_client,
    )

    # 1. Verify attribution phrasing in output
    assert "Several members discussed" in summary or "Community members discussed" in summary
    assert "potential partnership" in summary

    # 2. Verify it NEVER asserts the partnership as confirmed fact
    assert "Partnership with X confirmed" not in summary

    # 3. Verify system prompt passed to LLM enforced Spec §13.6.2 attribution rules
    assert len(mock_client.calls) == 1
    system_prompt = mock_client.calls[0]["system_prompt"]
    assert "ATTRIBUTION RULE" in system_prompt
    assert "Never state community rumors" in system_prompt
    assert "Several members discussed" in system_prompt


@pytest.mark.automated
def test_summarizer_rolling_window(memory_db: Path) -> None:
    """Verify messages older than 14 days are marked summarized and summary is saved."""
    project_id = "beta_proj"
    group_id = "-100888"

    reference_now = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)

    # Message 1: 20 days old (older than 14 days) -> should be summarized
    t_old_1 = reference_now - timedelta(days=20)
    id_old_1 = record_community_message(
        project_id=project_id,
        group_id=group_id,
        telegram_message_id=101,
        pseudonymous_user_id="old_user_1",
        content="Old discussion from 20 days ago regarding validator fees.",
        received_at=t_old_1,
        db_path=memory_db,
    )

    # Message 2: 15 days old (older than 14 days) -> should be summarized
    t_old_2 = reference_now - timedelta(days=15)
    id_old_2 = record_community_message(
        project_id=project_id,
        group_id=group_id,
        telegram_message_id=102,
        pseudonymous_user_id="old_user_2",
        content="Old discussion from 15 days ago regarding testnet rewards.",
        received_at=t_old_2,
        db_path=memory_db,
    )

    # Message 3: 5 days old (newer than 14 days) -> should NOT be summarized
    t_recent = reference_now - timedelta(days=5)
    id_recent = record_community_message(
        project_id=project_id,
        group_id=group_id,
        telegram_message_id=103,
        pseudonymous_user_id="recent_user",
        content="Recent active discussion from 5 days ago.",
        received_at=t_recent,
        db_path=memory_db,
    )

    # Run rolling window summarization with cutoff_days=14
    summary = summarize_rolling_window(
        project_id=project_id,
        group_id=group_id,
        cutoff_days=14,
        db_path=memory_db,
        current_time=reference_now,
    )

    assert summary is not None
    assert len(summary) > 0

    conn = open_community_memory_db(memory_db)
    try:
        # Check messages: old messages must have summarized_at set
        cur = conn.execute(
            "SELECT id, summarized_at FROM community_messages WHERE id IN (?, ?)",
            (id_old_1, id_old_2),
        )
        for row in cur.fetchall():
            assert row[1] is not None, f"Message {row[0]} should have been marked summarized"

        # Recent message must remain unsummarized (summarized_at is NULL)
        cur = conn.execute(
            "SELECT summarized_at FROM community_messages WHERE id = ?",
            (id_recent,),
        )
        recent_summarized_at = cur.fetchone()[0]
        assert recent_summarized_at is None, "Recent message (<14 days) must NOT be marked summarized"

        # Check summary saved in community_memory_summaries
        cur = conn.execute(
            "SELECT id, project_id, group_id, summary_text, period_start, period_end FROM community_memory_summaries WHERE project_id = ?",
            (project_id,),
        )
        saved_summaries = cur.fetchall()
        assert len(saved_summaries) == 1
        saved = saved_summaries[0]
        assert saved[1] == project_id
        assert saved[2] == group_id
        assert saved[3] == summary
        assert saved[4] == format_timestamp(t_old_1)
        assert saved[5] == format_timestamp(t_old_2)
    finally:
        conn.close()

