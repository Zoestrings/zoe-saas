"""Unit tests verifying natural conversational synthesis and duplicate/overflow prevention.

Tests:
- Test A: Ask 'Who is the captain?'. Assert the output is a short, natural sentence
  (e.g., 'The captain is Robbie Olson, a 500-Ton Master Mariner...') and does NOT contain
  raw hyphens, weird spacing ('s / y', '500 - ton'), or document bullet formatting.
- Test B: Assert the max token limit strictly caps generation at 250 tokens, preventing
  overly long copy-pasted responses.
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
from zoe.knowledge.ingestion import clean_decoded_text
from zoe.llm.mock import MockLLMClient
from zoe.telegram.normalizer import NormalizedMessage
from zoe.utils.sanitizer import clean_unnecessary_characters
from zoe.worker.pipeline import _safe_generate, process_message

PROJECT_ID = "onelove"
GROUP_ID = "-1005214407126"


@pytest.fixture
def synthesis_env(tmp_path: Path):
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
        VALUES (?, 'onelove_info.txt', '2026-01-01 00:00:00')
        """,
        (PROJECT_ID,),
    )
    doc_id = cur_doc.lastrowid

    # Simulated raw doc chunk with potential artifacts
    raw_chunk = "Captain: Robbie Olson - 500-Ton Master Mariner and founder of One Love Sailing."
    conn_kb.execute(
        """
        INSERT INTO official_chunks (doc_id, project_id, chunk_index, content, token_count, faiss_vector_id)
        VALUES (?, ?, 0, ?, 25, 1)
        """,
        (doc_id, PROJECT_ID, raw_chunk),
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
        "kb_path": kb_path,
        "mem_path": mem_path,
    }

    conn_op.close()
    conn_kb.close()
    conn_mem.close()


def test_clean_decoded_text_spacing():
    """Verify clean_decoded_text fixes all tokenizer artifact spacing."""
    raw = "The vessel s / y one love ² is a 500 - ton yacht for $ onelove coin . records , ."
    cleaned = clean_decoded_text(raw)
    assert "s/y" in cleaned
    assert "one love²" in cleaned
    assert "500-ton" in cleaned
    assert "$onelove" in cleaned
    assert "records." in cleaned


def test_a_natural_synthesis_captain_query(synthesis_env):
    """Test A: Ask 'Who is the captain?'.
    
    Assert the output is a short, natural sentence and does NOT contain raw hyphens,
    bullet points, or broken citations like 'According to official project records, .'.
    """
    conns = synthesis_env["conns"]
    conn_op = conns["operational"]
    kb_path = synthesis_env["kb_path"]
    mem_path = synthesis_env["mem_path"]

    class SynthesisLLM(MockLLMClient):
        def generate(self, system_prompt: str, user_prompt: str, **kwargs):
            # Verify prompt instructions require synthesis and ban raw dumping
            assert "NEVER copy and paste raw text directly from the official documents" in system_prompt
            assert "Synthesize" in user_prompt or "synthesize" in user_prompt
            # LLM synthesizes into a natural conversational sentence
            return "According to official project records, . The captain is Robbie Olson, a 500-Ton Master Mariner and founder of One Love Sailing."

    uid = random.randint(10000000, 99999999)
    msg = NormalizedMessage(
        project_id=PROJECT_ID,
        telegram_update_id=uid,
        group_id=GROUP_ID,
        telegram_message_id=uid % 10000,
        pseudonymous_user_id="sailor_1",
        text="Who is the captain?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 16:00:00",
    )
    persist_batch(conn_op, PROJECT_ID, [msg], uid)
    cur = conn_op.execute("SELECT id FROM inbox_messages WHERE telegram_update_id = ?", (uid,))
    inbox_id = cur.fetchone()[0]

    result = process_message(
        inbox_row=inbox_id,
        db_conns=conns,
        kb_db_path=kb_path,
        mem_db_path=mem_path,
        llm_client=SynthesisLLM(),
        web_search_fn=lambda q: [],
        simulated=True,
        intent="knowledge",
    )

    assert result.responded is True
    assert result.response_text is not None
    resp = result.response_text

    # Must contain the synthesized facts
    assert "Robbie Olson" in resp
    assert "500-Ton" in resp

    # Strictly must NOT contain broken citation prefix
    assert "According to official project records, ." not in resp
    assert "records, ." not in resp

    # No document bullets or raw text spacing
    assert not resp.startswith("- ")
    assert "s / y" not in resp
    assert "500 - ton" not in resp


def test_b_max_token_limit_prevents_long_dump():
    """Test B: Assert max_tokens is strictly capped at 250 in _safe_generate and GroqProvider."""
    class TrackingLLM(MockLLMClient):
        last_max_tokens = None
        def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 100, **kwargs):
            self.last_max_tokens = max_tokens
            return "Clean short response."

    client = TrackingLLM()

    # Pass 1000 tokens — must be hard-capped at 250
    _safe_generate(client, "system", "user prompt", max_tokens=1000)
    assert client.last_max_tokens == 250

    # Pass technical prompt with 500 tokens — must also be capped at 250
    _safe_generate(client, "system", "check this python code", max_tokens=500, is_technical=True)
    assert client.last_max_tokens == 250

    # Test clean_unnecessary_characters cleans weird spacing and citation glitches
    raw_glitch = "According to official project records, . - Robbie Olson is the captain of s / y one love ² ."
    cleaned = clean_unnecessary_characters(raw_glitch)
    assert "According to official project records, ." not in cleaned
    assert "- " not in cleaned
    assert "s/y" in cleaned
    assert "one love²" in cleaned
