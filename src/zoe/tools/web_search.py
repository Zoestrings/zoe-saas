"""DuckDuckGo web search tool for Zoe with fallback support."""

import asyncio
from html import unescape
import re
from typing import Any, Dict, List, Optional
import urllib.parse
import warnings
import httpx

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS
from zoe.utils.logging import get_logger

logger = get_logger("zoe.tools.web_search")


def _ddg_html_fallback(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Direct HTTP fallback to DuckDuckGo HTML endpoint if DDGS client encounters errors."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        resp = httpx.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers=headers,
            timeout=6.0,
        )
        if resp.status_code != 200:
            return []

        html = resp.text
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html)
        raw_hrefs = re.findall(r'href="(//duckduckgo\.com/l/\?[^"]+)"', html) or re.findall(r'href="(https?://[^"]+)"\s+class="result__url"', html)

        results: List[Dict[str, str]] = []
        for i in range(min(len(titles), max_results)):
            t = unescape(re.sub(r"<[^>]+>", "", titles[i])).strip()
            s = unescape(re.sub(r"<[^>]+>", "", snippets[i])).strip() if i < len(snippets) else ""
            raw_url = raw_hrefs[i] if i < len(raw_hrefs) else ""

            # Unquote DuckDuckGo redirect uddg parameter
            actual_url = raw_url
            if "uddg=" in raw_url:
                match = re.search(r"uddg=([^&]+)", raw_url)
                if match:
                    actual_url = urllib.parse.unquote(match.group(1))
            elif raw_url.startswith("//"):
                actual_url = f"https:{raw_url}"

            results.append({
                "title": t,
                "snippet": s,
                "body": s,
                "url": actual_url,
                "href": actual_url,
                "date": "Recent",
            })
        return results
    except Exception as exc:
        logger.debug("DuckDuckGo HTML fallback failed: %s", exc)
        return []


def search_web_sync(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Search DuckDuckGo synchronously with TTL caching and SSRF validation."""
    if not query or not query.strip():
        return []

    from zoe.tools.search_cache import GLOBAL_SEARCH_CACHE, is_safe_public_url

    # 1. Check Cache
    cached = GLOBAL_SEARCH_CACHE.get(query)
    if cached:
        logger.debug("Cache hit for web search query: %r", query)
        return cached[:max_results]

    raw_results: List[Dict[str, Any]] = []
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
            if raw_results:
                results: List[Dict[str, str]] = []
                for r in raw_results:
                    snip = r.get("body", "") or r.get("snippet", "")
                    url = r.get("href", "") or r.get("link", "")
                    if url and not is_safe_public_url(url):
                        continue
                    results.append(
                        {
                            "title": r.get("title", ""),
                            "snippet": snip,
                            "body": snip,
                            "url": url,
                            "href": url,
                            "date": r.get("date", "Recent"),
                        }
                    )
                if results:
                    GLOBAL_SEARCH_CACHE.set(query, results)
                    return results
    except Exception as exc:
        logger.debug("DDGS client encountered exception, attempting HTML fallback: %s", exc)

    fallback_results = _ddg_html_fallback(query, max_results=max_results)
    if fallback_results:
        # Filter safe URLs
        safe_fallback = [r for r in fallback_results if is_safe_public_url(r.get("url"))]
        if safe_fallback:
            GLOBAL_SEARCH_CACHE.set(query, safe_fallback)
            return safe_fallback
    return fallback_results


async def search_web(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Async wrapper executing DuckDuckGo search in a thread."""
    return await asyncio.to_thread(search_web_sync, query, max_results)
