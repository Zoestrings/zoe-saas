"""Unit tests for the Proactive Sentiment Radar (JARVIS Mode)."""

import pytest
from unittest.mock import MagicMock

from zoe.conversation.sentiment import (
    analyze_group_sentiment,
    analyze_group_sentiment_sync,
    classify_sentiment_heuristics,
)


def test_sentiment_monitor_detects_panicked_fud():
    """Assert that 5 panic/FUD messages classify as 'panicked/fud'."""
    panic_messages = [
        "I got hacked!",
        "The price is crashing hard!",
        "Total scam, the dev dumped!",
        "Is this project dead? The liquidity is dropping!",
        "Sell now before it goes to zero!",
    ]
    result = analyze_group_sentiment_sync(panic_messages)
    assert result == "panicked/fud"


def test_sentiment_monitor_detects_hyped_messages():
    """Assert that hype/bullish messages classify as 'hyped'."""
    hype_messages = [
        "LFG to the moon!",
        "This is an easy 100x gem!",
        "Huge pump incoming!",
        "We are flying, ATH soon!",
        "Send it to valhalla!",
    ]
    result = analyze_group_sentiment_sync(hype_messages)
    assert result == "hyped"


def test_sentiment_monitor_detects_calm_messages():
    """Assert that standard community chat classifies as 'calm'."""
    calm_messages = [
        "Good morning everyone",
        "How are you all doing today?",
        "Reading through the documentation now",
        "Setting up my validator node",
        "Nice to meet everyone in the community",
    ]
    result = analyze_group_sentiment_sync(calm_messages)
    assert result == "calm"


@pytest.mark.anyio
async def test_async_sentiment_monitor():
    """Verify asynchronous entrypoint returns 'panicked/fud' for panic messages."""
    panic_messages = [
        "Help I got drained by a scammer!",
        "Price is dumping!",
        "Is this a rugpull?",
    ]
    result = await analyze_group_sentiment(panic_messages)
    assert result == "panicked/fud"


def test_sentiment_monitor_with_llm_override():
    """Verify LLM client is consulted when heuristics are calm."""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "panicked/fud"

    messages = ["Something feels strange here", "Not sure about this update"]
    result = analyze_group_sentiment_sync(messages, llm_client=mock_llm)
    assert result == "panicked/fud"
    mock_llm.generate.assert_called_once()

