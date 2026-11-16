"""Solana Token Intelligence Scanner.

Provides deterministic on-chain and market intelligence for Solana tokens,
aggregating DexScreener and GoPlus security checks with evidence-based risk assessment.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional
import httpx

from zoe.utils.logging import get_logger

logger = get_logger("zoe.tools.scanner")

# Base58 character set for Solana contract addresses (length 32 to 44)
SOLANA_CA_REGEX = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def is_valid_solana_ca(ca: str) -> bool:
    """Validate whether a string matches standard Solana base58 public key format."""
    if not ca or not isinstance(ca, str):
        return False
    return bool(SOLANA_CA_REGEX.match(ca.strip()))


def format_currency(value: Optional[float], decimals: int = 2) -> str:
    """Format floating point numbers as human-readable USD."""
    if value is None or value < 0:
        return "N/A"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.2f}K"
    if value < 0.000001:
        return f"{value:.8f}"
    if value < 0.01:
        return f"{value:.6f}"
    return f"{value:,.{decimals}f}"


def format_price(value: Optional[float]) -> str:
    """Format token spot price with precision."""
    if value is None:
        return "N/A"
    if value == 0:
        return "0.00"
    if value < 0.000001:
        return f"{value:.8f}"
    if value < 0.001:
        return f"{value:.6f}"
    if value < 1.0:
        return f"{value:.4f}"
    return f"{value:,.2f}"


def shorten_ca(ca: str) -> str:
    """Return First 4...Last 4 representation of a contract address."""
    clean = ca.strip()
    if len(clean) <= 8:
        return clean
    return f"{clean[:4]}...{clean[-4:]}"


async def fetch_dexscreener_market_data(
    ca: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Fetch live market and trading pair metrics from DexScreener."""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
    result: Dict[str, Any] = {
        "found": False,
        "name": None,
        "symbol": None,
        "price_usd": None,
        "market_cap": None,
        "liquidity_usd": None,
        "volume_24h": None,
        "pair_url": None,
        "pair_created_at": None,
    }

    try:
        if client:
            resp = await client.get(url, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=10.0) as local_client:
                resp = await local_client.get(url)

        if resp.status_code == 200:
            data = resp.json()
            pairs = data.get("pairs") or []
            if pairs:
                # Find the highest liquidity Solana pair
                solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
                target_pairs = solana_pairs if solana_pairs else pairs
                sorted_pairs = sorted(
                    target_pairs,
                    key=lambda p: float(p.get("liquidity", {}).get("usd") or 0.0) if isinstance(p.get("liquidity"), dict) else 0.0,
                    reverse=True,
                )
                top_pair = sorted_pairs[0]
                result["found"] = True
                base = top_pair.get("baseToken", {})
                result["name"] = base.get("name")
                result["symbol"] = base.get("symbol")
                try:
                    result["price_usd"] = float(top_pair.get("priceUsd")) if top_pair.get("priceUsd") is not None else None
                except (ValueError, TypeError):
                    result["price_usd"] = None

                mcap = top_pair.get("marketCap") or top_pair.get("fdv")
                try:
                    result["market_cap"] = float(mcap) if mcap is not None else None
                except (ValueError, TypeError):
                    result["market_cap"] = None

                liq = top_pair.get("liquidity", {})
                if isinstance(liq, dict):
                    try:
                        result["liquidity_usd"] = float(liq.get("usd")) if liq.get("usd") is not None else None
                    except (ValueError, TypeError):
                        result["liquidity_usd"] = None

                vol = top_pair.get("volume", {})
                if isinstance(vol, dict):
                    try:
                        result["volume_24h"] = float(vol.get("h24")) if vol.get("h24") is not None else None
                    except (ValueError, TypeError):
                        result["volume_24h"] = None

                result["pair_url"] = top_pair.get("url")
                result["pair_created_at"] = top_pair.get("pairCreatedAt")
    except Exception as exc:
        logger.warning("DexScreener fetch error for %s: %s", ca, exc)

    return result


async def fetch_goplus_solana_security(
    ca: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Fetch on-chain security metrics from GoPlus Solana API."""
    url = f"https://api.gopluslabs.io/api/v1/solana/token_security?contract_addresses={ca}"
    result: Dict[str, Any] = {
        "success": False,
        "mint_revoked": None,
        "freeze_revoked": None,
        "top_10_holders_percent": None,
        "holder_count": None,
        "is_honeypot": False,
        "source": "GoPlus",
    }

    try:
        if client:
            resp = await client.get(url, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=10.0) as local_client:
                resp = await local_client.get(url)

        if resp.status_code == 200:
            data = resp.json()
            payload = data.get("result", {})
            token_data = payload.get(ca) if isinstance(payload, dict) else None

            if token_data and isinstance(token_data, dict):
                result["success"] = True

                # Mint authority: status '0' means non-mintable (revoked), '1' means mintable (active)
                mintable_info = token_data.get("mintable", {})
                if isinstance(mintable_info, dict):
                    status = str(mintable_info.get("status", ""))
                    result["mint_revoked"] = (status == "0")

                # Freeze authority: status '0' means non-freezable (revoked), '1' means freezable (active)
                freezable_info = token_data.get("freezable", {})
                if isinstance(freezable_info, dict):
                    status = str(freezable_info.get("status", ""))
                    result["freeze_revoked"] = (status == "0")

                # Non-transferable flag
                if str(token_data.get("non_transferable", "0")) == "1":
                    result["is_honeypot"] = True

                # Top 10 Holders concentration
                holders = token_data.get("holders") or []
                if isinstance(holders, list) and holders:
                    top_10 = holders[:10]
                    total_pct = 0.0
                    for h in top_10:
                        try:
                            pct_val = float(h.get("percent", 0.0))
                            # Handle decimal (0.104) vs percentage (10.4)
                            if pct_val <= 1.0:
                                total_pct += pct_val * 100.0
                            else:
                                total_pct += pct_val
                        except (ValueError, TypeError):
                            pass
                    result["top_10_holders_percent"] = round(total_pct, 2)

                try:
                    result["holder_count"] = int(token_data.get("holder_count", 0))
                except (ValueError, TypeError):
                    result["holder_count"] = None

    except Exception as exc:
        logger.warning("GoPlus fetch error for %s: %s", ca, exc)

    return result


async def fetch_rugcheck_fallback(
    ca: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Fallback security check using RugCheck API if GoPlus is unreachable."""
    url = f"https://api.rugcheck.xyz/v1/tokens/{ca}/report"
    result: Dict[str, Any] = {
        "success": False,
        "mint_revoked": None,
        "freeze_revoked": None,
        "top_10_holders_percent": None,
        "source": "RugCheck",
    }
    try:
        if client:
            resp = await client.get(url, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=10.0) as local_client:
                resp = await local_client.get(url)

        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict):
                result["success"] = True
                token_meta = data.get("tokenMeta", {})
                token_data = data.get("token", {})

                # In RugCheck, null authority means revoked
                mint_auth = token_data.get("mintAuthority")
                freeze_auth = token_data.get("freezeAuthority")
                result["mint_revoked"] = (mint_auth is None)
                result["freeze_revoked"] = (freeze_auth is None)

                top_holders = data.get("topHolders") or []
                if isinstance(top_holders, list) and top_holders:
                    top_10 = top_holders[:10]
                    total_pct = sum(float(h.get("pct", 0.0)) for h in top_10 if "pct" in h)
                    result["top_10_holders_percent"] = round(total_pct, 2)
    except Exception as exc:
        logger.debug("RugCheck fallback fetch error for %s: %s", ca, exc)

    return result


def evaluate_risk(
    market: Dict[str, Any],
    security: Dict[str, Any],
) -> Dict[str, Any]:
    """Deterministic Risk Assessment Engine.
    
    Risk Levels: CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN
    """
    reasons: List[str] = []
    risk_score = 0  # 0-10: LOW, 11-30: MEDIUM, 31-60: HIGH, 61+: CRITICAL

    mint_revoked = security.get("mint_revoked")
    freeze_revoked = security.get("freeze_revoked")
    top_10_pct = security.get("top_10_holders_percent")
    liq_usd = market.get("liquidity_usd")
    is_honeypot = security.get("is_honeypot", False)

    # If completely unlisted and no security data
    if not market.get("found") and not security.get("success"):
        return {
            "level": "UNKNOWN",
            "reasons": ["Token data not found on Solana DEXes or security registries."],
        }

    # 1. Honeypot / Transfer Block
    if is_honeypot:
        risk_score += 100
        reasons.append("Honeypot risk: token transfers may be blocked or restricted")

    # 2. Mint Authority
    if mint_revoked is False:
        risk_score += 35
        reasons.append("Mint Authority is active (owner can inflate supply)")
    elif mint_revoked is True:
        reasons.append("Mint Authority is revoked (fixed supply)")
    else:
        reasons.append("Mint Authority status unknown")

    # 3. Freeze Authority
    if freeze_revoked is False:
        risk_score += 35
        reasons.append("Freeze Authority is active (owner can freeze token accounts)")
    elif freeze_revoked is True:
        reasons.append("Freeze Authority is revoked (accounts cannot be frozen)")
    else:
        reasons.append("Freeze Authority status unknown")

    # 4. Top 10 Holder Concentration
    if top_10_pct is not None:
        if top_10_pct > 80.0:
            risk_score += 30
            reasons.append(f"Extreme holder concentration: Top 10 hold {top_10_pct:.1f}%")
        elif top_10_pct > 50.0:
            risk_score += 15
            reasons.append(f"Moderate holder concentration: Top 10 hold {top_10_pct:.1f}%")
        else:
            reasons.append(f"Healthy holder distribution: Top 10 hold {top_10_pct:.1f}%")

    # 5. Liquidity Checks
    if liq_usd is not None:
        if liq_usd < 1_000:
            risk_score += 50
            reasons.append(f"Extremely low liquidity (${format_currency(liq_usd)}) - high slippage/rug risk")
        elif liq_usd < 5_000:
            risk_score += 30
            reasons.append(f"Low liquidity (${format_currency(liq_usd)})")
        elif liq_usd >= 50_000:
            reasons.append(f"Strong DEX liquidity (${format_currency(liq_usd)})")
    else:
        if market.get("found"):
            risk_score += 20
            reasons.append("DEX liquidity pool unindexed or minimal")

    # Deterministic mapping
    if risk_score >= 60:
        level = "CRITICAL"
    elif risk_score >= 30:
        level = "HIGH"
    elif risk_score >= 15:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "level": level,
        "reasons": reasons,
        "risk_score": risk_score,
    }


async def scan_solana_token(
    ca: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Execute full Solana token investigation scan."""
    clean_ca = ca.strip()

    # Format validation
    if not is_valid_solana_ca(clean_ca):
        return {
            "valid": False,
            "ca": clean_ca,
            "error": "Invalid Solana contract address format. Solana CAs must be 32-44 base58 characters.",
        }

    # 1. Fetch Market Data (DexScreener)
    market_data = await fetch_dexscreener_market_data(clean_ca, client=client)

    # 2. Fetch Security Data (GoPlus primary, RugCheck fallback)
    security_data = await fetch_goplus_solana_security(clean_ca, client=client)
    if not security_data.get("success"):
        rugcheck_data = await fetch_rugcheck_fallback(clean_ca, client=client)
        if rugcheck_data.get("success"):
            security_data.update(rugcheck_data)

    # 3. Deterministic Risk Assessment
    risk_assessment = evaluate_risk(market_data, security_data)

    token_name = market_data.get("name") or "Unknown Token"
    symbol = market_data.get("symbol") or "N/A"

    return {
        "valid": True,
        "ca": clean_ca,
        "ca_short": shorten_ca(clean_ca),
        "name": token_name,
        "symbol": symbol,
        "market": market_data,
        "security": security_data,
        "risk": risk_assessment,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def scan_solana_token_sync(ca: str) -> Dict[str, Any]:
    """Synchronous execution wrapper for scan_solana_token."""
    clean_ca = ca.strip()
    if not is_valid_solana_ca(clean_ca):
        return {
            "valid": False,
            "ca": clean_ca,
            "error": "Invalid Solana contract address format. Solana CAs must be 32-44 base58 characters.",
        }

    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        # 1. DexScreener
        url_dex = f"https://api.dexscreener.com/latest/dex/tokens/{clean_ca}"
        market_data: Dict[str, Any] = {
            "found": False,
            "name": None,
            "symbol": None,
            "price_usd": None,
            "market_cap": None,
            "liquidity_usd": None,
            "volume_24h": None,
            "pair_url": None,
            "pair_created_at": None,
        }
        try:
            r = client.get(url_dex)
            if r.status_code == 200:
                data = r.json()
                pairs = data.get("pairs") or []
                if pairs:
                    solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
                    target_pairs = solana_pairs if solana_pairs else pairs
                    sorted_pairs = sorted(
                        target_pairs,
                        key=lambda p: float(p.get("liquidity", {}).get("usd") or 0.0) if isinstance(p.get("liquidity"), dict) else 0.0,
                        reverse=True,
                    )
                    top_pair = sorted_pairs[0]
                    market_data["found"] = True
                    base = top_pair.get("baseToken", {})
                    market_data["name"] = base.get("name")
                    market_data["symbol"] = base.get("symbol")
                    try:
                        market_data["price_usd"] = float(top_pair.get("priceUsd")) if top_pair.get("priceUsd") is not None else None
                    except (ValueError, TypeError):
                        pass
                    mcap = top_pair.get("marketCap") or top_pair.get("fdv")
                    try:
                        market_data["market_cap"] = float(mcap) if mcap is not None else None
                    except (ValueError, TypeError):
                        pass
                    liq = top_pair.get("liquidity", {})
                    if isinstance(liq, dict):
                        try:
                            market_data["liquidity_usd"] = float(liq.get("usd")) if liq.get("usd") is not None else None
                        except (ValueError, TypeError):
                            pass
                    vol = top_pair.get("volume", {})
                    if isinstance(vol, dict):
                        try:
                            market_data["volume_24h"] = float(vol.get("h24")) if vol.get("h24") is not None else None
                        except (ValueError, TypeError):
                            pass
                    market_data["pair_url"] = top_pair.get("url")
                    market_data["pair_created_at"] = top_pair.get("pairCreatedAt")
        except Exception as exc:
            logger.warning("Sync DexScreener error for %s: %s", clean_ca, exc)

        # 2. GoPlus Solana Security
        url_goplus = f"https://api.gopluslabs.io/api/v1/solana/token_security?contract_addresses={clean_ca}"
        security_data: Dict[str, Any] = {
            "success": False,
            "mint_revoked": None,
            "freeze_revoked": None,
            "top_10_holders_percent": None,
            "holder_count": None,
            "is_honeypot": False,
            "source": "GoPlus",
        }
        try:
            r2 = client.get(url_goplus)
            if r2.status_code == 200:
                data2 = r2.json()
                res2 = data2.get("result", {})
                token_data = res2.get(clean_ca) if isinstance(res2, dict) else None
                if token_data and isinstance(token_data, dict):
                    security_data["success"] = True
                    mint_info = token_data.get("mintable", {})
                    if isinstance(mint_info, dict):
                        security_data["mint_revoked"] = (str(mint_info.get("status", "")) == "0")

                    freeze_info = token_data.get("freezable", {})
                    if isinstance(freeze_info, dict):
                        security_data["freeze_revoked"] = (str(freeze_info.get("status", "")) == "0")

                    if str(token_data.get("non_transferable", "0")) == "1":
                        security_data["is_honeypot"] = True

                    holders = token_data.get("holders") or []
                    if isinstance(holders, list) and holders:
                        top_10 = holders[:10]
                        total_pct = 0.0
                        for h in top_10:
                            try:
                                p_val = float(h.get("percent", 0.0))
                                total_pct += (p_val * 100.0) if p_val <= 1.0 else p_val
                            except (ValueError, TypeError):
                                pass
                        security_data["top_10_holders_percent"] = round(total_pct, 2)
                    try:
                        security_data["holder_count"] = int(token_data.get("holder_count", 0))
                    except (ValueError, TypeError):
                        pass
        except Exception as exc:
            logger.warning("Sync GoPlus error for %s: %s", clean_ca, exc)

        # Fallback to RugCheck if GoPlus failed
        if not security_data.get("success"):
            try:
                url_rc = f"https://api.rugcheck.xyz/v1/tokens/{clean_ca}/report"
                r3 = client.get(url_rc)
                if r3.status_code == 200:
                    d3 = r3.json()
                    if isinstance(d3, dict):
                        security_data["success"] = True
                        security_data["source"] = "RugCheck"
                        tok = d3.get("token", {})
                        security_data["mint_revoked"] = (tok.get("mintAuthority") is None)
                        security_data["freeze_revoked"] = (tok.get("freezeAuthority") is None)
                        th = d3.get("topHolders") or []
                        if isinstance(th, list) and th:
                            top_10_rc = th[:10]
                            total_rc = sum(float(h.get("pct", 0.0)) for h in top_10_rc if "pct" in h)
                            security_data["top_10_holders_percent"] = round(total_rc, 2)
            except Exception as exc:
                logger.debug("Sync RugCheck fallback error: %s", exc)

        # 3. Risk Evaluation
        risk = evaluate_risk(market_data, security_data)
        token_name = market_data.get("name") or "Unknown Token"
        symbol = market_data.get("symbol") or "N/A"

        return {
            "valid": True,
            "ca": clean_ca,
            "ca_short": shorten_ca(clean_ca),
            "name": token_name,
            "symbol": symbol,
            "market": market_data,
            "security": security_data,
            "risk": risk,
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }


def format_scan_report(report_data: Dict[str, Any]) -> str:
    """Format investigation results into the required Zoe Intelligence Report string."""
    if not report_data.get("valid", True):
        return f"❌ **Investigation Error**\n\n{report_data.get('error', 'Invalid contract address.')}"

    name = report_data.get("name") or "Unknown Token"
    ca_short = report_data.get("ca_short") or shorten_ca(report_data.get("ca", ""))
    risk = report_data.get("risk", {})
    risk_level = risk.get("level", "UNKNOWN")
    reasons = risk.get("reasons", [])

    market = report_data.get("market", {})
    price_val = market.get("price_usd")
    price_str = format_price(price_val)
    mc_val = market.get("market_cap")
    mc_str = format_currency(mc_val)
    liq_val = market.get("liquidity_usd")
    liq_str = format_currency(liq_val)

    security = report_data.get("security", {})
    mint_rev = security.get("mint_revoked")
    if mint_rev is True:
        mint_status = "Revoked"
    elif mint_rev is False:
        mint_status = "Active"
    else:
        mint_status = "Unknown"

    freeze_rev = security.get("freeze_revoked")
    if freeze_rev is True:
        freeze_status = "Revoked"
    elif freeze_rev is False:
        freeze_status = "Active"
    else:
        freeze_status = "Unknown"

    top_10_pct = security.get("top_10_holders_percent")
    top_10_str = f"{top_10_pct:.1f}%" if top_10_pct is not None else "N/A"

    timestamp = report_data.get("timestamp_utc") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Format risk reasons
    reasons_block = "\n".join(f"- {r}" for r in reasons[:3]) if reasons else "- No critical risk flags detected"

    report = (
        f"🔍 Zoe Intelligence Report\n"
        f"**{name}** (CA: {ca_short}) · Solana\n\n"
        f"🚨 Risk Assessment: {risk_level}\n"
        f"{reasons_block}\n\n"
        f"📊 Market Data\n"
        f"Price: ${price_str}\n"
        f"Market Cap: ${mc_str}\n"
        f"Liquidity: ${liq_str}\n\n"
        f"🛡️ Security Checks\n"
        f"Mint Auth: {mint_status}\n"
        f"Freeze Auth: {freeze_status}\n"
        f"Top 10 Holders: {top_10_str}\n\n"
        f"Evidence Sources: DexScreener, GoPlus\n"
        f"Timestamp: {timestamp}\n"
        f"(This is a preliminary scan, not financial advice.)"
    )
    return report


def generate_scanner_inline_keyboard(
    ca: str,
    report_data: Optional[Dict[str, Any]] = None,
) -> List[List[Dict[str, str]]]:
    """Generate inline buttons for DexScreener Chart and Solscan Explorer."""
    clean_ca = ca.strip()
    pair_url = None
    if report_data and isinstance(report_data.get("market"), dict):
        pair_url = report_data["market"].get("pair_url")

    chart_url = pair_url or f"https://dexscreener.com/solana/{clean_ca}"
    solscan_url = f"https://solscan.io/token/{clean_ca}"

    return [
        [
            {"text": "📊 Live Chart", "url": chart_url},
            {"text": "🔍 Solscan Explorer", "url": solscan_url},
        ]
    ]

