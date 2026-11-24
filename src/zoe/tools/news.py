"""Web3 News Retrieval Engine with Source Attribution (Pillar 1).

Retrieves live crypto news for specific tokens, protocols, and market events
using multi-provider search (DuckDuckGo News + Institutional Crypto Feeds).
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from zoe.tools.crypto_news import fetch_crypto_news_sync

logger = logging.getLogger(__name__)


async def fetch_crypto_news(topic: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Retrieve live crypto news within the last 24-48 hours with verified source links.

    Returns:
        List of dicts: [{"title": "...", "snippet": "...", "url": "...", "date": "..."}]
    """
    clean_topic = topic.strip() if topic else "crypto"

    def _sync_fetch() -> List[Dict[str, str]]:
        # Use timelimit="d" (last 24-48 hours)
        raw_items = fetch_crypto_news_sync(clean_topic, timelimit="d", max_results=max_results)
        cleaned: List[Dict[str, str]] = []
        for item in raw_items:
            cleaned.append({
                "title": item.get("title", "").strip(),
                "snippet": item.get("snippet", "").strip(),
                "url": item.get("url", "").strip(),
                "date": item.get("date", "Recent").strip(),
            })
        return cleaned

    try:
        return await asyncio.to_thread(_sync_fetch)
    except Exception as exc:
        logger.warning("fetch_crypto_news failed for '%s': %s", topic, exc)
        return []
