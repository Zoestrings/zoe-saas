"""Pre-Trade Intelligence Brief Tool for Zoe Trading Terminal (Pillar 2).

Combines live DexScreener market/liquidity metrics, GoPlus/RugCheck holder
concentration, and Crypto Twitter (X) sentiment into a factual 3-bullet
pre-trade research brief without providing financial advice.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from zoe.llm.factory import get_llm_client
from zoe.tools.dexscreener import get_token_price
from zoe.tools.scanner import scan_token
from zoe.tools.x_intel import analyze_x_sentiment

logger = logging.getLogger("zoe.tools.trading_intel")

DISCLAIMER = "This is AI-generated research, not financial advice."


async def generate_trade_brief(ca: str) -> Dict[str, Any]:
    """Generate an objective 3-bullet Pre-Trade Intelligence Brief for a contract address."""
    clean_ca = (ca or "").strip()
    if not clean_ca:
        return {
            "contract_address": clean_ca,
            "bullets": [
                "Market Health: No contract address provided.",
                "Sentiment: Unavailable without a target token.",
                "Risk Warning: Always verify the exact contract address before interacting with any pool.",
            ],
            "brief_text": "Invalid contract address.",
            "disclaimer": DISCLAIMER,
        }

    # 1. Fetch Market, Security/Holders, and X Sentiment concurrently
    async def _fetch_scan() -> Dict[str, Any]:
        try:
            return await scan_token(clean_ca)
        except Exception as exc:
            logger.warning("Token scan failed in trading_intel for %s: %s", clean_ca, exc)
            return {}

    async def _fetch_dex() -> str:
        try:
            return await get_token_price(clean_ca)
        except Exception as exc:
            logger.warning("DexScreener fetch failed in trading_intel for %s: %s", clean_ca, exc)
            return "Price and liquidity telemetry unavailable."

    scan_data, dex_summary = await asyncio.gather(_fetch_scan(), _fetch_dex())

    market = scan_data.get("market") or {}
    security = scan_data.get("security") or {}
    token_name = scan_data.get("name") or market.get("name") or "Unknown Token"
    token_symbol = scan_data.get("symbol") or market.get("symbol") or clean_ca[:8]

    price_usd = market.get("price_usd")
    liquidity_usd = market.get("liquidity_usd")
    market_cap = market.get("market_cap")
    top10_pct = security.get("top_10_holders_percent")
    is_honeypot = security.get("is_honeypot")
    mint_revoked = security.get("mint_revoked")
    lp_locked = security.get("lp_locked")

    # Fetch X sentiment using token symbol/name
    x_query = f"{token_symbol} {token_name}".strip()
    try:
        x_intel = await analyze_x_sentiment(x_query, max_tweets=8)
    except Exception as exc:
        logger.warning("X sentiment failed in trading_intel for %s: %s", x_query, exc)
        x_intel = {"sentiment": "Neutral", "summary": "No recent X/Twitter discussion indexed."}

    x_sentiment = x_intel.get("sentiment", "Neutral")
    x_summary = x_intel.get("summary", "No recent X/Twitter discussion indexed.")

    # 2. Synthesize 3-bullet factual brief via LLM
    system_prompt = (
        "You are a Web3 Trading Research Analyst. Based on this data, write a 3-bullet objective brief. "
        "Bullet 1: Market Health (Liquidity/Holders). "
        "Bullet 2: Sentiment (X/Twitter). "
        "Bullet 3: Risk Warning. "
        "Do not tell the user to buy or sell. Keep it factual."
    )
    user_prompt = (
        f"TOKEN: {token_name} ({token_symbol})\n"
        f"CONTRACT ADDRESS: {clean_ca}\n"
        f"PRICE USD: {price_usd}\n"
        f"LIQUIDITY USD: {liquidity_usd}\n"
        f"MARKET CAP: {market_cap}\n"
        f"TOP 10 HOLDERS %: {top10_pct}\n"
        f"HONEYPOT DETECTED: {is_honeypot}\n"
        f"MINT REVOKED: {mint_revoked}\n"
        f"LP LOCKED: {lp_locked}\n"
        f"DEXSCREENER RAW: {dex_summary}\n"
        f"X SENTIMENT ({x_sentiment}): {x_summary}\n"
    )

    bullets: List[str] = []
    brief_text = ""

    try:
        llm = get_llm_client("default")
        if getattr(llm, "name", "") != "mock":
            raw_resp = await asyncio.to_thread(
                llm.generate,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=380,
            )
            if raw_resp and len(raw_resp.strip()) > 40:
                brief_text = raw_resp.strip()
                parsed_lines = [
                    line.lstrip("•*-1234567890. ").strip()
                    for line in brief_text.splitlines()
                    if line.strip() and (line.strip().startswith(("-", "*", "•", "1.", "2.", "3.")) or "Bullet" in line)
                ]
                if len(parsed_lines) >= 3:
                    bullets = parsed_lines[:3]
    except Exception as exc:
        logger.warning("LLM synthesis failed in trading_intel, using deterministic brief: %s", exc)

    # Deterministic factual fallback if LLM is unconfigured or response wasn't 3 bullets
    if len(bullets) < 3:
        liq_str = f"${float(liquidity_usd):,.2f}" if liquidity_usd is not None else "Unavailable"
        price_str = f"${float(price_usd):.6f}" if price_usd is not None else "Unavailable"
        holders_str = f"{float(top10_pct):.1f}%" if top10_pct is not None else "Unavailable"
        lp_str = "Locked" if lp_locked else ("Unlocked / Unverified" if lp_locked is False else "Unknown")

        risk_notes: List[str] = []
        if is_honeypot:
            risk_notes.append("Honeypot mechanics flagged by security scanner")
        if mint_revoked is False:
            risk_notes.append("Mint authority remains active")
        if top10_pct is not None and float(top10_pct) > 35.0:
            risk_notes.append(f"High top-10 holder concentration ({float(top10_pct):.1f}%)")
        if liquidity_usd is not None and float(liquidity_usd) < 25000:
            risk_notes.append(f"Thin liquidity depth (${float(liquidity_usd):,.0f})")
        if not risk_notes:
            risk_notes.append("Standard on-chain volatility, slippage, and smart-contract execution risks apply")

        bullets = [
            f"Market Health (Liquidity/Holders): {token_symbol} is trading at {price_str} with {liq_str} in pool liquidity (LP: {lp_str}) and top-10 holder concentration at {holders_str}.",
            f"Sentiment (X/Twitter): Social sentiment is currently {x_sentiment}. {x_summary}",
            f"Risk Warning: {'; '.join(risk_notes)}.",
        ]
        brief_text = "\n".join(f"• {b}" for b in bullets)

    return {
        "contract_address": clean_ca,
        "token_name": token_name,
        "token_symbol": token_symbol,
        "price_usd": price_usd,
        "liquidity_usd": liquidity_usd,
        "top_10_holders_percent": top10_pct,
        "sentiment": x_sentiment,
        "bullets": bullets,
        "brief_text": brief_text,
        "disclaimer": DISCLAIMER,
    }
