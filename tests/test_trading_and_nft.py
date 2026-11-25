"""Automated Tests for Pre-Trade Intelligence Brief & NFT Generation Studio (Pillar 2)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from zoe.tools.trading_intel import generate_trade_brief, DISCLAIMER
from zoe.tools.nft_studio import generate_nft_image


def test_generate_trade_brief_returns_3_factual_bullets():
    """Verify generate_trade_brief returns 3 objective bullets and disclaimer without financial advice."""
    mock_scan = {
        "name": "Jupiter",
        "symbol": "JUP",
        "market": {
            "price_usd": 0.95,
            "liquidity_usd": 4200000.0,
            "market_cap": 1200000000.0,
        },
        "security": {
            "top_10_holders_percent": 18.5,
            "is_honeypot": False,
            "mint_revoked": True,
            "lp_locked": True,
        },
    }
    mock_x = {
        "sentiment": "Bullish",
        "summary": "High developer activity and strong Solana DEX volume.",
    }

    with (
        patch("zoe.tools.trading_intel.scan_token", new=AsyncMock(return_value=mock_scan)),
        patch("zoe.tools.trading_intel.get_token_price", new=AsyncMock(return_value="JUP $0.95")),
        patch("zoe.tools.trading_intel.analyze_x_sentiment", new=AsyncMock(return_value=mock_x)),
    ):
        res = asyncio.run(generate_trade_brief("JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN"))

    assert res["token_symbol"] == "JUP"
    assert len(res["bullets"]) == 3
    assert "Market Health" in res["bullets"][0]
    assert "Sentiment" in res["bullets"][1]
    assert "Risk Warning" in res["bullets"][2]
    assert res["disclaimer"] == DISCLAIMER


def test_generate_nft_image_returns_pollinations_url():
    """Verify generate_nft_image encodes prompt and returns Pollinations URL."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://image.pollinations.ai/prompt/cyberpunk%20pirate?width=1024&height=1024&nologo=true"

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("zoe.tools.nft_studio.httpx.AsyncClient", return_value=mock_client):
        url = asyncio.run(generate_nft_image("cyberpunk pirate"))

    assert "pollinations.ai/prompt/cyberpunk%20pirate" in url
    assert "width=1024" in url
