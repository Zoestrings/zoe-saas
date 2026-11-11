"""Unit tests for DexScreener tool integration (Stage 11 Gate)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from zoe.tools.dexscreener import (
    get_token_price,
    get_token_price_sync,
    search_token_price,
    search_token_price_sync,
)


SAMPLE_DEXSCREENER_RESPONSE = {
    "schemaVersion": "1.0.0",
    "pairs": [
        {
            "chainId": "solana",
            "dexId": "raydium",
            "url": "https://dexscreener.com/solana/EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf",
            "pairAddress": "PairAddress123",
            "baseToken": {
                "address": "EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf",
                "name": "Hummingbird",
                "symbol": "FLY",
            },
            "quoteToken": {
                "address": "So11111111111111111111111111111111111111112",
                "name": "Wrapped SOL",
                "symbol": "SOL",
            },
            "priceNative": "0.000015",
            "priceUsd": "0.002420",
            "liquidity": {
                "usd": 93712.04,
                "base": 38664476,
                "quote": 140.99,
            },
            "volume": {
                "h24": 1250.50,
                "h6": 300.00,
                "h1": 50.00,
                "m5": 0.00,
            },
        }
    ],
}


@pytest.mark.anyio
async def test_get_token_price_parses_json_correctly():
    """Verify get_token_price extracts priceUsd, liquidity.usd, and volume.h24."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_DEXSCREENER_RESPONSE

    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await get_token_price(
        token_address="EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf",
        client=mock_client,
    )

    assert "Token: Hummingbird ($FLY)" in result
    assert "Current Price: $0.002420 USD" in result
    assert "Total Liquidity: $93,712.04 USD" in result
    assert "24h Volume: $1,250.50 USD" in result


@pytest.mark.anyio
async def test_get_token_price_handles_empty_pairs():
    """Verify get_token_price handles when no pairs exist for a token."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"pairs": []}

    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await get_token_price("NonExistentCA", client=mock_client)
    assert "No active trading pairs found" in result


@pytest.mark.anyio
async def test_get_token_price_handles_api_error():
    """Verify graceful error reporting when API returns non-200."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 500

    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await get_token_price("EmgFnDhxoDBCyFPoSoo2ejrsJRHNt1ovaaB3gCNDnRvf", client=mock_client)
    assert "Unable to retrieve live market data" in result


@pytest.mark.anyio
async def test_search_token_price_by_ticker():
    """Verify search_token_price queries the search endpoint and formats multi-chain results."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "pairs": [
            {
                "chainId": "solana",
                "dexId": "raydium",
                "baseToken": {"symbol": "SOL", "name": "Solana"},
                "priceUsd": "188.45",
                "liquidity": {"usd": 15420300.0},
                "volume": {"h24": 98452000.0},
                "priceChange": {"h24": 4.25},
            }
        ]
    }

    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await search_token_price("$SOL", client=mock_client)

    mock_client.get.assert_called_once_with(
        "https://api.dexscreener.com/latest/dex/search?q=SOL",
        timeout=10.0,
    )
    assert "Token: Solana ($SOL) on Solana (Raydium)" in result
    assert "Current Price: $188.45 USD" in result
    assert "24h Change: +4.25%" in result
    assert "Total Liquidity: $15,420,300.00 USD" in result
    assert "24h Volume: $98,452,000.00 USD" in result


@pytest.mark.anyio
async def test_search_token_price_empty_query():
    """Verify empty query returns early message."""
    result = await search_token_price("   ")
    assert "No token specified" in result


