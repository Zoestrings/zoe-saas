"""Web3 Live News Intelligence Tool with Source Attribution.

Fetches real-time crypto news using DuckDuckGo Search with automatic resilient
fallbacks to institutional crypto feeds (CoinTelegraph, Decrypt).
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

import httpx

logger = logging.getLogger(__name__)

# Known crypto news RSS feeds for reliable live fallback
CRYPTO_RSS_FEEDS = [
    {
        "name": "CoinTelegraph",
        "url": "https://cointelegraph.com/rss",
    },
    {
        "name": "Decrypt",
        "url": "https://decrypt.co/feed",
    },
]


def _clean_snippet(text: Optional[str]) -> str:
    """Strip HTML tags and excessive whitespace from news snippets."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:280]


def _format_source_name(url: str, default: str = "Web3 Wire") -> str:
    """Extract a friendly publisher name from an article URL."""
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or ""
        hostname = hostname.replace("www.", "")
        if "coindesk.com" in hostname:
            return "CoinDesk"
        if "cointelegraph.com" in hostname:
            return "CoinTelegraph"
        if "decrypt.co" in hostname:
            return "Decrypt"
        if "theblock.co" in hostname:
            return "The Block"
        if "bloomberg.com" in hostname:
            return "Bloomberg"
        if "reuters.com" in hostname:
            return "Reuters"
        if "u.today" in hostname or "utoday" in hostname:
            return "U.Today"
        if "crypto.com" in hostname:
            return "Crypto.com"
        if "coinmarketcap.com" in hostname:
            return "CoinMarketCap"
        if "coingape.com" in hostname:
            return "CoinGape"
        if "bitcoinist.com" in hostname:
            return "Bitcoinist"
        return hostname.capitalize() if hostname else default
    except Exception:
        return default


def _fetch_from_rss_feeds(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Fallback: Fetch live news items directly from institutional crypto RSS feeds."""
    results: List[Dict[str, str]] = []
    clean_query = query.lower().strip()
    # Normalize common keywords
    keywords = [k for k in re.split(r"[\s,]+", clean_query) if k and k not in {"crypto", "news", "token", "the", "latest", "today", "on", "about"}]

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Zoe/2.0"}

    for feed in CRYPTO_RSS_FEEDS:
        try:
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(feed["url"], headers=headers)
                if resp.status_code != 200:
                    continue

                root = ET.fromstring(resp.content)
                for item in root.findall(".//item"):
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    desc_elem = item.find("description")
                    date_elem = item.find("pubDate")

                    title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                    link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                    desc = _clean_snippet(desc_elem.text) if desc_elem is not None else ""
                    pub_date = date_elem.text.strip() if date_elem is not None and date_elem.text else "Recent"

                    # If specific keywords provided, filter; otherwise include top items
                    full_text = f"{title} {desc}".lower()
                    if keywords:
                        if not any(k in full_text for k in keywords):
                            continue

                    results.append({
                        "title": title,
                        "snippet": desc or title,
                        "url": link,
                        "date": pub_date,
                        "source": feed["name"],
                    })

                    if len(results) >= max_results:
                        return results
        except Exception as exc:
            logger.debug("Failed reading RSS feed %s: %s", feed["name"], exc)

    return results


def _fetch_from_duckduckgo(query: str, timelimit: str = "d", max_results: int = 5) -> List[Dict[str, str]]:
    """Primary: Fetch live news using DuckDuckGo search."""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        logger.warning("duckduckgo_search not installed; skipping DDG provider.")
        return []

    # Ensure search query is targeted for Web3 news
    search_q = query.strip()
    if not any(w in search_q.lower() for w in ("crypto", "news", "token", "coin")):
        search_q = f"{search_q} crypto news"

    results: List[Dict[str, str]] = []

    # First attempt: DDGS.news()
    try:
        with DDGS() as ddgs:
            raw_news = list(ddgs.news(keywords=search_q, region="wt-wt", safesearch="moderate", timelimit=timelimit, max_results=max_results))
            for r in raw_news:
                results.append({
                    "title": r.get("title", "").strip(),
                    "snippet": _clean_snippet(r.get("body", "")),
                    "url": r.get("url", ""),
                    "date": r.get("date", "Recent"),
                    "source": r.get("source") or _format_source_name(r.get("url", "")),
                })
            if results:
                return results
    except Exception as exc:
        logger.debug("DDGS news() returned error, trying text(): %s", exc)

    # Second attempt: DDGS.text()
    try:
        with DDGS() as ddgs:
            raw_text = list(ddgs.text(keywords=search_q, region="wt-wt", safesearch="moderate", timelimit=timelimit, max_results=max_results))
            for r in raw_text:
                url = r.get("href", "")
                results.append({
                    "title": r.get("title", "").strip(),
                    "snippet": _clean_snippet(r.get("body", "")),
                    "url": url,
                    "date": "Recent",
                    "source": _format_source_name(url),
                })
            if results:
                return results
    except Exception as exc:
        logger.debug("DDGS text() returned error: %s", exc)

    return results


def fetch_crypto_news_sync(query: str, timelimit: str = "d", max_results: int = 5) -> List[Dict[str, str]]:
    """Synchronously fetch live crypto news with source attribution and robust fallbacks."""
    if not query or not query.strip():
        return []

    # 1. Try DuckDuckGo
    results = _fetch_from_duckduckgo(query=query, timelimit=timelimit, max_results=max_results)
    if results:
        return results

    # 2. Resilient Fallback: Institutional RSS feeds
    rss_results = _fetch_from_rss_feeds(query=query, max_results=max_results)
    if rss_results:
        return rss_results

    return []


async def fetch_crypto_news(query: str, timelimit: str = "d", max_results: int = 5) -> List[Dict[str, str]]:
    """Asynchronously fetch live crypto news with source attribution and robust fallbacks."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, fetch_crypto_news_sync, query, timelimit, max_results)
