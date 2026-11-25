"""Thread-safe TTL Cache, Deduplication, and SSRF Protection for Web & News Retrieval."""

from datetime import datetime, timezone
import ipaddress
import logging
import re
import socket
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger("zoe.tools.search_cache")

# Private and non-routable IP networks to block (SSRF defense)
BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / AWS metadata
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),  # Carrier-grade NAT
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def is_safe_public_url(url: Optional[str]) -> bool:
    """Validate that a URL is a legitimate public web destination and does not target internal assets (SSRF)."""
    if not url or not isinstance(url, str):
        return False

    url_str = url.strip()
    if not url_str.startswith(("http://", "https://")):
        return False

    try:
        parsed = urlparse(url_str)
        hostname = parsed.hostname
        if not hostname:
            return False

        hostname_lower = hostname.lower()
        if hostname_lower in ("localhost", "127.0.0.1", "::1", "metadata.google.internal", "instance-data"):
            return False

        if hostname_lower.endswith((".local", ".internal", ".localhost")):
            return False

        # Attempt to resolve IP address
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for _, _, _, _, sockaddr in addr_info:
                ip_str = sockaddr[0]
                ip_obj = ipaddress.ip_address(ip_str)
                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                    logger.warning("SSRF defense blocked destination IP: %s (hostname: %s)", ip_str, hostname)
                    return False
                for blocked_net in BLOCKED_NETWORKS:
                    if ip_obj in blocked_net:
                        logger.warning("SSRF defense blocked subnet destination: %s", ip_str)
                        return False
        except socket.gaierror:
            # If DNS resolution fails, allow regular web hostnames to proceed if syntax is valid
            pass

        return True
    except Exception as exc:
        logger.debug("URL safety validation exception for %s: %s", url, exc)
        return False


class SearchAndNewsCache:
    """Thread-safe In-Memory TTL Cache for Web Search and Crypto News."""

    def __init__(self, default_ttl_seconds: int = 600):
        self.default_ttl = default_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _normalize_key(self, query: str, context: Optional[str] = None) -> str:
        clean_q = re.sub(r"\s+", " ", query.strip().lower())
        ctx = f":{context.strip().lower()}" if context else ""
        return f"{clean_q}{ctx}"

    def get(self, query: str, context: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Retrieve unexpired results from cache."""
        key = self._normalize_key(query, context)
        now = time.time()
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            if entry["expires_at"] < now:
                del self._cache[key]
                return None
            # Return a copy marked with cache metadata
            cached_data = []
            for item in entry["results"]:
                item_copy = dict(item)
                item_copy["_from_cache"] = True
                item_copy["_retrieved_at"] = entry["retrieved_at"]
                cached_data.append(item_copy)
            return cached_data

    def set(
        self,
        query: str,
        results: List[Dict[str, Any]],
        context: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Store results in cache with TTL and timestamp."""
        if not results:
            return  # Do not cache empty/failed results

        key = self._normalize_key(query, context)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Sanitize and deduplicate results
        deduped = []
        seen_identifiers = set()

        for r in results:
            url = r.get("url") or r.get("href") or ""
            # SSRF validation: Drop unsafe private/loopback URLs
            if url and not is_safe_public_url(url):
                logger.warning("Dropping unsafe URL from search results: %s", url)
                continue

            title = (r.get("title") or "").strip()
            identifier = url.lower() if url else title.lower()
            if not identifier or identifier in seen_identifiers:
                continue

            seen_identifiers.add(identifier)
            item = dict(r)
            item["_retrieved_at"] = now_iso
            deduped.append(item)

        with self._lock:
            self._cache[key] = {
                "results": deduped,
                "retrieved_at": now_iso,
                "expires_at": now + ttl,
            }

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


# Global Singleton Cache
GLOBAL_SEARCH_CACHE = SearchAndNewsCache(default_ttl_seconds=600)  # 10 minute TTL
