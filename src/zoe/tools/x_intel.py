"""X (Twitter) Intelligence, Sentiment Analysis, and Narrative Tracking Engine (Pillar 1).

Scrapes public Crypto Twitter discussions and applies LLM-driven sentiment
classification, narrative trend detection, and market psychology analysis.
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

DISCLAIMER_TEXT = "Social sentiment is speculative and does not constitute financial advice. Always DYOR."


def _clean_tweet_text(text: str) -> str:
    """Clean and normalize raw tweet snippet."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _extract_handle(url: str, text: str) -> str:
    """Extract Twitter/X user handle from URL or text."""
    match = re.search(r"(?:x\.com|twitter\.com)/([a-zA-Z0-9_]+)", url)
    if match and match.group(1).lower() not in {"status", "i", "search", "explore", "home"}:
        return f"@{match.group(1)}"
    match_txt = re.search(r"@([a-zA-Z0-9_]{3,15})", text)
    if match_txt:
        return f"@{match_txt.group(1)}"
    return "@CT_Trader"


def _scrape_tweets_sync(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Search DuckDuckGo for public X/Twitter posts matching query."""
    clean_q = query.strip()
    search_queries = [
        f"{clean_q} (site:x.com OR site:twitter.com)",
        f"{clean_q} crypto twitter",
    ]

    tweets: List[Dict[str, str]] = []
    seen_texts = set()

    for sq in search_queries:
        if len(tweets) >= max_results:
            break
        # 1. DDGS text search
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(keywords=sq, region="wt-wt", safesearch="moderate", max_results=max_results))
                    for r in raw_results:
                        url = r.get("href", "") or r.get("link", "")
                        body = _clean_tweet_text(r.get("body", "") or r.get("snippet", ""))
                        title = _clean_tweet_text(r.get("title", ""))
                        full_content = f"{title}: {body}" if title and title not in body else body

                        if not full_content or len(full_content) < 15:
                            continue

                        # Deduplicate
                        sig = full_content[:60].lower()
                        if sig in seen_texts:
                            continue
                        seen_texts.add(sig)

                        tweets.append({
                            "text": full_content,
                            "author": _extract_handle(url, full_content),
                            "url": url,
                        })
                        if len(tweets) >= max_results:
                            break
        except Exception as exc:
            logger.debug("DDGS client failed for '%s': %s", sq, exc)

        # 2. HTML Fallback if DDGS failed or returned 0
        if not tweets:
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
                    for i, snip in enumerate(snippets[:max_results]):
                        c_text = _clean_tweet_text(snip)
                        if not c_text or len(c_text) < 15:
                            continue
                        url = raw_urls[i] if i < len(raw_urls) else ""
                        if "uddg=" in url:
                            m = re.search(r"uddg=([^&]+)", url)
                            if m:
                                url = urllib.parse.unquote(m.group(1))

                        sig = c_text[:60].lower()
                        if sig in seen_texts:
                            continue
                        seen_texts.add(sig)

                        tweets.append({
                            "text": c_text,
                            "author": _extract_handle(url, c_text),
                            "url": url,
                        })
            except Exception as exc:
                logger.debug("HTML fallback failed for '%s': %s", sq, exc)

    return tweets


def _heuristic_sentiment_analysis(query: str, tweets: List[Dict[str, str]]) -> Dict[str, Any]:
    """Fallback sentiment heuristics when LLM is unavailable or offline."""
    bullish_keywords = {"pump", "bullish", "moon", "ath", "breakout", "buy", "long", "gem", "alpha", "accumulate", "undervalued", "holding", "safest"}
    bearish_keywords = {"dump", "bearish", "crash", "rug", "scam", "sell", "short", "fake", "rekt", "avoid", "drainer", "honeypot", "fud"}

    bull_count = 0
    bear_count = 0
    found_narratives = []

    for t in tweets:
        lower = t["text"].lower()
        if any(w in lower for w in bullish_keywords):
            bull_count += 1
        if any(w in lower for w in bearish_keywords):
            bear_count += 1

        # Detect narrative themes
        if "utility" in lower or "real-world" in lower:
            found_narratives.append("Real-world utility & infrastructure expansion")
        if "etf" in lower or "institution" in lower:
            found_narratives.append("Institutional adoption & ETF flows")
        if "meme" in lower or "solana" in lower:
            found_narratives.append("Solana ecosystem liquidity & community momentum")
        if "upgrade" in lower or "layer2" in lower or "l2" in lower:
            found_narratives.append("Protocol upgrade & scalability milestones")

    if not found_narratives:
        found_narratives = [
            f"Community sentiment around {query} expansion",
            "General market momentum and liquidity rotations",
        ]

    # Deduplicate narratives
    top_narratives = list(dict.fromkeys(found_narratives))[:3]

    if bull_count > bear_count * 1.5:
        sentiment = "Bullish"
        summary = f"Crypto Twitter is predominantly optimistic regarding {query}, citing community momentum and accumulation."
    elif bear_count > bull_count * 1.5:
        sentiment = "Bearish"
        summary = f"Crypto Twitter is displaying caution regarding {query}, with conversations highlighting market volatility and sell pressure."
    elif bull_count > 0 and bear_count > 0:
        sentiment = "Mixed"
        summary = f"Discussions on X regarding {query} are currently balanced, with active debate between bulls and bears."
    else:
        sentiment = "Neutral"
        summary = f"Crypto Twitter is observing {query} with steady, neutral activity and moderate discussion volume."

    return {
        "sentiment": sentiment,
        "summary": summary,
        "top_narratives": top_narratives,
        "bullish_factors": ["Community engagement on X", "Positive trading volume mentions"] if bull_count > 0 else ["Stable community chatter"],
        "bearish_factors": ["Macro market volatility", "Potential short-term profit taking"] if bear_count > 0 else ["No significant systemic FUD detected"],
        "tweet_count": len(tweets),
        "disclaimer": DISCLAIMER_TEXT,
    }


def analyze_x_sentiment_sync(query: str, max_tweets: int = 10) -> Dict[str, Any]:
    """Synchronously scrape X/Twitter and produce a structured sentiment & narrative report.

    Rules:
    - If DuckDuckGo returns fewer than 3 tweets, do NOT pass an empty list to the LLM.
      Instead return sentiment: "Unknown" with the required message.
    """
    clean_q = query.strip()
    if not clean_q:
        return {
            "sentiment": "Unknown",
            "summary": "Not enough recent public data to determine sentiment for this token.",
            "top_narratives": [],
            "bullish_factors": [],
            "bearish_factors": [],
            "tweet_count": 0,
            "disclaimer": DISCLAIMER_TEXT,
        }

    tweets = _scrape_tweets_sync(clean_q, max_results=max_tweets)

    # Critical Fallback Rule:
    # If fewer than 3 tweets, do NOT invoke LLM; return Unknown to prevent hallucinations.
    if len(tweets) < 3:
        return {
            "sentiment": "Unknown",
            "summary": "Not enough recent public data to determine sentiment for this token.",
            "top_narratives": [],
            "bullish_factors": [],
            "bearish_factors": [],
            "tweet_count": len(tweets),
            "disclaimer": DISCLAIMER_TEXT,
        }

    # Format tweets for LLM analysis
    tweet_block = "\n".join([f"{i+1}. {t['author']}: \"{t['text']}\"" for i, t in enumerate(tweets[:8])])

    try:
        from zoe.llm.client import get_default_llm_client
        client = get_default_llm_client()
        system_prompt = (
            "You are an expert Web3 Crypto Twitter (CT) intelligence analyst. "
            "Analyze the provided recent tweets and return ONLY a valid, raw JSON object (no markdown, no backticks):\n"
            "{\n"
            '  "sentiment": "Bullish" | "Bearish" | "Neutral" | "Mixed",\n'
            '  "summary": "2-sentence summary of what CT is saying.",\n'
            '  "top_narratives": ["Narrative 1", "Narrative 2"],\n'
            '  "bullish_factors": ["factor 1"],\n'
            '  "bearish_factors": ["factor 1"]\n'
            "}"
        )
        user_prompt = f"TARGET QUERY: {clean_q}\n\nRECENT TWEETS FROM CRYPTO TWITTER:\n{tweet_block}"

        raw_resp = client.generate(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=300)
        if raw_resp:
            cleaned_json = raw_resp.strip()
            if cleaned_json.startswith("```"):
                cleaned_json = re.sub(r"^```(?:json)?\s*", "", cleaned_json)
                cleaned_json = re.sub(r"\s*```$", "", cleaned_json)
            parsed = json.loads(cleaned_json)
            parsed["tweet_count"] = len(tweets)
            parsed["disclaimer"] = DISCLAIMER_TEXT
            if "sentiment" in parsed and "summary" in parsed:
                return parsed
    except Exception as exc:
        logger.debug("LLM sentiment parse failed, using heuristic analyzer: %s", exc)

    return _heuristic_sentiment_analysis(clean_q, tweets)


async def analyze_x_sentiment(query: str, max_tweets: int = 10) -> Dict[str, Any]:
    """Async wrapper for X/Twitter sentiment and narrative analysis."""
    return await asyncio.to_thread(analyze_x_sentiment_sync, query, max_tweets)
