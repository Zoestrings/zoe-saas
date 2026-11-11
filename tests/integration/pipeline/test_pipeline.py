import pytest
from pathlib import Path
from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.llm.mock import MockLLMClient
from zoe.worker.pipeline import process_message
from zoe.safety.validator import SafetyResult


@pytest.fixture
def pipeline_env(tmp_path: Path):
    # 1. Operational DB
    op_path = tmp_path / "operational.db"
    conn_op = open_operational_db(op_path)
    sql_op = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_operational.sql").read_text(encoding="utf-8")
    conn_op.executescript(sql_op)
    conn_op.execute("INSERT INTO projects (project_id, name, telegram_group_id, config_json, created_at, active) VALUES ('p1', 'Test', '-100999', '{}', '2026-01-01 00:00:00', 1)")
    conn_op.commit()

    # 2. Knowledge DB
    kb_path = tmp_path / "official_knowledge.db"
    conn_kb = open_official_knowledge_db(kb_path)
    sql_kb = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_knowledge.sql").read_text(encoding="utf-8")
    conn_kb.executescript(sql_kb)
    conn_kb.commit()

    # 3. Memory DB
    mem_path = tmp_path / "community_memory.db"
    conn_mem = open_community_memory_db(mem_path)
    sql_mem = (Path(__file__).resolve().parent.parent.parent.parent / "src/zoe/db/schema_community_memory.sql").read_text(encoding="utf-8")
    conn_mem.executescript(sql_mem)
    conn_mem.commit()

    index_dir = tmp_path / "indexes"

    conns = {
        "operational": conn_op,
        "knowledge": conn_kb,
        "memory": conn_mem,
    }
    return conns, op_path, kb_path, mem_path, index_dir


@pytest.mark.automated
def test_pipeline_produces_simulated_outbox_message(pipeline_env) -> None:
    conns, op_path, kb_path, mem_path, index_dir = pipeline_env
    conn_op = conns["operational"]

    # Insert an inbox message in message_persisted state
    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (
            'p1', 101, '-100999', 201, 'pseudo_u1',
            'What is the unbonding period for staking?', NULL, 0,
            '2026-11-05 12:00:00', 'message_persisted', '2026-11-05 12:00:00', '2026-11-05 12:00:00'
        )
        """
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    mock_llm = MockLLMClient(canned_response="The unbonding period is 14 days.")
    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
        llm_client=mock_llm,
    )

    assert result.responded
    assert result.outbox_id is not None
    assert result.response_text == "The unbonding period is 14 days."

    # Verify participation_log is populated
    p_cur = conn_op.execute("SELECT decision, reason_code FROM participation_log WHERE telegram_message_id = 201")
    p_row = p_cur.fetchone()
    assert p_row is not None
    assert p_row[0] == "respond"

    # Verify outbox row: simulated MUST equal 1
    o_cur = conn_op.execute("SELECT simulated, state, text FROM outbox_messages WHERE id = ?", (result.outbox_id,))
    o_row = o_cur.fetchone()
    assert o_row is not None
    assert o_row[0] == 1, f"Expected simulated=1, got {o_row[0]}"
    assert o_row[1] == "pending"
    assert o_row[2] == "The unbonding period is 14 days."


@pytest.mark.automated
def test_pipeline_aborts_safely_on_validator_exception(pipeline_env) -> None:
    """If safety validator raises an exception, pipeline must fail-closed and not enqueue outbox."""
    conns, op_path, kb_path, mem_path, index_dir = pipeline_env
    conn_op = conns["operational"]

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (
            'p1', 102, '-100999', 202, 'pseudo_u2',
            'Can you explain the protocol upgrade?', NULL, 0,
            '2026-11-05 12:00:00', 'message_persisted', '2026-11-05 12:00:00', '2026-11-05 12:00:00'
        )
        """
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    def crashing_validator(text, provenance):
        raise RuntimeError("Safety engine unexpected fault")

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
        safety_validator_fn=crashing_validator,
    )

    # Must abort safely
    assert not result.responded
    assert result.aborted
    assert result.outbox_id is None

    # No outbox row queued
    o_cur = conn_op.execute("SELECT COUNT(*) FROM outbox_messages WHERE inbox_message_id = ?", (inbox_id,))
    assert o_cur.fetchone()[0] == 0


@pytest.mark.automated
def test_pipeline_casual_chat_transitions_to_no_response_required(pipeline_env) -> None:
    conns, op_path, kb_path, mem_path, index_dir = pipeline_env
    conn_op = conns["operational"]

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (
            'p1', 103, '-100999', 203, 'pseudo_u3',
            'gm everyone', NULL, 0,
            '2026-11-05 12:00:00', 'message_persisted', '2026-11-05 12:00:00', '2026-11-05 12:00:00'
        )
        """
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
    )

    assert not result.responded
    assert result.decision.decision == "remain_silent"

    # State in inbox_messages must be no_response_required
    i_cur = conn_op.execute("SELECT state FROM inbox_messages WHERE id = ?", (inbox_id,))
    assert i_cur.fetchone()[0] == "no_response_required"


@pytest.mark.automated
def test_pipeline_accuracy_guard_fallback_on_low_confidence(pipeline_env) -> None:
    """When a knowledge question has no RAG chunks, accuracy guard returns safe fallback."""
    conns, op_path, kb_path, mem_path, index_dir = pipeline_env
    conn_op = conns["operational"]

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (
            'p1', 104, '-100999', 204, 'pseudo_u4',
            'What is Hummingbird and why does it require KYC?', NULL, 0,
            '2026-11-05 12:00:00', 'message_persisted', '2026-11-05 12:00:00', '2026-11-05 12:00:00'
        )
        """
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
        enforce_accuracy_guard=True,
    )

    assert result.responded
    assert result.response_text == "I don't have that in my official documents yet. Please check the official announcements."


@pytest.mark.automated
def test_pipeline_routes_fly_price_to_dexscreener_tool(pipeline_env) -> None:
    """When user asks for live price/liquidity, pipeline routes to API tool and injects live market data."""
    conns, op_path, kb_path, mem_path, index_dir = pipeline_env
    conn_op = conns["operational"]

    cur = conn_op.execute(
        """
        INSERT INTO inbox_messages (
            project_id, telegram_update_id, group_id, telegram_message_id,
            pseudonymous_user_id, text, reply_to_message_id, is_forward,
            message_timestamp, state, state_changed_at, created_at
        ) VALUES (
            'p1', 105, '-100999', 205, 'pseudo_u5',
            'What is the price of $FLY?', NULL, 0,
            '2026-11-05 12:00:00', 'message_persisted', '2026-11-05 12:00:00', '2026-11-05 12:00:00'
        )
        """
    )
    inbox_id = cur.lastrowid
    conn_op.commit()

    mock_llm = MockLLMClient()
    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        index_dir=index_dir,
        llm_client=mock_llm,
    )

    assert result.responded
    assert len(mock_llm.calls) == 1
    assert "[LIVE MARKET DATA]" in mock_llm.calls[0]["user_prompt"]
    assert "price" in result.response_text.lower() or "$0.0024" in result.response_text

