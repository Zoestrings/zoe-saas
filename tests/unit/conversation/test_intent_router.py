"""Unit tests for the Stage 10 Tool and Intent Router."""

import pytest
from zoe.conversation.router import route_intent


@pytest.mark.automated
def test_router_identifies_api_call_questions():
    """Verify market, on-chain, and price inquiries for project token route to 'api_call'."""
    assert route_intent("What is the price of $FLY?") == "api_call"
    assert route_intent("how much is $FLY right now?") == "api_call"
    assert route_intent("What is the market cap?") == "api_call"
    assert route_intent("Can you check the liquidity pool on DexScreener?") == "api_call"
    assert route_intent("What is the 24h volume?") == "api_call"
    assert route_intent("Where can I see the chart?") == "api_call"
    assert route_intent("What is the contract address (ca)?") == "api_call"


@pytest.mark.automated
def test_router_smart_price_routing_for_external_assets():
    """Verify inquiries for external cryptocurrency asset prices route to 'web_search'."""
    assert route_intent("What is the price of Bitcoin?") == "web_search"
    assert route_intent("What is the price of $FLY?") == "api_call"
    assert route_intent("What is the price of Ethereum?") == "web_search"
    assert route_intent("How much is Solana worth right now?") == "web_search"
    assert route_intent("What is the current BTC price?") == "web_search"
    assert route_intent("Can you search the web for Dogecoin price?") == "web_search"


@pytest.mark.automated
def test_router_identifies_knowledge_questions():
    """Verify project documentation, staking, KYC, and mechanics inquiries route to 'knowledge'."""
    assert route_intent("What is Hummingbird?") == "knowledge"
    assert route_intent("What is the $FLY token used for?") == "knowledge"
    assert route_intent("Why does Hummingbird require KYC?") == "knowledge"
    assert route_intent("How do staking rewards work?") == "knowledge"
    assert route_intent("How can I get a referral code?") == "knowledge"
    assert route_intent("What are social campaigns and B2B campaigns?") == "knowledge"
    assert route_intent("Where can I read the whitepaper and docs?") == "knowledge"


@pytest.mark.automated
def test_router_identifies_general_chat():
    """Verify greetings, jokes, and broad crypto definitions route to 'general'."""
    assert route_intent("Hello!") == "general"
    assert route_intent("gm everyone") == "general"
    assert route_intent("Tell me a funny joke") == "general"
    assert route_intent("Who are you?") == "general"
    assert route_intent("How are you doing today?") == "general"
    assert route_intent("What is a blockchain?") == "general"
    assert route_intent("Thanks for the help!") == "general"

