"""Unit tests for Dynamic Bot Identities (White-Label SaaS).

Tests:
- Test A: Load the ONELOVE project. Assert the system prompt contains "One Love AI" and does NOT contain "Zoe".
- Test B: Load the Hummingbird project. Assert the system prompt contains "Zoe" and does NOT contain "One Love AI".
- Test C: Send a DM to the ONELOVE bot. Assert the [RECENT GROUP CHAT HISTORY] block only contains messages from the ONELOVE SQLite table.
"""

from pathlib import Path
import sqlite3
import pytest

from zoe.conversation.prompt_builder import (
    build_prompt,
    get_project_display_name,
    get_project_system_prompt,
)
from zoe.db.connections import open_community_memory_db, open_operational_db
from zoe.llm.mock import MockLLMClient
from zoe.memory.short_term import record_community_message
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.pipeline import process_message


def test_a_onelove_identity_contains_one_love_ai_and_no_zoe():
    """Test A: Load the ONELOVE project. Assert the system prompt contains 'One Love AI' and does NOT contain 'Zoe'."""
    prompt = get_project_system_prompt("onelove")
    assert "One Love AI" in prompt
    assert "You are One Love AI" in prompt
    assert "Zoe" not in prompt


def test_b_hummingbird_identity_contains_zoe_and_no_onelove():
    """Test B: Load the Hummingbird project. Assert the system prompt contains 'Zoe' and does NOT contain 'One Love AI'."""
    prompt = get_project_system_prompt("live_test")
    assert "Zoe" in prompt
    assert "You are Zoe" in prompt
    assert "One Love AI" not in prompt


def test_c_cross_chat_memory_isolation_in_dm(tmp_path: Path):
    """Test C: Send a DM to the ONELOVE bot. Assert the [RECENT GROUP CHAT HISTORY] block only contains messages from the ONELOVE SQLite table."""
    op_path = tmp_path / "operational.db"
    conn_op = open_operational_db(op_path)
    sql_op = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src/zoe/db/schema_operational.sql"
    ).read_text(encoding="utf-8")
    conn_op.executescript(sql_op)

    conn_op.execute(
        """
        INSERT INTO projects (project_id, name, telegram_group_id, config_json, created_at, active)
        VALUES ('onelove', 'One Love', '-5214407126', '{"telegram": {"group_id": "-5214407126"}}', '2026-01-01 00:00:00', 1)
        """
    )
    conn_op.commit()

    mem_path = tmp_path / "community_memory.db"
    conn_mem = open_community_memory_db(mem_path)
    sql_mem = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src/zoe/db/schema_community_memory.sql"
    ).read_text(encoding="utf-8")
    conn_mem.executescript(sql_mem)

    # Insert Hummingbird messages into community_messages
    record_community_message(
        conn=conn_mem,
        project_id="live_test",
        group_id="-5214407126",
        telegram_message_id=101,
        pseudonymous_user_id="trader_hummingbird",
        content="Hummingbird secret message: buy FLY token!",
    )

    # Insert ONELOVE messages into community_messages
    record_community_message(
        conn=conn_mem,
        project_id="onelove",
        group_id="-5214407126",
        telegram_message_id=102,
        pseudonymous_user_id="trader_onelove",
        content="OneLove community message: Welcome aboard the catamaran!",
    )

    # Insert DM message sent to ONELOVE bot (positive group_id indicates DM)
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, is_forward, state, state_changed_at,
            created_at, message_timestamp
        ) VALUES ('onelove', 9991, '7136342824', 8881, 'dm_user', 'respond to the community please', 0, 'message_persisted', '2026-11-11 17:00:00', '2026-11-11 17:00:00', '2026-11-11 17:00:00')
        """,
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    captured_prompts = []

    class CapturingLLM(MockLLMClient):
        def generate(self, system_prompt: str, user_prompt: str, **kwargs):
            captured_prompts.append({"system": system_prompt, "user": user_prompt})
            return "Scanning the group logs now, sir."

    llm = CapturingLLM()
    conns = {"operational": conn_op, "memory": conn_mem}

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        llm_client=llm,
        mem_db_path=mem_path,
        simulated=True,
    )

    assert result.responded is True
    assert len(captured_prompts) > 0

    full_system = captured_prompts[-1]["system"]
    assert "[RECENT GROUP CHAT HISTORY]" in full_system
    # Verify ONELOVE message IS in the history
    assert "OneLove community message: Welcome aboard the catamaran!" in full_system
    # Verify Hummingbird message is NOT in the ONELOVE history
    assert "Hummingbird secret message" not in full_system
    assert "FLY token" not in full_system

    conn_op.close()
    conn_mem.close()
