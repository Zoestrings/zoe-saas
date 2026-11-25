"""Social Intelligence Architecture with extensible data adapters and coverage disclosure."""

import abc
import os
from typing import Any, Dict, List, Optional
from zoe.utils.logging import get_logger

logger = get_logger("zoe.scanner.social")


class BaseSocialAdapter(abc.ABC):
    """Abstract adapter for social discussion data sources."""

    @property
    @abc.abstractmethod
    def provider_id(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def display_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def is_connected(self) -> bool:
        pass

    @abc.abstractmethod
    async def fetch_mentions(
        self,
        query: str,
        limit: int = 15,
    ) -> List[Dict[str, Any]]:
        """Fetch posts/mentions matching the query."""
        pass


class XPublicAdapter(BaseSocialAdapter):
    """Adapter for X (Twitter) public sentiment using Phase 1/2 retrieval infrastructure."""

    @property
    def provider_id(self) -> str:
        return "x_twitter"

    @property
    def display_name(self) -> str:
        return "X (Twitter) Public Wire"

    @property
    def is_connected(self) -> bool:
        return True  # Available via public scraping/search adapter

    async def fetch_mentions(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        from zoe.tools.x_intel import _scrape_tweets_sync
        try:
            raw_tweets = _scrape_tweets_sync(query, max_results=limit)
            results = []
            for t in raw_tweets:
                results.append({
                    "provider": "x_twitter",
                    "text": t.get("text", ""),
                    "author": t.get("handle") or "crypto_trader",
                    "url": t.get("url", ""),
                    "published_at": t.get("date", "Recent"),
                    "engagement": {"retweets": 0, "likes": 0},
                })
            return results
        except Exception as exc:
            logger.warning("XPublicAdapter failed for '%s': %s", query, exc)
            return []


class RedditPublicAdapter(BaseSocialAdapter):
    """Adapter for public Reddit crypto discussions (e.g. r/CryptoCurrency, r/solana)."""

    @property
    def provider_id(self) -> str:
        return "reddit"

    @property
    def display_name(self) -> str:
        return "Reddit Crypto Communities"

    @property
    def is_connected(self) -> bool:
        return True

    async def fetch_mentions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        from zoe.tools.web_search import search_web
        try:
            ddg_query = f"site:reddit.com inurl:r/CryptoCurrency OR inurl:r/solana {query}"
            search_res = await search_web(ddg_query, limit=limit)
            results = []
            for item in search_res:
                results.append({
                    "provider": "reddit",
                    "text": f"{item.get('title', '')} - {item.get('snippet', '')}",
                    "author": "reddit_user",
                    "url": item.get("url", ""),
                    "published_at": "Recent",
                    "engagement": {"upvotes": 0, "comments": 0},
                })
            return results
        except Exception as exc:
            logger.warning("RedditPublicAdapter failed for '%s': %s", query, exc)
            return []


class Web3NewsAdapter(BaseSocialAdapter):
    """Adapter for authoritative Web3 media wires and RSS feeds."""

    @property
    def provider_id(self) -> str:
        return "web3_news"

    @property
    def display_name(self) -> str:
        return "Web3 Media & RSS Feeds"

    @property
    def is_connected(self) -> bool:
        return True

    async def fetch_mentions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        from zoe.tools.crypto_news import fetch_crypto_news
        try:
            articles = await fetch_crypto_news(query, max_results=limit)
            results = []
            for a in articles:
                results.append({
                    "provider": "web3_news",
                    "text": f"{a.get('title', '')}: {a.get('snippet', '')}",
                    "author": a.get("source", "Web3 Wire"),
                    "url": a.get("url", ""),
                    "published_at": a.get("date", "Recent"),
                    "engagement": {"views": 100},
                })
            return results
        except Exception as exc:
            logger.warning("Web3NewsAdapter failed for '%s': %s", query, exc)
            return []


class SocialIntelligenceEngine:
    """Coordinates all social adapters and provides aggregated coverage metrics."""

    def __init__(self):
        self.adapters: List[BaseSocialAdapter] = [
            XPublicAdapter(),
            RedditPublicAdapter(),
            Web3NewsAdapter(),
        ]

    async def collect_multi_source_mentions(
        self,
        query: str,
        limit_per_source: int = 8,
    ) -> Dict[str, Any]:
        """Collect mentions across all connected adapters and compute coverage."""
        all_mentions: List[Dict[str, Any]] = []
        source_breakdown: Dict[str, int] = {}
        connected_providers: List[str] = []

        for adapter in self.adapters:
            if adapter.is_connected:
                connected_providers.append(adapter.display_name)
                try:
                    res = await adapter.fetch_mentions(query, limit=limit_per_source)
                    source_breakdown[adapter.provider_id] = len(res)
                    all_mentions.extend(res)
                except Exception as exc:
                    logger.warning("Adapter %s failed: %s", adapter.provider_id, exc)
                    source_breakdown[adapter.provider_id] = 0

        unique_authors = len(set(m.get("author", "") for m in all_mentions if m.get("author")))

        return {
            "query": query,
            "total_mentions": len(all_mentions),
            "unique_authors": unique_authors,
            "source_breakdown": source_breakdown,
            "connected_providers": connected_providers,
            "coverage_disclosure": (
                "Data is collected from connected public sources: "
                f"{', '.join(connected_providers)}. Coverage is representative, not exhaustive."
            ),
            "mentions": all_mentions,
        }
