"""Unit tests for Cross-Chat Memory Bridge and Ban on AI Excuses.

Tests:
- Test A: Simulate a DM saying "what did they ask in the group?". Assert the pipeline retrieves
  the last 5 group messages and passes them to the LLM under [RECENT GROUP CHAT HISTORY].
- Test B: Assert the generated prompt and final output do NOT contain phrases like "I cannot see"
  or "Please copy and paste".
- Test C: When the group history is empty, assert she replies with the proper JARVIS message:
  "I checked the recent group logs, but there hasn't been any activity in the last few minutes."
"""

from pathlib import Path
import random
import pytest

from zoe.db.connections import (
    open_community_memory_db,
    open_official_knowledge_db,
    open_operational_db,
)
from zoe.inbox.inbox_service import persist_batch
from zoe.llm.mock import MockLLMClient
from zoe.memory.short_term import record_community_message
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.pipeline import process_message

PROJECT_ID = "onelove"
GROUP_ID = "-1005214407126"
DM_USER_CHAT_ID = "987654321"


@pytest.fixture
def cross_chat_env(tmp_path: Path):
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
        VALUES (?, 'One Love ($ONELOVE)', ?, '{"telegram": {"group_id": "-1005214407126"}, "modules": {"crypto_intelligence": true, "community_manager": true}}', '2026-01-01 00:00:00', 1)
        """,
        (PROJECT_ID, GROUP_ID),
    )
    conn_op.commit()

    kb_path = tmp_path / "official_knowledge.db"
    conn_kb = open_official_knowledge_db(kb_path)
    sql_kb = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src/zoe/db/schema_knowledge.sql"
    ).read_text(encoding="utf-8")
    conn_kb.executescript(sql_kb)

    cur_doc = conn_kb.execute(
        """
        INSERT INTO official_documents (project_id, filename, ingested_at)
        VALUES (?, 'onelove_info.txt', '2026-01-01 00:00:00')
        """,
        (PROJECT_ID,),
    )
    doc_id = cur_doc.lastrowid
    conn_kb.execute(
        """
        INSERT INTO official_chunks (doc_id, project_id, chunk_index, content, token_count, faiss_vector_id)
        VALUES (?, ?, 0, 'The flagship yacht is S/Y One Love Squared, an 82-foot Nautitech catamaran.', 25, 0)
        """,
        (doc_id, PROJECT_ID),
    )
    conn_kb.commit()

    mem_path = tmp_path / "community_memory.db"
    conn_mem = open_community_memory_db(mem_path)
    sql_mem = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src/zoe/db/schema_community_memory.sql"
    ).read_text(encoding="utf-8")
    conn_mem.executescript(sql_mem)

    conns = {
        "operational": conn_op,
        "knowledge": conn_kb,
        "memory": conn_mem,
    }

    yield {
        "conns": conns,
        "op_path": op_path,
        "kb_path": kb_path,
        "mem_path": mem_path,
    }

    conn_op.close()
    conn_kb.close()
    conn_mem.close()


def test_a_cross_chat_retrieves_last_5_group_messages(cross_chat_env):
    """Test A: Simulate a DM saying 'what did they ask in the group?'.
    
    Assert the pipeline retrieves the last 5 group messages and passes them
    to the LLM under a [RECENT GROUP CHAT HISTORY] block.
    """
    conns = cross_chat_env["conns"]
    conn_op = conns["operational"]
    conn_mem = conns["memory"]
    kb_path = cross_chat_env["kb_path"]
    mem_path = cross_chat_env["mem_path"]

    # Insert 5 group messages into community_messages
    group_texts = [
        "What is the token symbol?",
        "Where is the yacht sailing?",
        "Who is the captain?",
        "Is liquidity locked?",
        "Tell me about the flagship catamaran",
    ]
    for idx, text in enumerate(group_texts):
        record_community_message(
            conn=conn_mem,
            project_id=PROJECT_ID,
            group_id=GROUP_ID,
            telegram_message_id=5000 + idx,
            pseudonymous_user_id=f"sailor_{idx}",
            content=text,
            received_at=f"2026-11-11 15:0{idx}:00",
        )

    # User sends DM: "what are they saying in the group?"
    uid_dm = random.randint(10000000, 99999999)
    dm_msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=uid_dm,
        group_id=DM_USER_CHAT_ID,  # Positive ID indicates private chat / DM
        telegram_message_id=9001,
        pseudonymous_user_id="admin_dan",
        text="what are they saying in the group?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 15:10:00",
    )
    persist_batch(conn_op, PROJECT_ID, [dm_msg], uid_dm)
    cur_dm = conn_op.execute("SELECT id FROM inbox_messages WHERE telegram_update_id = ?", (uid_dm,))
    dm_inbox_id = cur_dm.fetchone()[0]

    class PromptCapturingLLM(MockLLMClient):
        captured_user_prompt = ""
        captured_system_prompt = ""
        def generate(self, system_prompt: str, user_prompt: str, **kwargs):
            self.captured_system_prompt = system_prompt
            self.captured_user_prompt = user_prompt
            return "Based on the official logs, the community asked about the yacht, the captain, and the token."

    llm = PromptCapturingLLM()

    result = process_message(
        inbox_row=dm_inbox_id,
        db_conns=conns,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        llm_client=llm,
        web_search_fn=lambda q: [],
        simulated=True,
        intent="general",
    )

    assert result.responded is True
    assert result.response_text is not None

    # Assert [RECENT GROUP CHAT HISTORY] is present in system or user prompt
    combined_prompt = f"{llm.captured_system_prompt}\n{llm.captured_user_prompt}"
    assert "[RECENT GROUP CHAT HISTORY]" in combined_prompt

    # Assert all 5 group messages were retrieved and passed to the LLM
    for text in group_texts:
        assert text in combined_prompt


def test_b_ban_ai_excuses_and_limitation_phrases(cross_chat_env):
    """Test B: Assert the final generated prompt and output do NOT contain 'I cannot see' or AI excuses."""
    conns = cross_chat_env["conns"]
    conn_op = conns["operational"]
    conn_mem = conns["memory"]
    kb_path = cross_chat_env["kb_path"]
    mem_path = cross_chat_env["mem_path"]

    # Insert 1 group message
    record_community_message(
        conn=conn_mem,
        project_id=PROJECT_ID,
        group_id=GROUP_ID,
        telegram_message_id=6001,
        pseudonymous_user_id="sailor_group",
        content="What is the roadmap?",
        received_at="2026-11-11 15:20:00",
    )

    uid_dm = random.randint(10000000, 99999999)
    dm_msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=uid_dm,
        group_id=DM_USER_CHAT_ID,
        telegram_message_id=9002,
        pseudonymous_user_id="admin_dan",
        text="respond to the community please",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 15:21:00",
    )
    persist_batch(conn_op, PROJECT_ID, [dm_msg], uid_dm)
    cur_dm = conn_op.execute("SELECT id FROM inbox_messages WHERE telegram_update_id = ?", (uid_dm,))
    dm_inbox_id = cur_dm.fetchone()[0]

    class ExcuseAttemptingLLM(MockLLMClient):
        captured_user_prompt = ""
        captured_system_prompt = ""
        def generate(self, system_prompt: str, user_prompt: str, **kwargs):
            self.captured_system_prompt = system_prompt
            self.captured_user_prompt = user_prompt
            # Model returns answer but tries to append an AI excuse
            return "Based on the logs, they asked about the roadmap. I cannot see the live feed. Please copy and paste the message."

    llm = ExcuseAttemptingLLM()

    result = process_message(
        inbox_row=dm_inbox_id,
        db_conns=conns,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        llm_client=llm,
        web_search_fn=lambda q: [],
        simulated=True,
        intent="general",
    )

    assert result.responded is True
    resp = result.response_text

    # Test B Assertion: System prompt explicitly contains the [RECENT GROUP CHAT HISTORY] block
    assert "[RECENT GROUP CHAT HISTORY]" in llm.captured_system_prompt

    # Prompt itself strictly instructs against excuses
    assert "strictly forbidden from saying 'I cannot see the group'" in llm.captured_system_prompt

    # Final response is sanitized and contains no AI excuse phrases
    assert "I cannot see" not in resp
    assert "cannot see the live" not in resp
    assert "copy and paste" not in resp
    assert "technical limitation" not in resp


def test_c_empty_group_history_returns_jarvis_response(cross_chat_env):
    """Test C: If the group history is empty, assert she replies with the JARVIS response."""
    conns = cross_chat_env["conns"]
    conn_op = conns["operational"]
    kb_path = cross_chat_env["kb_path"]
    mem_path = cross_chat_env["mem_path"]

    # No group messages inserted
    uid_dm = random.randint(10000000, 99999999)
    dm_msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=uid_dm,
        group_id=DM_USER_CHAT_ID,
        telegram_message_id=9003,
        pseudonymous_user_id="admin_dan",
        text="what did they ask in the group?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 15:30:00",
    )
    persist_batch(conn_op, PROJECT_ID, [dm_msg], uid_dm)
    cur_dm = conn_op.execute("SELECT id FROM inbox_messages WHERE telegram_update_id = ?", (uid_dm,))
    dm_inbox_id = cur_dm.fetchone()[0]

    result = process_message(
        inbox_row=dm_inbox_id,
        db_conns=conns,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        llm_client=MockLLMClient(),
        web_search_fn=lambda q: [],
        simulated=True,
        intent="general",
    )

    assert result.responded is True
    assert result.response_text == "I just checked the group logs, but it's quiet right now."
