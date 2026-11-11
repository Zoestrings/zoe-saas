"""DexScreener and CoinGecko API tool fetching live market data, price, liquidity, and volume."""

import asyncio
from typing import Any, Dict, Optional
import httpx

from zoe.utils.logging import get_logger

logger = get_logger("zoe.tools.dexscreener")

# Global persistent synchronous client with connection pooling
_SYNC_CLIENT: Optional[httpx.Client] = None

# Comprehensive map of popular crypto tickers and names to CoinGecko IDs
COINGECKO_TICKER_MAP = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "ether": "ethereum",
    "sol": "solana",
    "solana": "solana",
    "doge": "dogecoin",
    "dogecoin": "dogecoin",
    "xrp": "ripple",
    "ripple": "ripple",
    "ada": "cardano",
    "cardano": "cardano",
    "bnb": "binancecoin",
    "binance": "binancecoin",
    "avax": "avalanche-2",
    "avalanche": "avalanche-2",
    "ton": "the-open-network",
    "toncoin": "the-open-network",
    "sui": "sui",
    "near": "near",
    "trx": "tron",
    "tron": "tron",
    "link": "chainlink",
    "chainlink": "chainlink",
    "dot": "polkadot",
    "polkadot": "polkadot",
    "pepe": "pepe",
    "shib": "shiba-inu",
    "shiba": "shiba-inu",
    "bonk": "bonk",
    "wif": "dogwifcoin",
    "dogwifhat": "dogwifcoin",
    "uni": "uniswap",
    "uniswap": "uniswap",
    "ltc": "litecoin",
    "litecoin": "litecoin",
    "matic": "matic-network",
    "pol": "matic-network",
    "polygon": "matic-network",
    "arb": "arbitrum",
    "arbitrum": "arbitrum",
    "op": "optimism",
    "optimism": "optimism",
    "apt": "aptos",
    "aptos": "aptos",
}


def _get_sync_client() -> httpx.Client:
    global _SYNC_CLIENT
    if _SYNC_CLIENT is None or _SYNC_CLIENT.is_closed:
        _SYNC_CLIENT = httpx.Client(timeout=6.0, follow_redirects=True)
    return _SYNC_CLIENT


def _fetch_coingecko_price_sync(coin_id: str, display_name: str) -> Optional[str]:
    """Fetch authoritative spot price and 24h change from CoinGecko in <0.5s."""
    try:
        client = _get_sync_client()
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
        resp = client.get(url)
        if resp.status_code == 200:
            data = resp.json().get(coin_id, {})
            usd = data.get("usd")
            change = data.get("usd_24h_change")
            if usd is not None:
                lines = [
                    f"Token: {display_name} (${coin_id.upper()})",
                    f"Current Price: ${usd:,.2f} USD" if usd >= 1 else f"Current Price: ${usd} USD",
                ]
                if change is not None:
                    lines.append(f"24h Change: {float(change):+.2f}%")
                return "\n".join(lines)
    except Exception as exc:
        logger.debug("CoinGecko price fetch failed for '%s': %s", coin_id, exc)
    return None


async def get_token_price(token_address: str, client: Optional[httpx.AsyncClient] = None) -> str:
    """Fetch live token price, liquidity, and 24h volume from DexScreener.
    
    Args:
        token_address: The on-chain contract address of the token.
        client: Optional httpx.AsyncClient instance for testing/mocking.
        
    Returns:
        Formatted summary string with priceUsd, liquidity.usd, and volume.h24.
    """
    if not token_address or not token_address.strip():
        return "No contract address configured for live price lookup."

    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address.strip()}"

    try:
        if client is not None:
            response = await client.get(url, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=8.0) as local_client:
                response = await local_client.get(url)

        if response.status_code != 200:
            logger.warning(
                "DexScreener API returned non-200 status %d for token %s",
                response.status_code,
                token_address,
            )
            return "Unable to retrieve live market data from DexScreener at this time."

        data: Dict[str, Any] = response.json()
        pairs = data.get("pairs")
        if not pairs or not isinstance(pairs, list) or len(pairs) == 0:
            return f"No active trading pairs found on DexScreener for address {token_address}."

        sorted_pairs = sorted(
            pairs,
            key=lambda p: (
                float(p.get("volume", {}).get("h24") or 0.0) > 10.0,
                float(p.get("liquidity", {}).get("usd") or 0.0) if isinstance(p.get("liquidity"), dict) else 0.0,
            ),
            reverse=True,
        )
        pair = sorted_pairs[0]

        price_usd = pair.get("priceUsd", "N/A")
        base_token = pair.get("baseToken", {})
        symbol = base_token.get("symbol", "TOKEN")
        name = base_token.get("name", "Token")

        liquidity = pair.get("liquidity", {})
        liquidity_usd = liquidity.get("usd") if isinstance(liquidity, dict) else None

        volume = pair.get("volume", {})
        volume_24h = volume.get("h24") if isinstance(volume, dict) else None

        parts = [f"Token: {name} (${symbol})", f"Current Price: ${price_usd} USD"]
        if liquidity_usd is not None:
            parts.append(f"Total Liquidity: ${float(liquidity_usd):,.2f} USD")
        if volume_24h is not None:
            parts.append(f"24h Volume: ${float(volume_24h):,.2f} USD")

        return "\n".join(parts)

    except Exception as exc:
        logger.error("Exception fetching DexScreener data for %s: %s", token_address, str(exc))
        return "Unable to retrieve live market data due to a temporary network issue."


def get_token_price_sync(token_address: str) -> str:
    """Fast, synchronous helper for get_token_price avoiding event loop contention."""
    if not token_address or not token_address.strip():
        return "No contract address configured for live price lookup."

    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address.strip()}"
    try:
        client = _get_sync_client()
        response = client.get(url)
        if response.status_code != 200:
            return "Unable to retrieve live market data from DexScreener at this time."

        data: Dict[str, Any] = response.json()
        pairs = data.get("pairs")
        if not pairs or not isinstance(pairs, list) or len(pairs) == 0:
            return f"No active trading pairs found on DexScreener for address {token_address}."

        sorted_pairs = sorted(
            pairs,
            key=lambda p: (
                float(p.get("volume", {}).get("h24") or 0.0) > 10.0,
                float(p.get("liquidity", {}).get("usd") or 0.0) if isinstance(p.get("liquidity"), dict) else 0.0,
            ),
            reverse=True,
        )
        pair = sorted_pairs[0]

        price_usd = pair.get("priceUsd", "N/A")
        base_token = pair.get("baseToken", {})
        symbol = base_token.get("symbol", "TOKEN")
        name = base_token.get("name", "Token")

        liquidity = pair.get("liquidity", {})
        liquidity_usd = liquidity.get("usd") if isinstance(liquidity, dict) else None

        volume = pair.get("volume", {})
        volume_24h = volume.get("h24") if isinstance(volume, dict) else None

        parts = [f"Token: {name} (${symbol})", f"Current Price: ${price_usd} USD"]
        if liquidity_usd is not None:
            parts.append(f"Total Liquidity: ${float(liquidity_usd):,.2f} USD")
        if volume_24h is not None:
            parts.append(f"24h Volume: ${float(volume_24h):,.2f} USD")

        return "\n".join(parts)
    except Exception as exc:
        logger.warning("Sync DexScreener error for %s: %s", token_address, exc)
        return "Unable to retrieve live market data due to a temporary network issue."


async def search_token_price(query: str, client: Optional[httpx.AsyncClient] = None) -> str:
    """Search DexScreener across all DEX pairs for any token name, symbol, or contract address.

    Args:
        query: Token symbol (e.g. 'PEPE', 'SOL', 'WIF', 'BONK'), name, or contract address.
        client: Optional httpx.AsyncClient instance for testing/mocking.

    Returns:
        Formatted summary string with token details, chain, DEX, price, liquidity, and volume.
    """
    clean_q = query.strip().lstrip("$")
    if not clean_q:
        return "No token specified for market search."

    is_address = len(clean_q) >= 30 and " " not in clean_q
    if is_address:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{clean_q}"
    else:
        url = f"https://api.dexscreener.com/latest/dex/search?q={clean_q}"

    try:
        if client is not None:
            response = await client.get(url, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=8.0) as local_client:
                response = await local_client.get(url)

        if response.status_code != 200:
            return "Unable to retrieve live market data from DexScreener at this time."

        data: Dict[str, Any] = response.json()
        pairs = data.get("pairs")
        if not pairs or not isinstance(pairs, list) or len(pairs) == 0:
            return f"No active trading pairs found on DexScreener for {query}."

        sorted_pairs = sorted(
            pairs,
            key=lambda p: (
                float(p.get("volume", {}).get("h24") or 0.0) > 50.0,
                float(p.get("liquidity", {}).get("usd") or 0.0) if isinstance(p.get("liquidity"), dict) else 0.0,
            ),
            reverse=True,
        )
        pair = sorted_pairs[0]

        price_usd = pair.get("priceUsd", "N/A")
        base_token = pair.get("baseToken", {})
        symbol = base_token.get("symbol", clean_q.upper())
        name = base_token.get("name", symbol)
        chain_id = str(pair.get("chainId", "crypto")).capitalize()
        dex_id = str(pair.get("dexId", "DEX")).capitalize()

        liquidity = pair.get("liquidity", {})
        liquidity_usd = liquidity.get("usd") if isinstance(liquidity, dict) else None

        volume = pair.get("volume", {})
        volume_24h = volume.get("h24") if isinstance(volume, dict) else None

        price_change = pair.get("priceChange", {})
        change_24h = price_change.get("h24") if isinstance(price_change, dict) else None

        parts = [
            f"Token: {name} (${symbol}) on {chain_id} ({dex_id})",
            f"Current Price: ${price_usd} USD",
        ]
        if change_24h is not None:
            parts.append(f"24h Change: {float(change_24h):+.2f}%")
        if liquidity_usd is not None:
            parts.append(f"Total Liquidity: ${float(liquidity_usd):,.2f} USD")
        if volume_24h is not None:
            parts.append(f"24h Volume: ${float(volume_24h):,.2f} USD")

        return "\n".join(parts)

    except Exception as exc:
        logger.error("Exception in search_token_price for %s: %s", query, str(exc))
        return f"Unable to fetch market data for {query} due to network issue."


def search_token_price_sync(query: str) -> str:
    """Fast, synchronous universal token search combining CoinGecko and DexScreener."""
    clean_q = query.strip().lstrip("$")
    if not clean_q:
        return "No token specified for market search."

    # 1. Check CoinGecko for top macro tokens (fastest: <0.4s and 100% accurate)
    lookup_key = clean_q.lower()
    if lookup_key in COINGECKO_TICKER_MAP:
        cg_id = COINGECKO_TICKER_MAP[lookup_key]
        display = clean_q.upper()
        cg_result = _fetch_coingecko_price_sync(cg_id, display)
        if cg_result:
            return cg_result

    # 2. DexScreener for DEX tokens, meme coins, and contract addresses
    is_address = len(clean_q) >= 30 and " " not in clean_q
    if is_address:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{clean_q}"
    else:
        url = f"https://api.dexscreener.com/latest/dex/search?q={clean_q}"

    try:
        client = _get_sync_client()
        response = client.get(url)
        if response.status_code != 200:
            return "Unable to retrieve live market data from DexScreener at this time."

        data: Dict[str, Any] = response.json()
        pairs = data.get("pairs")
        if not pairs or not isinstance(pairs, list) or len(pairs) == 0:
            return f"No active trading pairs found on DexScreener for {query}."

        sorted_pairs = sorted(
            pairs,
            key=lambda p: (
                float(p.get("volume", {}).get("h24") or 0.0) > 50.0,
                float(p.get("liquidity", {}).get("usd") or 0.0) if isinstance(p.get("liquidity"), dict) else 0.0,
            ),
            reverse=True,
        )
        pair = sorted_pairs[0]

        price_usd = pair.get("priceUsd", "N/A")
        base_token = pair.get("baseToken", {})
        symbol = base_token.get("symbol", clean_q.upper())
        name = base_token.get("name", symbol)
        chain_id = str(pair.get("chainId", "crypto")).capitalize()
        dex_id = str(pair.get("dexId", "DEX")).capitalize()

        liquidity = pair.get("liquidity", {})
        liquidity_usd = liquidity.get("usd") if isinstance(liquidity, dict) else None

        volume = pair.get("volume", {})
        volume_24h = volume.get("h24") if isinstance(volume, dict) else None

        price_change = pair.get("priceChange", {})
        change_24h = price_change.get("h24") if isinstance(price_change, dict) else None

        parts = [
            f"Token: {name} (${symbol}) on {chain_id} ({dex_id})",
            f"Current Price: ${price_usd} USD",
        ]
        if change_24h is not None:
            parts.append(f"24h Change: {float(change_24h):+.2f}%")
        if liquidity_usd is not None:
            parts.append(f"Total Liquidity: ${float(liquidity_usd):,.2f} USD")
        if volume_24h is not None:
            parts.append(f"24h Volume: ${float(volume_24h):,.2f} USD")

        return "\n".join(parts)

    except Exception as exc:
        logger.error("Sync search_token_price error for %s: %s", query, str(exc))
        return f"Unable to fetch market data for {query} due to network issue."
