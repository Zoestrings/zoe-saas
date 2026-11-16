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

            results.append({"title": t, "body": s, "href": actual_url})
        return results
    except Exception as exc:
        logger.debug("DuckDuckGo HTML fallback failed: %s", exc)
        return []


def search_web_sync(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Search DuckDuckGo synchronously and return title, body, and href for top results."""
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
            if raw_results:
                results: List[Dict[str, str]] = []
                for r in raw_results:
                    results.append(
                        {
                            "title": r.get("title", ""),
                            "body": r.get("body", "") or r.get("snippet", ""),
                            "href": r.get("href", "") or r.get("link", ""),
                        }
                    )
                return results
    except Exception as exc:
        logger.debug("DDGS client encountered exception, attempting HTML fallback: %s", exc)

    return _ddg_html_fallback(query, max_results=max_results)


async def search_web(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Async wrapper executing DuckDuckGo search in a thread."""
    return await asyncio.to_thread(search_web_sync, query, max_results)
