"""Automated Tests for Pillar 3: Agent Registry & /summon Persona Switching."""

from pathlib import Path
from zoe.agents.registry import (
    AGENT_REGISTRY,
    get_active_agent,
    get_session_key,
    list_registered_agents,
    set_active_agent,
)
from zoe.db.connections import open_community_memory_db, open_official_knowledge_db, open_operational_db
from zoe.llm.mock import MockLLMClient
from zoe.worker.pipeline import process_message


def test_agent_registry_contains_core_personas():
    """Verify defi, security, nft, and researcher personas are registered."""
    assert {"defi", "security", "nft", "researcher"}.issubset(set(AGENT_REGISTRY.keys()))
    agents = list_registered_agents()
    assert len(agents) >= 4
    assert "DeFi specialist" in AGENT_REGISTRY["defi"]["system_prompt"]


def test_summon_session_switching_and_reset():
    """Verify /summon switches persona in session memory and 'default' resets to JARVIS."""
    key = get_session_key("proj_1", "user_99")
    set_active_agent(key, "default")
    assert get_active_agent(key) is None

    persona = set_active_agent(key, "defi")
    assert persona is not None
    assert persona["id"] == "defi"
    assert get_active_agent(key)["id"] == "defi"

    # Reset back to JARVIS
    reset_res = set_active_agent(key, "default")
    assert reset_res is None
    assert get_active_agent(key) is None


def test_pipeline_summon_and_help_commands(tmp_path: Path):
    """Verify /summon defi, /help agent listing, and persona injection in pipeline."""
    op_db = open_operational_db(tmp_path / "op.db")
    kb_db = open_official_knowledge_db(tmp_path / "kb.db")
    mem_db = open_community_memory_db(tmp_path / "mem.db")

    op_db.execute(
        """
        INSERT OR REPLACE INTO projects (project_id, name, telegram_group_id, config_json, created_at, active)
        VALUES ('onelove', 'One Love AI', '-5214407126', '{}', '2026-11-25T00:00:00Z', 1)
        """
    )
    op_db.commit()

    def _run_msg(msg_id: int, text: str, llm: MockLLMClient):
        from zoe.worker.claim import claim_next_inbox_row
        op_db.execute(
            """
            INSERT INTO inbox_messages (
                id, project_id, telegram_update_id, group_id, telegram_message_id,
                pseudonymous_user_id, text, state, state_changed_at, message_timestamp, created_at
            ) VALUES (?, 'onelove', ?, '-5214407126', ?, 'user_summon_test', ?, 'message_persisted', '2026-11-25T00:00:00Z', '2026-11-25T00:00:00Z', '2026-11-25T00:00:00Z')
            """,
            (msg_id, 500 + msg_id, 600 + msg_id, text),
        )
        op_db.commit()
        claimed = claim_next_inbox_row(op_db, project_id="onelove", worker_id="test_worker")
        assert claimed is not None
        return process_message(
            inbox_row=claimed,
            db_conns={"operational": op_db, "knowledge": kb_db, "memory": mem_db},
            llm_client=llm,
            simulated=True,
        )

    mock_llm = MockLLMClient()

    # 1. /help lists available agents
    res_help = _run_msg(1, "/help", mock_llm)
    help_text = res_help.response_text or ""
    assert "/summon defi" in help_text and "Switch to DeFi Expert" in help_text
    assert "/summon security" in help_text and "Switch to Security Auditor" in help_text
    assert "/summon default" in help_text and "Return to Zoe (JARVIS)" in help_text

    # 2. /summon defi switches persona
    res_summon = _run_msg(2, "/summon defi", mock_llm)
    assert "DeFi Expert mode" in (res_summon.response_text or "")

    # 3. Subsequent question uses DeFi system prompt
    _run_msg(3, "@Zoe How does impermanent loss work on Raydium?", mock_llm)
    assert len(mock_llm.calls) >= 1
    assert any("DeFi specialist" in c["system_prompt"] for c in mock_llm.calls)

    # 4. /summon default returns to JARVIS
    res_reset = _run_msg(4, "/summon default", mock_llm)
    assert "JARVIS" in (res_reset.response_text or "")
