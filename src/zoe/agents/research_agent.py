"""Autonomous Scheduled Research Reporter Agent (Pillar 3).

Proactively generates daily "Morning Brief" intelligence reports for projects by
combining live DexScreener market/liquidity data, DuckDuckGo web news, and
Crypto Twitter (X) sentiment, then persisting the brief to Supabase and local SQLite.
"""

import asyncio
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

from zoe.llm.factory import get_llm_client
from zoe.tools.dexscreener import get_token_price, search_token_price
from zoe.tools.web_search import search_web
from zoe.tools.x_intel import analyze_x_sentiment

logger = logging.getLogger("zoe.agents.research_agent")


def _get_supabase_client() -> Optional[Any]:
    """Initialize Supabase service client if configured."""
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or "").strip()
    if not url or not key or "your-project" in url:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as exc:
        logger.debug("Supabase client unavailable for research_agent: %s", exc)
        return None


def _get_dev_db_path() -> Path:
    """Resolve local SQLite dev database path."""
    env_dir = os.getenv("DATA_DIR", "").strip()
    if env_dir:
        return Path(env_dir) / "saas_dev.db"
    root = Path(__file__).resolve().parent.parent.parent.parent
    candidate = root / "saas-dashboard" / "backend" / "saas_dev.db"
    if candidate.exists():
        return candidate
    return root / "data" / "saas_dev.db"


def _ensure_local_reports_table(conn: sqlite3.Connection) -> None:
    """Create dev_research_reports table in local SQLite if not present."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dev_research_reports (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            report_text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_dev_research_reports_proj ON dev_research_reports(project_id, created_at DESC)"
    )
    conn.commit()


def _resolve_project_metadata(
    project_id: str,
    project_name: Optional[str] = None,
    token_address: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """Fetch project name and token_address from Supabase or local SQLite."""
    if project_name and token_address:
        return {"name": project_name, "token_address": token_address}

    resolved_name = project_name
    resolved_ca = token_address

    client = _get_supabase_client()
    if client:
        try:
            res = client.table("projects").select("name, token_address").eq("id", str(project_id)).execute()
            if res.data:
                resolved_name = resolved_name or res.data[0].get("name")
                resolved_ca = resolved_ca or res.data[0].get("token_address")
        except Exception as exc:
            logger.debug("Could not fetch project metadata from Supabase: %s", exc)

    if not resolved_name or not resolved_ca:
        try:
            db_path = _get_dev_db_path()
            if db_path.exists():
                conn = sqlite3.connect(str(db_path), timeout=5.0)
                cur = conn.execute(
                    "SELECT name, token_address FROM dev_projects WHERE id = ?",
                    (str(project_id),),
                )
                row = cur.fetchone()
                conn.close()
                if row:
                    resolved_name = resolved_name or row[0]
                    resolved_ca = resolved_ca or row[1]
        except Exception as exc:
            logger.debug("Could not fetch project metadata from SQLite: %s", exc)

    return {
        "name": resolved_name or f"Project {project_id}",
        "token_address": resolved_ca,
    }


def _persist_report(project_id: str, report_text: str) -> Dict[str, Any]:
    """Save generated report to Supabase `research_reports` and local SQLite."""
    report_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    saved_supabase = False
    client = _get_supabase_client()
    if client:
        try:
            res = client.table("research_reports").insert({
                "id": report_id,
                "project_id": str(project_id),
                "report_text": report_text,
                "created_at": created_at,
            }).execute()
            if res.data and len(res.data) > 0:
                report_id = str(res.data[0].get("id", report_id))
                created_at = str(res.data[0].get("created_at", created_at))
            saved_supabase = True
        except Exception as exc:
            logger.warning("Failed to save research report to Supabase for %s: %s", project_id, exc)

    # Always persist locally for dev/offline resilience
    try:
        db_path = _get_dev_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=10.0)
        _ensure_local_reports_table(conn)
        conn.execute(
            "INSERT INTO dev_research_reports (id, project_id, report_text, created_at) VALUES (?, ?, ?, ?)",
            (report_id, str(project_id), report_text, created_at),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning("Failed to save research report to local SQLite for %s: %s", project_id, exc)

    return {
        "id": report_id,
        "project_id": str(project_id),
        "report_text": report_text,
        "created_at": created_at,
        "persisted_supabase": saved_supabase,
    }


async def generate_daily_report(
    project_id: str,
    project_name: Optional[str] = None,
    token_address: Optional[str] = None,
) -> Dict[str, Any]:
    """Autonomously gather market, news, and X sentiment intelligence for a project
    and synthesize a 3-paragraph Morning Brief saved to `research_reports`.
    """
    meta = _resolve_project_metadata(project_id, project_name, token_address)
    proj_name = meta["name"] or str(project_id)
    ca = meta["token_address"]

    logger.info("Generating daily Morning Brief for project '%s' (%s)...", proj_name, project_id)

    # 1. Fetch Market, News, and X Sentiment concurrently
    async def _fetch_market() -> str:
        try:
            if ca:
                return await get_token_price(ca)
            return await search_token_price(proj_name)
        except Exception as exc:
            logger.warning("DexScreener fetch failed for %s: %s", proj_name, exc)
            return "Market price and liquidity data temporarily unavailable."

    async def _fetch_news() -> List[Dict[str, str]]:
        try:
            return await search_web(f"{proj_name} crypto token news", max_results=4)
        except Exception as exc:
            logger.warning("Web search failed for %s: %s", proj_name, exc)
            return []

    async def _fetch_x() -> Dict[str, Any]:
        try:
            return await analyze_x_sentiment(proj_name, max_tweets=8)
        except Exception as exc:
            logger.warning("X sentiment failed for %s: %s", proj_name, exc)
            return {"sentiment": "Neutral", "summary": "X sentiment data unavailable."}

    market_data, news_items, x_intel = await asyncio.gather(
        _fetch_market(),
        _fetch_news(),
        _fetch_x(),
    )

    news_summary = "\n".join(
        [f"- {n.get('title', 'Update')}: {n.get('snippet', '')[:140]}" for n in (news_items or [])]
    ) or "No breaking news articles indexed in the past 24 hours."

    x_sentiment_label = x_intel.get("sentiment", "Neutral")
    x_summary_text = x_intel.get("summary", "No significant Crypto Twitter activity detected.")
    bearish_factors = ", ".join(x_intel.get("bearish_factors", []) or ["Monitor liquidity & broader market volatility"])

    # 2. Synthesize 3-paragraph Morning Brief via LLM
    system_prompt = (
        "You are Zoe, an autonomous Web3 Intelligence Analyst writing a daily Morning Brief for a crypto project owner. "
        "Write EXACTLY 3 clear, concise, data-grounded paragraphs separated by blank lines:\n"
        "Paragraph 1 (Overnight Market & Liquidity): Summarize the token price, 24h performance, and liquidity depth using only the provided DexScreener telemetry.\n"
        "Paragraph 2 (News & Crypto Twitter Sentiment): Summarize the latest news headlines and X (Twitter) community sentiment.\n"
        "Paragraph 3 (Top 3 Risks & Watchpoints Today): Highlight the 3 most important risks or action items for the project owner today.\n"
        "Do NOT invent price numbers or fake news. Keep the tone executive, sharp, and objective."
    )
    user_prompt = (
        f"PROJECT: {proj_name}\n"
        f"TOKEN ADDRESS: {ca or 'Not configured'}\n\n"
        f"--- DEXSCREENER TELEMETRY ---\n{market_data}\n\n"
        f"--- LATEST NEWS ---\n{news_summary}\n\n"
        f"--- X (TWITTER) SENTIMENT ({x_sentiment_label}) ---\n{x_summary_text}\n"
        f"Observed Risk Signals: {bearish_factors}\n"
    )

    report_text = ""
    try:
        llm = get_llm_client(str(project_id))
        if getattr(llm, "name", "") != "mock":
            generated = await asyncio.to_thread(
                llm.generate,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=550,
            )
            if generated and len(generated.strip()) > 60:
                report_text = generated.strip()
    except Exception as exc:
        logger.warning("LLM synthesis failed for %s, using structured brief fallback: %s", proj_name, exc)

    # Structured fallback if LLM key is missing or offline
    if not report_text:
        clean_market = " ".join(str(market_data).splitlines()[:4])
        top_news_line = news_items[0].get("title", "No major breaking headlines") if news_items else "No major breaking headlines indexed overnight"
        report_text = (
            f"**Overnight Market & Liquidity:** {proj_name} telemetry snapshot: {clean_market}\n\n"
            f"**News & X Sentiment:** Crypto Twitter sentiment is currently **{x_sentiment_label}**. "
            f"{x_summary_text} Top news signal: {top_news_line}.\n\n"
            f"**Top 3 Risks & Watchpoints Today:** (1) Monitor DEX liquidity depth and slippage during peak UTC trading hours; "
            f"(2) Track social narrative shifts around {bearish_factors}; "
            f"(3) Keep official community knowledge base updated to counter potential FUD or misinformation."
        )

    # 3. Persist to Supabase & SQLite
    return _persist_report(str(project_id), report_text)


async def generate_billed_token_report(
    project_id: str,
    token_query: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Agent-to-Agent tool-calling report flow using the Internal Agent Ledger.

    1. Charges 15 credits for Scanner tool -> runs DexScreener / Security Scan.
    2. Charges 10 credits for X Intel tool -> runs Crypto Twitter sentiment.
    3. Combines data into a comprehensive intelligence report.
    """
    from zoe.agents.ledger import charge_user_for_tool, get_last_ledger_alert
    from zoe.tools.scanner import scan_token

    clean_target = (token_query or "").strip()
    if not clean_target:
        return {"success": False, "error": "Please specify a token name or contract address (e.g. `/report $ONELOVE`)."}

    # Step 1: Charge 15 credits for Scanner
    scanner_ok = await charge_user_for_tool(
        project_id=project_id,
        tool_name="scanner",
        credit_cost=15,
        agent_name="Research Agent",
        user_id=user_id,
    )
    if not scanner_ok:
        alert = get_last_ledger_alert(project_id) or "🔒 Insufficient credits. The Research Agent needs 15 credits to access live scanner data."
        return {"success": False, "error": alert, "credits_charged": 0}

    credits_charged = 15
    market_summary = ""
    try:
        if len(clean_target) >= 32 and (" " not in clean_target):
            scan_res = await scan_token(clean_target)
            mkt = scan_res.get("market") or {}
            sec = scan_res.get("security") or {}
            market_summary = (
                f"Token: {scan_res.get('name') or clean_target} ({scan_res.get('symbol') or ''}) | "
                f"Price: ${mkt.get('price_usd', 'N/A')} | Liquidity: ${mkt.get('liquidity_usd', 'N/A')} | "
                f"Top 10 Holders: {sec.get('top_10_holders_percent', 'N/A')}% | Honeypot: {sec.get('is_honeypot', False)}"
            )
        else:
            market_summary = await search_token_price(clean_target.lstrip("$"))
    except Exception as exc:
        market_summary = f"Scanner telemetry error: {exc}"

    # Step 2: Charge 10 credits for X Intel
    x_ok = await charge_user_for_tool(
        project_id=project_id,
        tool_name="x_intel",
        credit_cost=10,
        agent_name="Research Agent",
        user_id=user_id,
    )
    if x_ok:
        credits_charged += 10
        try:
            x_res = await analyze_x_sentiment(clean_target.lstrip("$"), max_tweets=8)
            x_block = f"Sentiment: {x_res.get('sentiment', 'Neutral')} — {x_res.get('summary', '')}"
        except Exception as exc:
            x_block = f"X Intelligence error: {exc}"
    else:
        x_block = get_last_ledger_alert(project_id) or "🔒 Insufficient credits for live X Intel (10 credits)."

    report_text = (
        f"📊 **Autonomous Research Agent Report: {clean_target}**\n"
        f"_(Agent Ledger: {credits_charged} credits billed across verified tools)_\n\n"
        f"**1. Market & Scanner Telemetry (15 credits):**\n{market_summary}\n\n"
        f"**2. X (Twitter) Intelligence (10 credits):**\n{x_block}\n\n"
        f"_Note: Objective intelligence synthesis. Not financial advice._"
    )
    saved = _persist_report(str(project_id), report_text)
    return {
        "success": True,
        "report_id": saved["id"],
        "report_text": report_text,
        "credits_charged": credits_charged,
    }
