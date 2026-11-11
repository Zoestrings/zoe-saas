"""Verification tests for Strict Isolation, JARVIS Persona & Market Cap Scanner.

Tests:
- Test A (Isolation): Ask ONELOVE "What is the price of FLY?".
  Assert she refuses and does not query Hummingbird.
- Test B (Market Cap): Ask ONELOVE "What is the market cap?".
  Assert she returns the live DexScreener data INCLUDING the market cap value.
- Test C (JARVIS): Ask ONELOVE "What is a blockchain?".
  Assert she answers perfectly with no pirate slang.
"""

from pathlib import Path
import random
import pytest

from zoe.conversation.intent import detect_intent
from zoe.conversation.prompt_builder import DEFAULT_ZOE_IDENTITY_PROMPT, build_prompt
from zoe.conversation.router import route_intent
from zoe.db.connections import open_operational_db
from zoe.inbox.inbox_service import persist_batch
from zoe.llm.mock import MockLLMClient
from zoe.telegram.normalizer import NormalizedMessage
from zoe.worker.claim import claim_next_inbox_row
from zoe.worker.pipeline import process_message

ONELOVE_CA = "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon"
HUMMINGBIRD_CA = "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf"


def test_price_and_market_cap_keywords_route_to_api_call():
    """Requirement 4: Ensure price, market cap, liquidity, chart route to api_call."""
    queries = [
        "what is the price of FLY?",
        "what is the current price of ONELOVE?",
        "what is the market cap?",
        "check market cap",
        "how much is the liquidity?",
        "check the chart please",
        "show me 24h volume",
    ]
    for q in queries:
        routed = route_intent(q)
        assert routed == "api_call", f"Expected 'api_call' for '{q}', got '{routed}'"

        detected = detect_intent(q)
        assert detected.intent == "api_call", f"Expected 'api_call' for '{q}', got '{detected.intent}'"


def test_a_isolation_refuses_foreign_token_before_dexscreener(monkeypatch):
    """Test A (Isolation): Ask ONELOVE 'What is the price of FLY?'.
    Assert she refuses ('I only manage data for One Love ($ONELOVE)...') and does NOT query Hummingbird."""
    conn_op = open_operational_db("data/operational/operational.db")

    queried_urls = []

    def mock_get(url, *args, **kwargs):
        queried_urls.append(url)
        raise RuntimeError("DexScreener should not be called for foreign token queries!")

    monkeypatch.setattr("httpx.Client.get", lambda self, url, **kwargs: mock_get(url, **kwargs))

    uid = random.randint(100000000, 999999999)
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id="-5214407126",
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="trader_joe",
        text="What is the price of FLY?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-10 10:00:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    claim = claim_next_inbox_row(conn_op, project_id="onelove", worker_id="test_worker_isolation")
    assert claim is not None

    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        simulated=True,
    )

    assert result.responded is True
    assert result.response_text is not None

    resp = result.response_text
    # 1. Assert she refuses and states tenant boundary
    assert "I only manage data for One Love ($ONELOVE)" in resp
    assert "I don't have specific info on that other token" in resp

    # 2. Assert DexScreener was NOT queried for Hummingbird
    assert not any(HUMMINGBIRD_CA in url for url in queried_urls)


def test_b_market_cap_query_returns_dexscreener_mcap(monkeypatch):
    """Test B (Market Cap): Ask ONELOVE 'What is the market cap?'.
    Assert she returns the live DexScreener data INCLUDING the market cap value."""
    conn_op = open_operational_db("data/operational/operational.db")

    queried_cas = []

    class MockDexScreenerResponse:
        status_code = 200

        def json(self):
            return {
                "pairs": [
                    {
                        "baseToken": {"name": "One Love", "symbol": "ONELOVE"},
                        "priceUsd": "0.000045",
                        "marketCap": 2450000.0,
                        "fdv": 2450000.0,
                        "liquidity": {"usd": 15230.0},
                        "volume": {"h24": 4500.0},
                    }
                ]
            }

    def mock_get(url, *args, **kwargs):
        queried_cas.append(url)
        return MockDexScreenerResponse()

    monkeypatch.setattr("httpx.Client.get", lambda self, url, **kwargs: mock_get(url, **kwargs))

    uid = random.randint(100000000, 999999999)
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id="-5214407126",
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="trader_joe",
        text="What is the market cap?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-10 10:00:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    claim = claim_next_inbox_row(conn_op, project_id="onelove", worker_id="test_worker_mcap")
    assert claim is not None

    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        simulated=True,
    )

    assert result.responded is True
    assert result.response_text is not None

    resp = result.response_text
    # Assert live DexScreener queried for ONELOVE's CA
    assert any(ONELOVE_CA in url for url in queried_cas)

    # Assert live report includes Market Cap alongside Price, Liquidity, and Volume
    assert "Market Cap: $2,450,000.00" in resp or "Market Cap:" in resp
    assert "2,450,000" in resp
    assert "Price: $0.000045" in resp
    assert "Liquidity: $15,230.00" in resp
    assert "24h Volume: $4,500.00" in resp


def test_c_jarvis_answers_blockchain_with_no_pirate_slang():
    """Test C (JARVIS): Ask ONELOVE 'What is a blockchain?'.
    Assert she answers perfectly with no pirate slang."""
    conn_op = open_operational_db("data/operational/operational.db")

    uid = random.randint(100000000, 999999999)
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=uid,
        group_id="-5214407126",
        telegram_message_id=uid % 100000,
        pseudonymous_user_id="crypto_novice",
        text="What is a blockchain?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-10 10:00:00",
    )
    persist_batch(conn_op, "onelove", [msg], uid)

    claim = claim_next_inbox_row(conn_op, project_id="onelove", worker_id="test_worker_blockchain")
    assert claim is not None

    mock_llm = MockLLMClient()
    result = process_message(
        inbox_row=claim,
        db_conns={"operational": conn_op},
        llm_client=mock_llm,
        simulated=True,
    )

    assert result.responded is True
    assert result.response_text is not None

    # Assert response contains Web3 explanation and ZERO pirate slang
    resp_lower = result.response_text.lower()
    assert "blockchain" in resp_lower or "ledger" in resp_lower or "decentralized" in resp_lower
    assert "ahoy" not in resp_lower
    assert "matey" not in resp_lower
    assert "crew" not in resp_lower
    assert "deck" not in resp_lower


def test_prompt_builder_strict_tenant_boundary_and_no_pirate():
    """Assert prompt builder injects the exact Tenant Boundary Guard and has no pirate text."""
    msg = NormalizedMessage(
        project_id="onelove",
        telegram_update_id=1,
        group_id="-5214407126",
        telegram_message_id=10,
        pseudonymous_user_id="user_test",
        text="GM! What's the play today?",
        reply_to_message_id=None,
        is_forward=False,
        timestamp="2026-11-10 10:00:00",
    )

    prompt = build_prompt(
        message=msg,
        community_context=[],
        official_chunks=[],
        conversation_history=[],
    )

    prompt_lower = prompt.lower()
    # No pirate slang
    assert "ahoy" not in prompt_lower
    assert "matey" not in prompt_lower
    assert "crew" not in prompt_lower
    assert "on deck" not in prompt_lower

    # Contains exact tenant boundary
    assert "Tenant Boundary Guard:" in prompt
    assert "You are the AI Community Manager for One Love ($ONELOVE)" in prompt
    assert "I only manage data for One Love ($ONELOVE)" in prompt
