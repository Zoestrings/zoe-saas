"""Web3 Research Engine using permitted sources (DexScreener, Crypto News, Official Web Docs)."""

from datetime import datetime, timezone
import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

from zoe.social.publisher import ensure_social_growth_schema
from zoe.tools.crypto_news import fetch_crypto_news
from zoe.tools.scanner import detect_chain, fetch_dexscreener_market_data

logger = logging.getLogger("zoe.social.research_engine")

VALID_RESEARCH_CATEGORIES = {
    "project_discovery",
    "ecosystem",
    "defi_nft",
    "rwa_tokenization",
    "narrative",
    "announcement",
}


async def run_web3_research(
    user_id: str,
    organization_id: str,
    query: str,
    category: str = "ecosystem",
    project_id: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """Run attributed Web3 research using only permitted market, news, and official sources."""
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("Research query is required.")
    clean_cat = category.strip().lower() if category else "ecosystem"
    if clean_cat not in VALID_RESEARCH_CATEGORIES:
        clean_cat = "ecosystem"

    sources: List[Dict[str, str]] = []
    structured_data: Dict[str, Any] = {"category": clean_cat, "query": clean_query}

    # 1. If query looks like a CA, fetch live DexScreener market snapshot
    chain_type = detect_chain(clean_query)
    if chain_type in ("solana", "evm"):
        snap = await fetch_dexscreener_market_data(clean_query)
        if snap and snap.get("found"):
            structured_data["market_snapshot"] = {
                "name": snap.get("name"),
                "symbol": snap.get("symbol"),
                "chain_id": snap.get("chain_id"),
                "price_usd": snap.get("price_usd"),
                "market_cap": snap.get("market_cap"),
                "liquidity_usd": snap.get("liquidity_usd"),
            }
            sources.append({"provider": "DexScreener", "reference": f"chain:{snap.get('chain_id')}:{clean_query}"})

    # 2. Fetch permitted crypto news / announcements
    try:
        news_items = await fetch_crypto_news(query=clean_query, limit=5)
        if isinstance(news_items, list) and news_items:
            structured_data["news_headlines"] = [
                {"title": str(n.get("title", "")), "url": str(n.get("url", "")), "source": str(n.get("source", "CryptoNews"))}
                for n in news_items[:5]
                if isinstance(n, dict)
            ]
            for item in structured_data["news_headlines"]:
                sources.append({"provider": item["source"], "reference": item["url"] or item["title"]})
    except Exception as exc:
        logger.debug("Crypto news lookup skipped/failed for '%s': %s", clean_query, exc)

    if not sources:
        sources.append({"provider": "Zoe Permitted Research Index", "reference": f"query:{clean_query}"})

    # 3. Synthesize summary via LLMRouter with deterministic fallback
    title = f"{clean_cat.replace('_', ' ').title()} Research: {clean_query[:60]}"
    summary = ""
    try:
        from zoe.llm.router import LLMRouter
        router = LLMRouter()
        prompt = (
            f"Summarize Web3 {clean_cat} research for '{clean_query}' based strictly on these verified inputs: "
            f"{json.dumps(structured_data)[:1500]}. Be objective, cite sources, and do not promise financial returns."
        )
        resp = await router.generate(prompt=prompt, max_tokens=320)
        summary = (resp.text if hasattr(resp, "text") else str(resp)).strip()
    except Exception:
        pass

    if not summary:
        headline_count = len(structured_data.get("news_headlines", []))
        snap_info = structured_data.get("market_snapshot")
        snap_text = (
            f"Market data ({snap_info['symbol']} on {snap_info['chain_id']}): "
            f"price ${snap_info['price_usd']}, liquidity ${snap_info['liquidity_usd']}. "
            if snap_info
            else ""
        )
        summary = (
            f"Permitted-source research brief for '{clean_query}' ({clean_cat}). "
            f"{snap_text}Collected {headline_count} attributed news/announcement references."
        )

    report_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    report = {
        "id": report_id,
        "user_id": str(user_id),
        "organization_id": str(organization_id),
        "project_id": project_id,
        "category": clean_cat,
        "query": clean_query,
        "title": title,
        "summary": summary,
        "sources": sources,
        "data": structured_data,
        "created_at": now_iso,
    }

    if conn is not None:
        ensure_social_growth_schema(conn)
        conn.execute(
            """
            INSERT INTO web3_research_reports (
                id, user_id, organization_id, project_id, category, query,
                title, summary, sources_json, data_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                str(user_id),
                str(organization_id),
                project_id,
                clean_cat,
                clean_query,
                title,
                summary,
                json.dumps(sources),
                json.dumps(structured_data),
                now_iso,
            ),
        )
        conn.commit()

    return report
