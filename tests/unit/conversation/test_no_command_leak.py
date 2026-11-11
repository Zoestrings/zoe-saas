"""Unit tests verifying that Zoe never leaks bot commands (/ask, /ca, /price, /help) in conversation.

Tests:
- Test A: Paste a Contract Address -> Response contains ONLY token data and does NOT contain `/ask` or `/help`.
- Test B: Ask a normal question ("Who is the captain?") -> Response does NOT contain `/ca` or `/price`.
- Test C: Type `/help` -> Response contains the full formatted command menu.
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
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.pipeline import process_message

PROJECT_ID = "onelove"
GROUP_ID = "-1005214407126"
SOL_CA = "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon"


@pytest.fixture
def cmd_leak_env(tmp_path: Path):
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
        VALUES (?, 'One Love ($ONELOVE)', ?, '{"token_address": "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon", "modules": {"crypto_intelligence": true, "community_manager": true}}', '2026-01-01 00:00:00', 1)
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
        VALUES (?, 'captain_info.txt', '2026-01-01 00:00:00')
        """,
        (PROJECT_ID,),
    )
    doc_id = cur_doc.lastrowid
    conn_kb.execute(
        """
        INSERT INTO official_chunks (doc_id, project_id, chunk_index, content, token_count, faiss_vector_id)
        VALUES (?, ?, 0, 'Captain Robbie Olson is the founder and skipper of the One Love project in the Bahamas.', 25, 0)
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


def test_a_ca_scanner_does_not_leak_commands(cmd_leak_env, monkeypatch):
    """Test A: Paste a Contract Address. Assert response contains ONLY token data and does NOT contain /ask or /help."""
    conns = cmd_leak_env["conns"]
    conn_op = conns["operational"]
    kb_path = cmd_leak_env["kb_path"]
    mem_path = cmd_leak_env["mem_path"]

    class MockDexResponse:
        status_code = 200

        def json(self):
            return {
                "pairs": [
                    {
                        "baseToken": {"name": "One Love Sailing", "symbol": "ONELOVE"},
                        "priceUsd": "0.000095",
                        "liquidity": {"usd": 50000.0},
                        "volume": {"h24": 12000.0},
                        "marketCap": 95000.0,
                    }
                ]
            }

    monkeypatch.setattr("httpx.Client.get", lambda self, url, **kwargs: MockDexResponse())

    uid = random.randint(10000000, 99999999)
    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=uid,
        group_id=GROUP_ID,
        telegram_message_id=uid % 10000,
        pseudonymous_user_id="trader_ca",
        text=SOL_CA,
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 15:00:00",
    )
    persist_batch(conn_op, PROJECT_ID, [msg], uid)
    cur = conn_op.execute("SELECT id FROM inbox_messages WHERE telegram_update_id = ?", (uid,))
    inbox_id = cur.fetchone()[0]

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        simulated=True,
    )

    assert result.responded is True
    assert result.response_text is not None
    resp = result.response_text

    # Must contain token data
    assert "Price: $0.000095" in resp
    assert "Liquidity: $50,000.00" in resp
    assert "24h Volume: $12,000.00" in resp

    # Strictly MUST NOT leak commands
    assert "/ask" not in resp
    assert "/help" not in resp
    assert "/ca" not in resp
    assert "/price" not in resp


def test_b_normal_question_does_not_leak_commands(cmd_leak_env):
    """Test B: Ask a normal question 'Who is the captain?'. Assert response does NOT contain /ca or /price."""
    conns = cmd_leak_env["conns"]
    conn_op = conns["operational"]
    kb_path = cmd_leak_env["kb_path"]
    mem_path = cmd_leak_env["mem_path"]

    # Even if LLM tries to mention /ca or /price in its response, pipeline purges it
    class ChattyLLM(MockLLMClient):
        def generate(self, system_prompt: str, user_prompt: str, **kwargs):
            return "Captain Robbie Olson is the founder of the One Love project. You can also type /ca for contract address or /price for price info."

    uid = random.randint(10000000, 99999999)
    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=uid,
        group_id=GROUP_ID,
        telegram_message_id=uid % 10000,
        pseudonymous_user_id="user_question",
        text="Who is the captain?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 15:01:00",
    )
    persist_batch(conn_op, PROJECT_ID, [msg], uid)
    cur = conn_op.execute("SELECT id FROM inbox_messages WHERE telegram_update_id = ?", (uid,))
    inbox_id = cur.fetchone()[0]

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        llm_client=ChattyLLM(),
        web_search_fn=lambda q: [],
        simulated=True,
    )

    assert result.responded is True
    assert result.response_text is not None
    resp = result.response_text

    assert "Robbie Olson" in resp
    # Strict verification: commands are stripped from conversational responses
    assert "/ca" not in resp
    assert "/price" not in resp
    assert "/help" not in resp
    assert "/ask" not in resp


def test_c_help_command_outputs_command_list(cmd_leak_env):
    """Test C: Type /help. Assert the command list is printed."""
    conns = cmd_leak_env["conns"]
    conn_op = conns["operational"]
    kb_path = cmd_leak_env["kb_path"]
    mem_path = cmd_leak_env["mem_path"]

    uid = random.randint(10000000, 99999999)
    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=uid,
        group_id=GROUP_ID,
        telegram_message_id=uid % 10000,
        pseudonymous_user_id="user_help",
        text="/help",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 15:02:00",
    )
    persist_batch(conn_op, PROJECT_ID, [msg], uid)
    cur = conn_op.execute("SELECT id FROM inbox_messages WHERE telegram_update_id = ?", (uid,))
    inbox_id = cur.fetchone()[0]

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        simulated=True,
    )

    assert result.responded is True
    assert result.response_text is not None
    resp = result.response_text

    # /help MUST output the full command menu
    assert "/ca" in resp
    assert "/price" in resp
    assert "/ask" in resp
    assert "/help" in resp
    assert "/credits" in resp

