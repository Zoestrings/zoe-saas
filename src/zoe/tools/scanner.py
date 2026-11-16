"""Solana & EVM Token Intelligence Scanner (Mega-Module 1: Holder & LP Intelligence).

Provides deterministic on-chain and market intelligence:
- Top 10 Holder Concentration
- Liquidity Pool (LP) Lock & Burn Verification
- Developer / Deployer Wallet Holding Analysis
- Mint & Freeze Authority Checks
- Evidence-based Deterministic Risk Evaluation
"""

import asyncio
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional
import httpx

from zoe.utils.logging import get_logger

logger = get_logger("zoe.tools.scanner")

# Base58 character set for Solana contract addresses (length 32 to 44)
SOLANA_CA_REGEX = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
# EVM address pattern
EVM_CA_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")


def is_valid_solana_ca(ca: str) -> bool:
    """Validate whether a string matches standard Solana base58 public key format."""
    if not ca or not isinstance(ca, str):
        return False
    clean = ca.strip()
    return bool(SOLANA_CA_REGEX.match(clean))


def is_valid_evm_ca(ca: str) -> bool:
    """Validate whether a string matches standard EVM 0x contract address format."""
    if not ca or not isinstance(ca, str):
        return False
    return bool(EVM_CA_REGEX.match(ca.strip()))


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
        "chain_id": None,
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
                # Prefer Solana pair if CA matches Solana, or highest liquidity pair
                solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
                target_pairs = solana_pairs if solana_pairs else pairs
                sorted_pairs = sorted(
                    target_pairs,
                    key=lambda p: float(p.get("liquidity", {}).get("usd") or 0.0) if isinstance(p.get("liquidity"), dict) else 0.0,
                    reverse=True,
                )
                top_pair = sorted_pairs[0]
                result["found"] = True
                result["chain_id"] = top_pair.get("chainId")
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
                result["info"] = top_pair.get("info") or {}
    except Exception as exc:
        logger.warning("DexScreener fetch error for %s: %s", ca, exc)

    return result


async def fetch_goplus_solana_security(
    ca: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Fetch on-chain security metrics from GoPlus Solana API with LP and creator extraction."""
    url = f"https://api.gopluslabs.io/api/v1/solana/token_security?contract_addresses={ca}"
    result: Dict[str, Any] = {
        "success": False,
        "mint_revoked": None,
        "freeze_revoked": None,
        "top_10_holders_percent": None,
        "holder_count": None,
        "is_honeypot": False,
        "lp_locked": False,
        "lp_lock_percent": 0.0,
        "creator_address": None,
        "dev_wallet_percent": 0.0,
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

                # 1. Mint authority: '0' = revoked, '1' = active
                mintable_info = token_data.get("mintable", {})
                if isinstance(mintable_info, dict):
                    status = str(mintable_info.get("status", ""))
                    result["mint_revoked"] = (status == "0")

                # 2. Freeze authority: '0' = revoked, '1' = active
                freezable_info = token_data.get("freezable", {})
                if isinstance(freezable_info, dict):
                    status = str(freezable_info.get("status", ""))
                    result["freeze_revoked"] = (status == "0")

                # 3. Honeypot check
                if str(token_data.get("non_transferable", "0")) == "1":
                    result["is_honeypot"] = True

                # 4. Creator / Deployer Address
                creators = token_data.get("creators") or []
                creator_addr = None
                if isinstance(creators, list) and creators:
                    c0 = creators[0]
                    creator_addr = c0.get("address") if isinstance(c0, dict) else str(c0)
                if not creator_addr:
                    mut_auth = token_data.get("metadata_mutable", {}).get("metadata_upgrade_authority", [])
                    if isinstance(mut_auth, list) and mut_auth:
                        creator_addr = mut_auth[0].get("address")
                result["creator_address"] = creator_addr

                # 5. Holders Analysis & Dev Wallet Balance
                holders = token_data.get("holders") or []
                if isinstance(holders, list) and holders:
                    top_10 = holders[:10]
                    total_pct = 0.0
                    for h in top_10:
                        try:
                            pct_val = float(h.get("percent", 0.0))
                            total_pct += (pct_val * 100.0) if pct_val <= 1.0 else pct_val
                        except (ValueError, TypeError):
                            pass
                    result["top_10_holders_percent"] = round(total_pct, 2)

                    # Check creator holding
                    if creator_addr:
                        dev_holder = next(
                            (h for h in holders if h.get("account") == creator_addr),
                            None
                        )
                        if dev_holder:
                            p = float(dev_holder.get("percent", 0.0))
                            result["dev_wallet_percent"] = round((p * 100.0) if p <= 1.0 else p, 2)

                try:
                    result["holder_count"] = int(token_data.get("holder_count", 0))
                except (ValueError, TypeError):
                    result["holder_count"] = None

                # 6. LP Lock Analysis
                dex_pools = token_data.get("dex") or []
                max_burn = 0.0
                for pool in dex_pools:
                    b_pct = pool.get("burn_percent")
                    if b_pct is not None:
                        try:
                            val = float(b_pct)
                            if val > max_burn:
                                max_burn = val
                        except (ValueError, TypeError):
                            pass

                result["lp_lock_percent"] = round(max_burn, 2)
                # Consider locked if >= 70% of pool is burned or LP tokens renounced
                result["lp_locked"] = (max_burn >= 70.0)

    except Exception as exc:
        logger.warning("GoPlus fetch error for %s: %s", ca, exc)

    return result


async def fetch_rugcheck_fallback(
    ca: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Fallback security check using RugCheck API with LP and creator data."""
    url = f"https://api.rugcheck.xyz/v1/tokens/{ca}/report"
    result: Dict[str, Any] = {
        "success": False,
        "mint_revoked": None,
        "freeze_revoked": None,
        "top_10_holders_percent": None,
        "lp_locked": False,
        "lp_lock_percent": 0.0,
        "creator_address": None,
        "dev_wallet_percent": 0.0,
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
                token_data = data.get("token", {})

                result["mint_revoked"] = (token_data.get("mintAuthority") is None)
                result["freeze_revoked"] = (token_data.get("freezeAuthority") is None)

                # Creator
                creator_addr = data.get("creator")
                result["creator_address"] = creator_addr

                # Top Holders & Dev Wallet
                top_holders = data.get("topHolders") or []
                if isinstance(top_holders, list) and top_holders:
                    top_10 = top_holders[:10]
                    total_pct = sum(float(h.get("pct", 0.0)) for h in top_10 if "pct" in h)
                    result["top_10_holders_percent"] = round(total_pct, 2)

                    if creator_addr:
                        dev_h = next((h for h in top_holders if h.get("address") == creator_addr), None)
                        if dev_h and "pct" in dev_h:
                            result["dev_wallet_percent"] = round(float(dev_h["pct"]), 2)

                # LP Lock Check
                markets = data.get("markets") or []
                if markets and isinstance(markets[0], dict):
                    m0 = markets[0]
                    lp_info = m0.get("lp", {})
                    if isinstance(lp_info, dict):
                        lp_locked_pct = float(lp_info.get("lpLockedPct") or 0.0)
                        result["lp_lock_percent"] = round(lp_locked_pct, 2)
                        result["lp_locked"] = (lp_locked_pct >= 70.0)
                        
                # Check risks for LP unlock mention
                risks = data.get("risks") or []
                for r in risks:
                    r_name = str(r.get("name", "")).lower()
                    if "lp not locked" in r_name or "unlocked lp" in r_name:
                        result["lp_locked"] = False
                    elif "copycat" in r_name or "honeypot" in r_name:
                        result["is_honeypot"] = True

    except Exception as exc:
        logger.debug("RugCheck fallback fetch error for %s: %s", ca, exc)

    return result


async def investigate_project_osint(
    token_name: str,
    symbol: Optional[str] = None,
    market_info: Optional[Dict[str, Any]] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Execute Project & Founder OSINT intelligence investigation (Mega-Module 2).
    
    Searches official web presence, scrapes homepage for social links,
    and identifies public founders/executives via search queries.
    """
    clean_name = (token_name or "").strip()
    if clean_name.lower() in ("unknown token", "unknown", "n/a", ""):
        return {
            "website": "Unknown",
            "founder": "Unverified",
            "socials": {},
            "has_official_website": False,
            "twitter": None,
            "telegram": None,
            "discord": None,
            "github": None,
            "linkedin": None,
            "is_anonymous_founder": True,
            "evidence_sources": [],
        }

    evidence: List[str] = []
    website_url: Optional[str] = None
    twitter_url: Optional[str] = None
    telegram_url: Optional[str] = None
    discord_url: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    founder_name: Optional[str] = None

    # 1. Parse DexScreener verified info if available
    if market_info and isinstance(market_info, dict):
        websites = market_info.get("websites") or []
        for w in websites:
            if isinstance(w, dict) and w.get("url"):
                website_url = w["url"]
                evidence.append("DexScreener Official Registry")
                break
        socials = market_info.get("socials") or []
        for s in socials:
            if isinstance(s, dict) and s.get("url"):
                stype = (s.get("type") or "").lower()
                surl = s["url"]
                if "twitter" in stype or "x.com" in surl or "twitter.com" in surl:
                    twitter_url = twitter_url or surl
                elif "telegram" in stype or "t.me" in surl:
                    telegram_url = telegram_url or surl
                elif "discord" in stype:
                    discord_url = discord_url or surl
                elif "linkedin" in stype or "linkedin.com" in surl:
                    linkedin_url = linkedin_url or surl

    # 2. Search DuckDuckGo for Official Website if missing
    from zoe.tools.web_search import search_web
    if not website_url:
        search_query = f"{clean_name} official website"
        try:
            web_results = await search_web(search_query, max_results=3)
            for res in web_results:
                href = res.get("href") or ""
                # Filter out aggregators / social platforms
                if href and not any(skip in href.lower() for skip in (
                    "dexscreener.com", "dextools.io", "coingecko.com", "coinmarketcap.com",
                    "twitter.com", "x.com", "youtube.com", "t.me", "medium.com", "reddit.com"
                )):
                    website_url = href
                    evidence.append(f"DuckDuckGo Search: '{search_query}'")
                    break
        except Exception as exc:
            logger.debug("OSINT website search failed: %s", exc)

    # 3. Scrape website homepage for social links if present
    if website_url:
        try:
            async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as scrape_client:
                resp = await scrape_client.get(
                    website_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                if resp.status_code == 200:
                    html_content = resp.text
                    evidence.append(f"Homepage Scrape: {website_url}")

                    # Regex patterns for social links
                    if not twitter_url:
                        tw_match = re.search(r'https?://(?:www\.)?(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,50})', html_content)
                        if tw_match and tw_match.group(1).lower() not in ("share", "intent", "home", "search", "status"):
                            twitter_url = tw_match.group(0)

                    if not telegram_url:
                        tg_match = re.search(r'https?://t\.me/([A-Za-z0-9_]{1,50})', html_content)
                        if tg_match and tg_match.group(1).lower() not in ("share", "joinchat"):
                            telegram_url = tg_match.group(0)

                    if not discord_url:
                        dc_match = re.search(r'https?://discord\.(?:gg|com/invite)/[A-Za-z0-9_-]+', html_content)
                        if dc_match:
                            discord_url = dc_match.group(0)

                    if not github_url:
                        gh_match = re.search(r'https?://github\.com/([A-Za-z0-9_-]{1,50})', html_content)
                        if gh_match and gh_match.group(1).lower() not in ("features", "pricing", "enterprise", "site"):
                            github_url = gh_match.group(0)

                    if not linkedin_url:
                        li_match = re.search(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[A-Za-z0-9_-]+', html_content)
                        if li_match:
                            linkedin_url = li_match.group(0)
        except Exception as exc:
            logger.debug("OSINT website scraping error for %s: %s", website_url, exc)

    # 4. Search DuckDuckGo for Founder / CEO
    founder_query = f"{clean_name} crypto founder CEO"
    snippets_collected: List[str] = []
    try:
        founder_results = await search_web(founder_query, max_results=4)
        if founder_results:
            evidence.append(f"DuckDuckGo Search: '{founder_query}'")
            for fr in founder_results:
                title = fr.get("title") or ""
                body = fr.get("body") or ""
                snippets_collected.append(f"{title} - {body}")
    except Exception as exc:
        logger.debug("OSINT founder search failed: %s", exc)

    # 5. Parse founder name
    founder_patterns = [
        r'(?:co-founder|founder|creator|ceo)\s+(?:of\s+[A-Za-z0-9_\s]+\s+)?(?:is\s+|:\s+)?([A-Z][a-zA-Z0-9_\s]{1,25})',
        r'([A-Z][a-zA-Z0-9_\s]{1,20})\s+(?:is\s+the\s+)?(?:co-founder|founder|creator|ceo)\b',
        r'(?:founded|created)\s+by\s+([A-Z][a-zA-Z0-9_\s]{1,25})',
    ]
    stopwords = {"the", "a", "an", "this", "solana", "crypto", "coin", "token", "many", "everything", "popular", "meme", "here", "read", "how", "what", "who", "when"}
    for text in snippets_collected:
        for pat in founder_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                cand = m.group(1).strip()
                if cand.lower() not in stopwords and len(cand) >= 2:
                    founder_name = cand
                    break
        if founder_name:
            break

    is_anon = not bool(founder_name)
    display_founder = founder_name if founder_name else "Unverified"

    socials_dict: Dict[str, str] = {}
    if twitter_url:
        socials_dict["twitter"] = twitter_url
    if telegram_url:
        socials_dict["telegram"] = telegram_url
    if discord_url:
        socials_dict["discord"] = discord_url
    if github_url:
        socials_dict["github"] = github_url
    if linkedin_url:
        socials_dict["linkedin"] = linkedin_url

    return {
        "website": website_url if website_url else "Unknown",
        "founder": display_founder,
        "socials": socials_dict,
        "has_official_website": bool(website_url),
        "twitter": twitter_url,
        "telegram": telegram_url,
        "discord": discord_url,
        "github": github_url,
        "linkedin": linkedin_url,
        "is_anonymous_founder": is_anon,
        "evidence_sources": list(dict.fromkeys(evidence)),
    }


def evaluate_risk(
    market: Dict[str, Any],
    security: Dict[str, Any],
    osint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Upgraded Risk Assessment Engine for Mega-Module 1 & 2.
    
    Deterministic Rules:
    - If Honeypot -> CRITICAL
    - If Top 10 Holders > 80% -> CRITICAL
    - If Dev Wallet holds > 10% -> HIGH
    - If LP is NOT locked/renounced -> HIGH
    - If Mint Authority active -> HIGH
    - If Freeze Authority active -> HIGH
    - If No website found -> MEDIUM ("No official website found.")
    - If Founder anonymous -> UNKNOWN/INFO ("Founder identity is unverified.")
    - If LP is locked and Top 10 < 40% (and mint revoked, freeze revoked, dev <= 5%) -> LOW
    """
    if not market.get("found") and not security.get("success"):
        return {
            "level": "UNKNOWN",
            "reasons": ["Token data not found on decentralized exchanges or security registries."],
            "critical_count": 0,
            "high_count": 0,
        }

    critical_reasons: List[str] = []
    high_reasons: List[str] = []
    medium_reasons: List[str] = []
    low_reasons: List[str] = []
    unknown_reasons: List[str] = []

    mint_revoked = security.get("mint_revoked")
    freeze_revoked = security.get("freeze_revoked")
    top_10_pct = security.get("top_10_holders_percent")
    liq_usd = market.get("liquidity_usd")
    is_honeypot = security.get("is_honeypot", False)
    lp_locked = security.get("lp_locked", False)
    lp_lock_pct = security.get("lp_lock_percent", 0.0)
    dev_pct = security.get("dev_wallet_percent", 0.0)

    # 1. Honeypot Check
    if is_honeypot:
        critical_reasons.append("Honeypot risk: token transfers are restricted or blocked")

    # 2. Holder Concentration Check
    # Rule: Top 10 Holders > 80% -> CRITICAL
    if top_10_pct is not None:
        if top_10_pct > 80.0:
            critical_reasons.append(f"Extreme holder concentration: Top 10 hold {top_10_pct:.1f}% (>80% threshold)")
        elif top_10_pct > 50.0:
            medium_reasons.append(f"Moderate holder concentration: Top 10 hold {top_10_pct:.1f}%")
        elif top_10_pct < 40.0:
            low_reasons.append(f"Healthy holder distribution: Top 10 hold {top_10_pct:.1f}% (<40%)")
        else:
            low_reasons.append(f"Acceptable holder distribution: Top 10 hold {top_10_pct:.1f}%")

    # 3. Developer Wallet Check
    # Rule: Dev Wallet holds > 10% -> HIGH
    if dev_pct is not None:
        if dev_pct > 10.0:
            high_reasons.append(f"Developer wallet holds {dev_pct:.1f}% of supply (>10% dump risk)")
        elif dev_pct > 5.0:
            medium_reasons.append(f"Developer wallet holds {dev_pct:.1f}% of supply")
        else:
            low_reasons.append(f"Developer wallet holds {dev_pct:.1f}% (Low risk)")

    # 4. Liquidity Lock Check
    # Rule: If LP is NOT locked/renounced -> HIGH
    if lp_locked:
        pct_tag = f" ({lp_lock_pct:.1f}% burned/locked)" if lp_lock_pct > 0 else ""
        low_reasons.append(f"Liquidity is Locked/Burned{pct_tag} (Safe)")
    else:
        high_reasons.append("Liquidity is NOT locked/renounced - High LP removal/rug risk")

    # 5. Mint Authority Check
    if mint_revoked is False:
        high_reasons.append("Mint Authority is active (owner can inflate supply)")
    elif mint_revoked is True:
        low_reasons.append("Mint Authority is revoked (fixed supply)")

    # 6. Freeze Authority Check
    if freeze_revoked is False:
        high_reasons.append("Freeze Authority is active (owner can freeze token accounts)")
    elif freeze_revoked is True:
        low_reasons.append("Freeze Authority is revoked (accounts cannot be frozen)")

    # 7. DEX Liquidity Check
    if liq_usd is not None:
        if liq_usd < 1_000:
            critical_reasons.append(f"Extremely low liquidity (${format_currency(liq_usd)})")
        elif liq_usd < 5_000:
            high_reasons.append(f"Low liquidity (${format_currency(liq_usd)})")
        elif liq_usd >= 50_000:
            low_reasons.append(f"Strong DEX liquidity (${format_currency(liq_usd)})")

    # 8. Project & Founder OSINT Checks (Mega-Module 2)
    if osint and isinstance(osint, dict):
        has_web = osint.get("has_official_website") or (osint.get("website") and osint.get("website") != "Unknown")
        if not has_web:
            medium_reasons.append("No official website found.")
        elif osint.get("website") and osint.get("website") != "Unknown":
            low_reasons.append(f"Official website verified: {osint.get('website')}")

        is_anon = osint.get("is_anonymous_founder") or (osint.get("founder") in ("Unverified", "Anonymous / Unverified", None))
        if is_anon:
            unknown_reasons.append("Founder identity is unverified.")
        elif osint.get("founder") and osint.get("founder") not in ("Unverified", "Anonymous / Unverified"):
            low_reasons.append(f"Public founder identified: {osint.get('founder')}")

    # Deterministic Risk Hierarchy
    if critical_reasons:
        level = "CRITICAL"
        reasons = critical_reasons + high_reasons + medium_reasons + unknown_reasons
    elif high_reasons:
        level = "HIGH"
        reasons = high_reasons + medium_reasons + unknown_reasons + low_reasons
    elif medium_reasons:
        level = "MEDIUM"
        reasons = medium_reasons + unknown_reasons + low_reasons
    elif unknown_reasons:
        level = "LOW"
        reasons = unknown_reasons + low_reasons
    else:
        # Rule: LP is locked and Top 10 < 40% -> LOW risk
        level = "LOW"
        reasons = low_reasons

    return {
        "level": level,
        "reasons": reasons,
        "critical_count": len(critical_reasons),
        "high_count": len(high_reasons),
    }


async def scan_solana_token(
    ca: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Execute full token investigation scan for Solana and EVM."""
    clean_ca = ca.strip()

    # Format validation
    valid_sol = is_valid_solana_ca(clean_ca)
    valid_evm = is_valid_evm_ca(clean_ca)

    if not valid_sol and not valid_evm:
        return {
            "valid": False,
            "ca": clean_ca,
            "error": "Invalid contract address format. Must be a valid Solana (base58, 32-44 chars) or EVM (0x..., 42 chars) address.",
        }

    chain_type = "Solana" if valid_sol else "EVM"

    # 1. Fetch Market Data (DexScreener)
    market_data = await fetch_dexscreener_market_data(clean_ca, client=client)

    # 2. Fetch Security Data (GoPlus primary, RugCheck fallback)
    security_data = await fetch_goplus_solana_security(clean_ca, client=client)
    if not security_data.get("success") and valid_sol:
        rugcheck_data = await fetch_rugcheck_fallback(clean_ca, client=client)
        if rugcheck_data.get("success"):
            security_data.update(rugcheck_data)

    token_name = market_data.get("name") or "Unknown Token"
    symbol = market_data.get("symbol") or "N/A"

    # 3. Project & Founder OSINT Investigation (Mega-Module 2)
    osint_data: Dict[str, Any] = {
        "has_official_website": False,
        "website": None,
        "twitter": None,
        "telegram": None,
        "discord": None,
        "github": None,
        "founder": "Anonymous / Unverified",
        "is_anonymous_founder": True,
        "evidence_sources": [],
    }
    if market_data.get("found") and token_name != "Unknown Token":
        try:
            osint_data = await investigate_project_osint(
                token_name=token_name,
                symbol=symbol,
                market_info=market_data.get("info"),
                client=client,
            )
        except Exception as exc:
            logger.warning("Project OSINT investigation failed for %s: %s", token_name, exc)

    # 4. Deterministic Risk Assessment (incorporating OSINT flags)
    risk_assessment = evaluate_risk(market_data, security_data, osint=osint_data)

    # Holder Concentration intelligence summary
    top_10 = security_data.get("top_10_holders_percent")
    if top_10 is not None:
        if top_10 < 40.0:
            holder_status = "Healthy"
        elif top_10 <= 80.0:
            holder_status = "Concentrated"
        else:
            holder_status = "Critical Danger"
    else:
        holder_status = "Unknown"

    # LP Lock summary
    lp_locked = security_data.get("lp_locked", False)
    lp_status = "Locked (Safe)" if lp_locked else "Unlocked (Risky)"

    # Dev Wallet summary
    dev_pct = security_data.get("dev_wallet_percent", 0.0)
    dev_status = "High risk" if dev_pct > 10.0 else ("Moderate risk" if dev_pct > 5.0 else "Low risk")

    return {
        "valid": True,
        "ca": clean_ca,
        "ca_short": shorten_ca(clean_ca),
        "chain": chain_type,
        "name": token_name,
        "symbol": symbol,
        "market": market_data,
        "security": security_data,
        "holder_intelligence": {
            "top_10_percent": top_10,
            "holder_count": security_data.get("holder_count"),
            "status": holder_status,
        },
        "lp_intelligence": {
            "is_locked": lp_locked,
            "lock_percent": security_data.get("lp_lock_percent", 0.0),
            "status": lp_status,
        },
        "dev_wallet_intelligence": {
            "creator_address": security_data.get("creator_address"),
            "creator_address_short": shorten_ca(security_data.get("creator_address") or ""),
            "holds_percent": dev_pct,
            "status": dev_status,
        },
        "osint": osint_data,
        "project_osint": osint_data,
        "risk": risk_assessment,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def scan_solana_token_sync(ca: str) -> Dict[str, Any]:
    """Synchronous execution wrapper for scan_solana_token."""
    clean_ca = ca.strip()
    valid_sol = is_valid_solana_ca(clean_ca)
    valid_evm = is_valid_evm_ca(clean_ca)

    if not valid_sol and not valid_evm:
        return {
            "valid": False,
            "ca": clean_ca,
            "error": "Invalid contract address format. Must be a valid Solana (base58, 32-44 chars) or EVM (0x..., 42 chars) address.",
        }

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(asyncio.run, scan_solana_token(clean_ca)).result(timeout=25.0)
        else:
            return asyncio.run(scan_solana_token(clean_ca))
    except Exception as exc:
        logger.warning("scan_solana_token_sync encountered error: %s", exc)
        return asyncio.run(scan_solana_token(clean_ca))


# Aliases for scan functions
scan_token = scan_solana_token
scan_token_sync = scan_solana_token_sync


def format_scan_report(report_data: Dict[str, Any]) -> str:
    """Format investigation results into the upgraded Zoe Intelligence Report string."""
    if not report_data.get("valid", True):
        return f"❌ **Investigation Error**\n\n{report_data.get('error', 'Invalid contract address.')}"

    name = report_data.get("name") or "Unknown Token"
    ca_short = report_data.get("ca_short") or shorten_ca(report_data.get("ca", ""))
    chain = report_data.get("chain") or "Solana"
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
    mint_status = "Revoked" if security.get("mint_revoked") is True else ("Active" if security.get("mint_revoked") is False else "Unknown")
    freeze_status = "Revoked" if security.get("freeze_revoked") is True else ("Active" if security.get("freeze_revoked") is False else "Unknown")

    holder_intel = report_data.get("holder_intelligence", {})
    top_10_pct = holder_intel.get("top_10_percent")
    top_10_str = f"{top_10_pct:.1f}% ({holder_intel.get('status', 'Unknown')})" if top_10_pct is not None else "N/A"

    lp_intel = report_data.get("lp_intelligence", {})
    lp_status_str = lp_intel.get("status", "Unlocked (Risky)")

    dev_intel = report_data.get("dev_wallet_intelligence", {})
    dev_pct_val = dev_intel.get("holds_percent", 0.0)
    dev_str = f"Holds {dev_pct_val:.1f}% ({dev_intel.get('status', 'Low risk')})"

    osint = report_data.get("osint") or report_data.get("project_osint") or {}
    website_str = osint.get("website") or "Unknown"
    twitter_str = osint.get("twitter") or "Unknown"
    founder_str = osint.get("founder") or "Anonymous / Unverified"

    timestamp = report_data.get("timestamp_utc") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Format risk reasons
    reasons_block = "\n".join(f"- {r}" for r in reasons[:3]) if reasons else "- No critical risk flags detected"

    report = (
        f"🔍 Zoe Intelligence Report\n"
        f"**{name}** (CA: {ca_short}) · {chain}\n\n"
        f"🚨 Risk Assessment: {risk_level}\n"
        f"{reasons_block}\n\n"
        f"📊 Market Data\n"
        f"Price: ${price_str}\n"
        f"Market Cap: ${mc_str}\n"
        f"Liquidity: ${liq_str}\n\n"
        f"🛡️ Security & Holder Intelligence\n"
        f"👥 Holder Concentration: Top 10 hold {top_10_str}\n"
        f"🔒 LP Lock: {lp_status_str}\n"
        f"🧑‍💻 Dev Wallet: {dev_str}\n"
        f"Mint Auth: {mint_status}\n"
        f"Freeze Auth: {freeze_status}\n\n"
        f"🌐 Project OSINT\n"
        f"Website: {website_str}\n"
        f"Twitter: {twitter_str}\n"
        f"Founder: {founder_str}\n\n"
        f"Evidence Sources: DexScreener, GoPlus\n"
        f"Timestamp: {timestamp}\n"
        f"(This is a preliminary scan, not financial advice.)"
    )
    return report


def format_contract_report(report_data: Dict[str, Any]) -> str:
    """Format Security & Contract checks (Honeypot, Taxes, Mint/Freeze Auth)."""
    if not report_data.get("valid", True):
        return f"❌ **Investigation Error**\n\n{report_data.get('error', 'Invalid contract address.')}"

    name = report_data.get("name") or "Unknown Token"
    ca_short = report_data.get("ca_short") or shorten_ca(report_data.get("ca", ""))
    chain = report_data.get("chain") or "Solana"
    security = report_data.get("security", {})

    mint_status = "Revoked (Safe)" if security.get("mint_revoked") is True else ("Active (High Risk)" if security.get("mint_revoked") is False else "Unknown")
    freeze_status = "Revoked (Safe)" if security.get("freeze_revoked") is True else ("Active (High Risk)" if security.get("freeze_revoked") is False else "Unknown")
    honeypot_status = "🚨 Honeypot Detected!" if security.get("is_honeypot") else "✅ No Honeypot Detected"

    buy_tax = security.get("buy_tax")
    sell_tax = security.get("sell_tax")
    tax_str = f"{buy_tax}% / {sell_tax}%" if (buy_tax is not None and sell_tax is not None) else "0% / 0% (Standard)"

    risk = report_data.get("risk", {})
    risk_level = risk.get("level", "UNKNOWN")

    return (
        f"🛡️ **Security & Contract Checks: {name}**\n"
        f"CA: `{ca_short}` · {chain}\n\n"
        f"🚨 Risk: {risk_level}\n"
        f"Honeypot: {honeypot_status}\n"
        f"Mint Authority: {mint_status}\n"
        f"Freeze Authority: {freeze_status}\n"
        f"Taxes: {tax_str}\n"
        f"Evidence Sources: GoPlus, RugCheck"
    )


def format_holders_report(report_data: Dict[str, Any]) -> str:
    """Format Holder Concentration and Dev Wallet intelligence."""
    if not report_data.get("valid", True):
        return f"❌ **Investigation Error**\n\n{report_data.get('error', 'Invalid contract address.')}"

    name = report_data.get("name") or "Unknown Token"
    ca_short = report_data.get("ca_short") or shorten_ca(report_data.get("ca", ""))
    chain = report_data.get("chain") or "Solana"
    holder_intel = report_data.get("holder_intelligence", {})
    top_10 = holder_intel.get("top_10_percent")
    top_10_str = f"{top_10:.1f}% ({holder_intel.get('status', 'Unknown')})" if top_10 is not None else "N/A"
    total_holders = holder_intel.get("holder_count")
    total_holders_str = f"{total_holders:,}" if total_holders else "Unknown"

    dev_intel = report_data.get("dev_wallet_intelligence", {})
    dev_pct = dev_intel.get("holds_percent", 0.0)
    dev_str = f"{dev_pct:.1f}% ({dev_intel.get('status', 'Low risk')})"
    creator_addr = dev_intel.get("creator_address_short") or "Not detected"

    return (
        f"👥 **Holder Concentration: {name}**\n"
        f"CA: `{ca_short}` · {chain}\n\n"
        f"Top 10 Holders: {top_10_str}\n"
        f"Total Unique Holders: {total_holders_str}\n"
        f"Developer Holding: {dev_str}\n"
        f"Creator Address: `{creator_addr}`\n"
        f"Evidence Sources: Solana RPC / GoPlus"
    )


def format_liquidity_report(report_data: Dict[str, Any]) -> str:
    """Format Market Data and Liquidity metrics."""
    if not report_data.get("valid", True):
        return f"❌ **Investigation Error**\n\n{report_data.get('error', 'Invalid contract address.')}"

    name = report_data.get("name") or "Unknown Token"
    ca_short = report_data.get("ca_short") or shorten_ca(report_data.get("ca", ""))
    chain = report_data.get("chain") or "Solana"
    market = report_data.get("market", {})
    price_val = market.get("price_usd")
    price_str = format_price(price_val)
    mc_val = market.get("market_cap")
    mc_str = format_currency(mc_val)
    liq_val = market.get("liquidity_usd")
    liq_str = format_currency(liq_val)

    lp_intel = report_data.get("lp_intelligence", {})
    lp_status_str = lp_intel.get("status", "Unlocked (Risky)")
    lp_pct = lp_intel.get("lock_percent", 0.0)
    lp_pct_str = f" ({lp_pct:.1f}% locked/burned)" if lp_pct > 0 else ""

    return (
        f"📊 **Market & Liquidity: {name}**\n"
        f"CA: `{ca_short}` · {chain}\n\n"
        f"Price: ${price_str}\n"
        f"Market Cap: ${mc_str}\n"
        f"Liquidity Pool: ${liq_str}\n"
        f"LP Status: {lp_status_str}{lp_pct_str}\n"
        f"Evidence Sources: DexScreener"
    )


def format_osint_report(report_data: Dict[str, Any]) -> str:
    """Format Project OSINT and Founder Intelligence."""
    if not report_data.get("valid", True):
        return f"❌ **Investigation Error**\n\n{report_data.get('error', 'Invalid contract address.')}"

    name = report_data.get("name") or "Unknown Token"
    ca_short = report_data.get("ca_short") or shorten_ca(report_data.get("ca", ""))
    chain = report_data.get("chain") or "Solana"
    osint = report_data.get("osint") or report_data.get("project_osint") or {}
    website_str = osint.get("website") or "Unknown"
    twitter_str = osint.get("twitter") or "Unknown"
    founder_str = osint.get("founder") or "Unverified"
    sources = osint.get("evidence_sources", [])
    sources_str = ", ".join(sources[:2]) if sources else "DuckDuckGo, DexScreener"

    return (
        f"🌐 **Project OSINT: {name}**\n"
        f"CA: `{ca_short}` · {chain}\n\n"
        f"Website: {website_str}\n"
        f"Twitter: {twitter_str}\n"
        f"Founder: {founder_str}\n"
        f"Evidence Sources: {sources_str}"
    )


def generate_scanner_inline_keyboard(
    ca: str,
    report_data: Optional[Dict[str, Any]] = None,
) -> List[List[Dict[str, str]]]:
    """Generate inline buttons for DexScreener Chart and Blockchain Explorer."""
    clean_ca = ca.strip()
    pair_url = None
    is_sol = is_valid_solana_ca(clean_ca)

    if report_data and isinstance(report_data.get("market"), dict):
        pair_url = report_data["market"].get("pair_url")

    chart_url = pair_url or (f"https://dexscreener.com/solana/{clean_ca}" if is_sol else f"https://dexscreener.com/search?q={clean_ca}")
    explorer_url = f"https://solscan.io/token/{clean_ca}" if is_sol else f"https://etherscan.io/token/{clean_ca}"

    return [
        [
            {"text": "📊 Live Chart", "url": chart_url},
            {"text": "🔍 Explorer", "url": explorer_url},
        ]
    ]
