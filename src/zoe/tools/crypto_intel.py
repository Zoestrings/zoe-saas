"""Crypto intelligence module analyzing on-chain contract addresses via DexScreener on-demand."""

from typing import Any, Dict, List, Optional
import httpx

from zoe.utils.logging import get_logger

logger = get_logger("zoe.tools.crypto_intel")


async def analyze_contract_address(
    contract_address: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Fetch token metadata, price, liquidity, and 24h volume from DexScreener.
    
    Strictly on-demand with a 10-second timeout to protect event loop and RAM.
    """
    clean_ca = contract_address.strip()
    if not clean_ca:
        return {"error": "Empty contract address provided"}

    url = f"https://api.dexscreener.com/latest/dex/tokens/{clean_ca}"

    try:
        if client is not None:
            resp = await client.get(url, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=10.0) as local_client:
                resp = await local_client.get(url)

        if resp.status_code != 200:
            logger.warning("DexScreener returned status %d for CA %s", resp.status_code, clean_ca)
            return {"error": f"DexScreener API error {resp.status_code}", "ca": clean_ca}

        data = resp.json()
        pairs = data.get("pairs") or []
        if not pairs:
            return {"error": "No trading pairs found", "ca": clean_ca}

        # Select highest liquidity pair
        sorted_pairs = sorted(
            pairs,
            key=lambda p: float(p.get("liquidity", {}).get("usd") or 0.0) if isinstance(p.get("liquidity"), dict) else 0.0,
            reverse=True,
        )
        top_pair = sorted_pairs[0]

        base_token = top_pair.get("baseToken", {})
        name = base_token.get("name") or "Unknown"
        symbol = base_token.get("symbol") or "TOKEN"
        price_usd = top_pair.get("priceUsd") or "0.00"

        liq = top_pair.get("liquidity", {})
        liquidity_usd = liq.get("usd") if isinstance(liq, dict) else None

        vol = top_pair.get("volume", {})
        volume_24h = vol.get("h24") if isinstance(vol, dict) else None

        mcap = top_pair.get("marketCap") or top_pair.get("fdv")

        return {
            "ca": clean_ca,
            "name": f"{name} (${symbol})",
            "raw_name": name,
            "symbol": symbol,
            "price": f"${price_usd}",
            "raw_price": price_usd,
            "market_cap": f"${float(mcap):,.2f}" if mcap is not None else "N/A",
            "raw_market_cap": mcap,
            "liquidity": f"${float(liquidity_usd):,.2f}" if liquidity_usd is not None else "N/A",
            "volume_24h": f"${float(volume_24h):,.2f}" if volume_24h is not None else "N/A",
        }

    except Exception as exc:
        logger.error("Error analyzing contract address %s: %s", clean_ca, exc)
        return {"error": str(exc), "ca": clean_ca}


def format_ca_analysis(intel: Dict[str, Any]) -> str:
    """Format crypto intelligence into a strict, data-only report."""
    return format_token_intel_response(intel)


def analyze_contract_address_sync(contract_address: str) -> str:
    """Synchronous wrapper for contract address analysis."""
    clean_ca = contract_address.strip()
    if not clean_ca:
        return "🪙 Unknown Token · N/A\nCA: N/A\n💰 Price: N/A\n🌐 Market Cap: N/A\n💧 Liquidity: N/A\n📊 24h Volume: N/A"

    intel = get_token_intel_sync(clean_ca)
    return format_token_intel_response(intel)


_DEFAULT_ANALYZE_SYNC = analyze_contract_address_sync


def resolve_target_token_address(
    ca: Optional[str] = None,
    project_id: Optional[str] = None,
    token_address: Optional[str] = None,
) -> str:
    """Resolve token address from explicit arguments or project config without hardcoded globals."""
    if token_address and str(token_address).strip():
        return str(token_address).strip()
    if ca and str(ca).strip():
        return str(ca).strip()
    if project_id:
        try:
            from zoe.settings import load_project_config
            cfg = load_project_config(project_id)
            addr = cfg.get("token_address") or cfg.get("project", {}).get("token_address")
            if addr:
                return str(addr).strip()
        except Exception:
            pass
    return ""


async def get_token_intel(
    ca: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
    project_id: Optional[str] = None,
    token_address: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch live token intelligence from DexScreener on-demand.
    
    Extracts name, symbol, price (USD), market cap (USD), liquidity (USD), and 24h volume (USD).
    Accepts project_id or token_address and never reads from global hardcoded variables.
    """
    clean_ca = resolve_target_token_address(ca=ca, project_id=project_id, token_address=token_address)
    if not clean_ca:
        return {
            "ca": clean_ca,
            "found": False,
            "name": "Unknown",
            "symbol": "N/A",
            "price": "N/A",
            "market_cap": "N/A",
            "fdv": "N/A",
            "liquidity": "N/A",
            "volume_24h": "N/A",
            "error": "Empty contract address",
        }

    url = f"https://api.dexscreener.com/latest/dex/tokens/{clean_ca}"
    try:
        if client is not None:
            resp = await client.get(url, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=10.0) as local_client:
                resp = await local_client.get(url)

        if resp.status_code != 200:
            logger.warning("DexScreener returned status %d for CA %s", resp.status_code, clean_ca)
            return {
                "ca": clean_ca,
                "found": False,
                "name": "Unknown",
                "symbol": "N/A",
                "price": "N/A",
                "market_cap": "N/A",
                "fdv": "N/A",
                "liquidity": "N/A",
                "volume_24h": "N/A",
                "error": f"DexScreener API error {resp.status_code}",
            }

        data = resp.json()
        pairs = data.get("pairs") or []
        if not pairs:
            return {
                "ca": clean_ca,
                "found": False,
                "name": "Unknown",
                "symbol": "N/A",
                "price": "N/A",
                "market_cap": "N/A",
                "fdv": "N/A",
                "liquidity": "N/A",
                "volume_24h": "N/A",
                "error": "No trading pairs found",
            }

        sorted_pairs = sorted(
            pairs,
            key=lambda p: float(p.get("liquidity", {}).get("usd") or 0.0)
            if isinstance(p.get("liquidity"), dict)
            else 0.0,
            reverse=True,
        )
        top_pair = sorted_pairs[0]

        base_token = top_pair.get("baseToken", {})
        name = base_token.get("name") or "Unknown"
        symbol = base_token.get("symbol") or "TOKEN"
        price_usd = top_pair.get("priceUsd") or "0.00"
        mcap = top_pair.get("marketCap") or top_pair.get("fdv")

        liq = top_pair.get("liquidity", {})
        liquidity_usd = liq.get("usd") if isinstance(liq, dict) else None

        vol = top_pair.get("volume", {})
        volume_24h = vol.get("h24") if isinstance(vol, dict) else None

        return {
            "ca": clean_ca,
            "found": True,
            "name": name,
            "symbol": symbol,
            "price": str(price_usd),
            "market_cap": str(mcap) if mcap is not None else "N/A",
            "fdv": str(top_pair.get("fdv")) if top_pair.get("fdv") is not None else "N/A",
            "liquidity": str(liquidity_usd) if liquidity_usd is not None else "0",
            "volume_24h": str(volume_24h) if volume_24h is not None else "0",
            "raw_pair": top_pair,
        }

    except Exception as exc:
        logger.error("Error fetching token intel for %s: %s", clean_ca, exc)
        return {
            "ca": clean_ca,
            "found": False,
            "name": "Unknown",
            "symbol": "N/A",
            "price": "N/A",
            "market_cap": "N/A",
            "fdv": "N/A",
            "liquidity": "N/A",
            "volume_24h": "N/A",
            "error": str(exc),
        }


def get_token_intel_sync(
    ca: Optional[str] = None,
    project_id: Optional[str] = None,
    token_address: Optional[str] = None,
) -> Dict[str, Any]:
    """Synchronous helper for get_token_intel."""
    clean_ca = resolve_target_token_address(ca=ca, project_id=project_id, token_address=token_address)
    if not clean_ca:
        return {
            "ca": clean_ca,
            "found": False,
            "name": "Unknown",
            "symbol": "N/A",
            "price": "N/A",
            "market_cap": "N/A",
            "fdv": "N/A",
            "liquidity": "N/A",
            "volume_24h": "N/A",
            "error": "Empty contract address",
        }

    url = f"https://api.dexscreener.com/latest/dex/tokens/{clean_ca}"
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                logger.warning("DexScreener returned status %d for CA %s", resp.status_code, clean_ca)
                return {
                    "ca": clean_ca,
                    "found": False,
                    "name": "Unknown",
                    "symbol": "N/A",
                    "price": "N/A",
                    "market_cap": "N/A",
                    "fdv": "N/A",
                    "liquidity": "N/A",
                    "volume_24h": "N/A",
                    "error": f"DexScreener API error {resp.status_code}",
                }

            data = resp.json()
            pairs = data.get("pairs") or []
            if not pairs:
                return {
                    "ca": clean_ca,
                    "found": False,
                    "name": "Unknown",
                    "symbol": "N/A",
                    "price": "N/A",
                    "market_cap": "N/A",
                    "fdv": "N/A",
                    "liquidity": "N/A",
                    "volume_24h": "N/A",
                    "error": "No trading pairs found",
                }

            sorted_pairs = sorted(
                pairs,
                key=lambda p: float(p.get("liquidity", {}).get("usd") or 0.0)
                if isinstance(p.get("liquidity"), dict)
                else 0.0,
                reverse=True,
            )
            top_pair = sorted_pairs[0]

            base_token = top_pair.get("baseToken", {})
            name = base_token.get("name") or "Unknown"
            symbol = base_token.get("symbol") or "TOKEN"
            price_usd = top_pair.get("priceUsd") or "0.00"
            mcap = top_pair.get("marketCap") or top_pair.get("fdv")

            liq = top_pair.get("liquidity", {})
            liquidity_usd = liq.get("usd") if isinstance(liq, dict) else None

            vol = top_pair.get("volume", {})
            volume_24h = vol.get("h24") if isinstance(vol, dict) else None

            return {
                "ca": clean_ca,
                "found": True,
                "name": name,
                "symbol": symbol,
                "price": str(price_usd),
                "market_cap": str(mcap) if mcap is not None else "N/A",
                "fdv": str(top_pair.get("fdv")) if top_pair.get("fdv") is not None else "N/A",
                "liquidity": str(liquidity_usd) if liquidity_usd is not None else "0",
                "volume_24h": str(volume_24h) if volume_24h is not None else "0",
                "raw_pair": top_pair,
            }

    except Exception as exc:
        logger.error("Sync token intel error for %s: %s", clean_ca, exc)
        return {
            "ca": clean_ca,
            "found": False,
            "name": "Unknown",
            "symbol": "N/A",
            "price": "N/A",
            "market_cap": "N/A",
            "fdv": "N/A",
            "liquidity": "N/A",
            "volume_24h": "N/A",
            "error": str(exc),
        }


def generate_ca_inline_keyboard(
    ca: str,
    intel: Optional[Dict[str, Any]] = None,
    project_id: Optional[str] = None,
) -> List[List[Dict[str, str]]]:
    """Generate sleek inline keyboard buttons matching and exceeding Coral.
    
    Includes:
    - 📈 Chart (DexScreener pair or token link)
    - 🔍 Solscan / Etherscan block explorer verification
    - ⚡ Buy on Jupiter / Uniswap instant swap
    - 🌐 Website / Community links when available
    - 🐦 Social channels (Twitter, Telegram, TikTok)
    """
    clean_ca = ca.strip()
    chain = "solana"
    raw_pair: Dict[str, Any] = {}
    if intel and isinstance(intel.get("raw_pair"), dict):
        raw_pair = intel["raw_pair"]
        chain = str(raw_pair.get("chainId") or "solana").lower()
    elif clean_ca.startswith("0x"):
        chain = "ethereum"

    # 1. DexScreener Chart URL
    dex_url = raw_pair.get("url") if raw_pair else None
    if not dex_url:
        dex_url = f"https://dexscreener.com/{chain}/{clean_ca}"

    # 2. Block Explorer URL
    if chain == "solana":
        explorer_name = "Solscan"
        explorer_url = f"https://solscan.io/token/{clean_ca}"
    elif chain in ("bsc", "binance"):
        explorer_name = "BscScan"
        explorer_url = f"https://bscscan.com/token/{clean_ca}"
    elif chain == "polygon":
        explorer_name = "PolygonScan"
        explorer_url = f"https://polygonscan.com/token/{clean_ca}"
    elif chain in ("base", "arbitrum", "optimism"):
        explorer_name = f"{chain.capitalize()}Scan"
        explorer_url = f"https://{chain}scan.org/token/{clean_ca}"
    else:
        explorer_name = "Etherscan"
        explorer_url = f"https://etherscan.io/token/{clean_ca}"

    # 3. Swap / Buy URL
    if chain == "solana":
        buy_name = "Buy on Jupiter"
        buy_url = f"https://jup.ag/swap/SOL-{clean_ca}"
    elif chain in ("bsc", "binance"):
        buy_name = "Buy on PancakeSwap"
        buy_url = f"https://pancakeswap.finance/swap?outputCurrency={clean_ca}"
    else:
        buy_name = "Buy on Uniswap"
        buy_url = f"https://app.uniswap.org/#/swap?outputCurrency={clean_ca}"

    keyboard: List[List[Dict[str, str]]] = [
        [
            {"text": "📈 Chart", "url": dex_url},
            {"text": f"🔍 {explorer_name}", "url": explorer_url},
        ],
        [
            {"text": f"⚡ {buy_name}", "url": buy_url},
        ],
    ]

    # Optional official website if present in DexScreener pair metadata
    info = raw_pair.get("info") if isinstance(raw_pair, dict) else {}
    websites = info.get("websites") if isinstance(info, dict) else []
    if websites and isinstance(websites, list) and websites[0].get("url"):
        keyboard[1].append({"text": "🌐 Website", "url": websites[0]["url"]})

    # Optional social links (Twitter, Telegram, TikTok)
    if project_id == "onelove" or clean_ca == "F1r5AqRj8bJyzM4nUZpVBH1JQT8ToR4Rvjj2YwxHmoon":
        keyboard.append([
            {"text": "🐦 Twitter", "url": "https://x.com/thecaptrobbie?s=11"},
            {"text": "✈️ Telegram", "url": "https://t.me/ONELOVECoinCrew"},
            {"text": "🎵 TikTok", "url": "https://www.tiktok.com/@captain.robbie"},
        ])

    return keyboard


def format_token_intel_response(intel: Dict[str, Any]) -> str:
    """Format token intelligence into a strict, brutal, data-only report without conversational wrapping."""
    if not intel.get("found", True) or intel.get("error"):
        ca_err = intel.get("ca", "Unknown")
        return f"🪙 Unknown Token · N/A\nCA: {ca_err}\n💰 Price: N/A\n🌐 Market Cap: N/A\n💧 Liquidity: N/A\n📊 24h Volume: N/A"

    name = intel.get("name") or "Unknown"
    symbol = intel.get("symbol")
    token_display = f"{name} ({symbol})" if symbol and symbol not in name else name

    def _fmt_usd(val: Any) -> str:
        if val is None or val == "" or str(val).upper() == "N/A":
            return "N/A"
        s = str(val).strip()
        if s.startswith("$"):
            s = s[1:]
        try:
            f = float(s.replace(",", ""))
            if 0 < f < 1:
                return f"{f:,.6f}".rstrip("0").rstrip(".")
            return f"{f:,.2f}"
        except Exception:
            return s

    raw_price = _fmt_usd(intel.get("price"))
    raw_mcap = _fmt_usd(intel.get("market_cap") or intel.get("fdv"))
    raw_liq = _fmt_usd(intel.get("liquidity"))
    raw_vol = _fmt_usd(intel.get("volume_24h"))
    ca_str = intel.get("ca") or "N/A"

    # Chain & Risk Analysis
    chain = "SOLANA"
    if isinstance(intel.get("raw_pair"), dict):
        chain = str(intel["raw_pair"].get("chainId") or "SOLANA").upper()
    elif ca_str and ca_str.startswith("0x"):
        chain = "ETHEREUM"

    header_line = f"🪙 {token_display} · {chain}"

    price_line = f"💰 Price: ${raw_price}" if raw_price != "N/A" else "💰 Price: N/A"
    mcap_line = f"🌐 Market Cap: ${raw_mcap}" if raw_mcap != "N/A" else "🌐 Market Cap: N/A"
    liq_line = f"💧 Liquidity: ${raw_liq}" if raw_liq != "N/A" else "💧 Liquidity: N/A"
    vol_line = f"📊 24h Volume: ${raw_vol}" if raw_vol != "N/A" else "📊 24h Volume: N/A"

    lines = [
        header_line,
        f"CA: {ca_str}",
        price_line,
        mcap_line,
        liq_line,
        vol_line,
    ]
    return "\n".join(lines).strip()

