"""DuckDuckGo web search tool for Zoe."""

import asyncio
from typing import Any, Dict, List, Optional
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS
from zoe.utils.logging import get_logger

logger = get_logger("zoe.tools.web_search")


def search_web_sync(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Search DuckDuckGo synchronously and return title, body, and href for top results."""
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
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
        logger.warning("DuckDuckGo search failed for query '%s': %s", query, str(exc))
        return []


async def search_web(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Async wrapper executing DuckDuckGo search in a thread."""
    return await asyncio.to_thread(search_web_sync, query, max_results)
