"""Catalyst & Event Calendar Intelligence Tool (Pillar 1).

Retrieves verified upcoming token unlocks, protocol upgrades, mainnet launches,
and crypto conference dates with source attribution.
"""

import asyncio
from html import unescape
import json
import logging
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

logger = logging.getLogger(__name__)


def _clean_text(text: str) -> str:
    """Strip tags and normalize whitespace."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = unescape(clean)
    return re.sub(r"\s+", " ", clean).strip()


def _search_catalysts_ddg(query: str, max_results: int = 6) -> List[Dict[str, str]]:
    """Search DuckDuckGo for upcoming crypto catalysts and event milestones."""
    clean_q = query.strip()
    search_queries = [
        f"{clean_q} crypto upcoming events calendar 2026",
        f"{clean_q} token unlock date roadmap mainnet",
    ]

    results: List[Dict[str, str]] = []
    seen_urls = set()

    for sq in search_queries:
        if len(results) >= max_results:
            break
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(keywords=sq, region="wt-wt", safesearch="moderate", max_results=max_results))
                    for r in raw_results:
                        url = r.get("href", "") or r.get("link", "")
                        body = _clean_text(r.get("body", "") or r.get("snippet", ""))
                        title = _clean_text(r.get("title", ""))

                        if not body or len(body) < 20 or url in seen_urls:
                            continue
                        seen_urls.add(url)

                        results.append({
                            "title": title,
                            "snippet": body,
                            "url": url,
                        })
                        if len(results) >= max_results:
                            break
        except Exception as exc:
            logger.debug("DDGS client failed for catalyst query '%s': %s", sq, exc)

        if not results:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                }
                resp = httpx.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": sq},
                    headers=headers,
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', resp.text)
                    raw_urls = re.findall(r'href="(//duckduckgo\.com/l/\?[^"]+)"', resp.text)
                    titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', resp.text)
                    for i, snip in enumerate(snippets[:max_results]):
                        s_text = _clean_text(snip)
                        t_text = _clean_text(titles[i]) if i < len(titles) else ""
                        url = raw_urls[i] if i < len(raw_urls) else ""
                        if "uddg=" in url:
                            m = re.search(r"uddg=([^&]+)", url)
                            if m:
                                url = urllib.parse.unquote(m.group(1))
                        if url and url not in seen_urls and s_text:
                            seen_urls.add(url)
                            results.append({"title": t_text, "snippet": s_text, "url": url})
            except Exception as exc:
                logger.debug("HTML fallback failed for catalyst query: %s", exc)

    return results


def _extract_events_from_snippets(query: str, snippets: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Heuristic / LLM extraction of confirmed dates and events from search snippets."""
    if not snippets:
        return []

    # Prompt LLM to extract events with strict JSON output
    snippet_context = "\n".join([
        f"- Title: {s['title']}\n  Snippet: {s['snippet']}\n  Source: {s['url']}"
        for s in snippets[:6]
    ])

    try:
        from zoe.llm.client import get_default_llm_client
        client = get_default_llm_client()
        system_prompt = (
            "You are a Web3 Catalyst and Crypto Event Researcher. "
            "Read the search results and extract up to 3 upcoming confirmed events, token unlocks, mainnet launches, or conferences. "
            "STRICT RULES:\n"
            "1. NEVER hallucinate dates or events. If no future or upcoming dates exist in the snippets, return an empty array `[]`.\n"
            "2. Return ONLY a raw JSON array of objects without markdown formatting or backticks:\n"
            '[{"date": "YYYY-MM-DD or Month YYYY", "event": "Clear description", "source": "URL"}]\n'
            "If no confirmed events are mentioned, return strictly `[]`."
        )
        user_prompt = f"TARGET ASSET: {query}\n\nSEARCH RESULTS:\n{snippet_context}"

        raw_resp = client.generate(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=250)
        if raw_resp:
            cleaned = raw_resp.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                valid_events = []
                for item in parsed:
                    if isinstance(item, dict) and "event" in item and "date" in item:
                        valid_events.append({
                            "date": str(item.get("date", "Upcoming")).strip(),
                            "event": str(item.get("event", "")).strip(),
                            "source": str(item.get("source") or snippets[0]["url"]).strip(),
                        })
                return valid_events[:3]
    except Exception as exc:
        logger.debug("LLM event extraction fallback to heuristic parsing: %s", exc)

    # Heuristic Regex Extraction: Find snippets with explicit dates
    events: List[Dict[str, str]] = []
    date_regex = re.compile(r"\b((?:202[5-9]|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-zA-Z0-9\s,\.\-–]{3,20})\b", re.IGNORECASE)

    for s in snippets:
        match = date_regex.search(s["snippet"]) or date_regex.search(s["title"])
        if match and any(k in s["snippet"].lower() for k in ("unlock", "upgrade", "launch", "conference", "breakpoint", "hard fork", "summit", "testnet", "mainnet")):
            date_str = match.group(0).strip()
            # Construct short description
            desc = s["title"] if len(s["title"]) < 80 else s["snippet"][:80] + "..."
            events.append({
                "date": date_str,
                "event": desc,
                "source": s["url"],
            })
            if len(events) >= 3:
                break

    return events


def get_upcoming_events_sync(query: str) -> List[Dict[str, str]]:
    """Synchronously retrieve confirmed upcoming catalysts and events.

    Returns:
        List of dicts: [{"date": "...", "event": "...", "source": "..."}]
        Returns empty list [] if no live confirmed events are found.
    """
    clean_q = query.strip()
    if not clean_q:
        return []

    snippets = _search_catalysts_ddg(clean_q, max_results=6)
    if not snippets:
        return []

    return _extract_events_from_snippets(clean_q, snippets)


async def get_upcoming_events(query: str) -> List[Dict[str, str]]:
    """Async wrapper to retrieve upcoming catalysts and events."""
    return await asyncio.to_thread(get_upcoming_events_sync, query)
