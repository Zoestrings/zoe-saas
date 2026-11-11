"""Tests for ONELOVE Official Knowledge Ingestion, RAG Accuracy & Strict Isolation.

Tests:
- Test A (Isolation): Ask ONELOVE "What is the price of FLY?".
  Assert the bot refuses and does not query DexScreener for Hummingbird.
- Test B (RAG Accuracy): Ask ONELOVE "What is the official contract address?".
  Assert the RAG/pipeline returns exactly F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon.
- Test C (RAG Accuracy): Ask ONELOVE "Who is the creator and what is the yacht?".
  Assert the RAG/pipeline returns Captain Robbie Olson and the 82-foot Nautitech catamaran.
"""

from pathlib import Path
import random
import pytest

from zoe.conversation.prompt_builder import get_project_system_prompt
from zoe.db.connections import open_operational_db
from zoe.inbox.inbox_service import persist_batch
from zoe.knowledge.retriever import search
from zoe.llm.mock import MockLLMClient
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.claim import claim_next_inbox_row
from zoe.worker.pipeline import process_message

ONELOVE_CA = "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon"
HUMMINGBIRD_CA = "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf"


def test_a_isolation_refuses_foreign_token_before_dexscreener(monkeypatch):
    """Test A (Isolation): Ask 'What is the price of FLY?'.
    Assert the bot refuses and does not query DexScreener for Hummingbird.
    """
    conn_op = open_operational_db("data/operational/operational.db")

    queried_urls = []

    def mock_get(url, *args, **kwargs):
        queried_urls.append(url)
        raise RuntimeError("DexScreener should never be called for cross-project token query!")

    monkeypatch.setattr("httpx.Client.get", lambda self, url, **kwargs: mock_get(url, **kwargs))

    uid = random.randint(100000000, 999999999)
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id="-5214407126",
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="trader_bob",
        text="What is the price of FLY?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 10:00:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    claim = claim_next_inbox_row(conn_op, project_id="onelove", worker_id="test_worker_onelove_a")
    assert claim is not None

    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        simulated=True,
    )

    assert result.responded is True
    assert result.response_text is not None
    resp = result.response_text

    # Assert she refuses politely and strictly states the project boundary
    assert "I only manage data for One Love ($ONELOVE)" in resp
    assert "I don't have specific info on that other token" in resp

    # Assert DexScreener was NOT called for Hummingbird
    assert not any(HUMMINGBIRD_CA in url for url in queried_urls)


def test_b_rag_accuracy_contract_address():
    """Test B (RAG Accuracy): Ask 'What is the official contract address?'.
    Assert the RAG retrieval returns the chunk containing the exact CA and the pipeline responds with it.
    """
    chunks = search("onelove", "What is the official contract address?", top_k=4)
    assert len(chunks) > 0

    # 1. Ensure the exact contract address is present in retrieved official knowledge
    found_ca = any(ONELOVE_CA.lower() in c.content.lower() for c in chunks)
    assert found_ca, f"Expected CA {ONELOVE_CA} to be in retrieved official chunks, got: {[c.content[:80] for c in chunks]}"

    # 2. Test through pipeline
    conn_op = open_operational_db("data/operational/operational.db")
    uid = random.randint(100000000, 999999999)
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id="-5214407126",
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="crypto_fan",
        text="What is the official contract address?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 10:00:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    claim = claim_next_inbox_row(conn_op, project_id="onelove", worker_id="test_worker_onelove_b")
    assert claim is not None

    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        simulated=True,
    )

    assert result.responded is True
    assert result.response_text is not None
    assert ONELOVE_CA.lower() in result.response_text.lower()


def test_c_rag_accuracy_creator_and_yacht():
    """Test C (RAG Accuracy): Ask 'Who is the creator and what is the yacht?'.
    Assert the RAG retrieval returns Captain Robbie Olson and the 82-foot Nautitech catamaran.
    """
    chunks = search("onelove", "Who is the creator and what is the yacht?", top_k=4)
    assert len(chunks) > 0

    all_content = " ".join(c.content.lower() for c in chunks)
    assert "robbie olson" in all_content or "captain robert olson" in all_content
    assert "82" in all_content or "nautitech" in all_content or "catamaran" in all_content

    # Also test through pipeline
    conn_op = open_operational_db("data/operational/operational.db")
    uid = random.randint(100000000, 999999999)
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id="-5214407126",
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="sailing_enthusiast",
        text="Who is Captain Robbie and what is the yacht?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-11 10:00:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    claim = claim_next_inbox_row(conn_op, project_id="onelove", worker_id="test_worker_onelove_c")
    assert claim is not None

    mock_llm = MockLLMClient()
    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        llm_client=mock_llm,
        simulated=True,
    )

    assert result.responded is True
    assert len(mock_llm.calls) > 0
    prompt_lower = mock_llm.calls[-1]["user_prompt"].lower()
    assert "robbie" in prompt_lower or "robert olson" in prompt_lower
    assert "nautitech" in prompt_lower or "82" in prompt_lower or "catamaran" in prompt_lower


def test_system_prompt_uses_default_zoe_identity():
    """Assert ONELOVE system prompt uses DEFAULT_ZOE_IDENTITY_PROMPT and no pirate slang."""
    system_prompt = get_project_system_prompt("onelove")
    prompt_lower = system_prompt.lower()

    assert "ahoy" not in prompt_lower
    assert "matey" not in prompt_lower
    assert "crew" not in prompt_lower
    assert "on deck" not in prompt_lower
    assert "Tenant Boundary Guard:" in system_prompt
    assert "You are the AI Community Manager for One Love ($ONELOVE)" in system_prompt
