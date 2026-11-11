"""Group sentiment analysis radar classifying community mood into calm, hyped, or panicked/fud."""

import asyncio
import re
from typing import Any, List, Optional

from zoe.utils.logging import get_logger

logger = get_logger("zoe.conversation.sentiment")

# High-precision FUD and panic indicator patterns
FUD_PANIC_PATTERNS = [
    re.compile(r"\b(?:scam|scammer|scammed|rug|rugpull|honeypot|stolen|drain|drained|drainer)\b", re.IGNORECASE),
    re.compile(r"\b(?:dump|dumping|devs?\s+dumping|devs?\s+dumped|crashed|crashing|going\s+to\s+zero|dip\s+hard|liquidity\s+drop(?:ping)?)\b", re.IGNORECASE),
    re.compile(r"\b(?:liquidity\s+pulled|pull(?:ed|ing)?\s+liquidity|pulled\s+lp|lp\s+pulled)\b", re.IGNORECASE),
    re.compile(r"\b(?:dead\s+project|is\s+this\s+dead|sell\s+now|lost\s+(?:all|everything|funds))\b", re.IGNORECASE),
    re.compile(r"\b(?:hacked|exploit|exploited|compromised|fake\s+token|fake\s+contract)\b", re.IGNORECASE),
    re.compile(r"\b(?:looks?\s+like\s+a\s+rug|is\s+this\s+a\s+rug|soft\s+rug|slow\s+rug|we\s+got\s+rugged)\b", re.IGNORECASE),
]

SEVERE_WEB3_FUD_KEYWORDS = [
    re.compile(r"\b(?:rug|rugpull|honeypot|scam)\b", re.IGNORECASE),
    re.compile(r"\b(?:devs?\s+dumping|devs?\s+dumped)\b", re.IGNORECASE),
    re.compile(r"\b(?:liquidity\s+pulled|pull(?:ed|ing)?\s+liquidity)\b", re.IGNORECASE),
    re.compile(r"\b(?:hacked|exploit)\b", re.IGNORECASE),
    re.compile(r"\blooks?\s+like\s+a\s+rug\b", re.IGNORECASE),
]

HYPE_PATTERNS = [
    re.compile(r"\b(?:moon|lfg|pump|pumping|ath|100x|1000x|bullish|flying|send\s+it|gem)\b", re.IGNORECASE),
    re.compile(r"\b(?:buy\s+more|breakout|parabolic|huge\s+news|major\s+announcement)\b", re.IGNORECASE),
]


# In-memory buffer tracking the last 5 messages per group
_GROUP_BUFFERS: dict[str, List[str]] = {}


def record_group_message(group_id: str, message_text: str, max_size: int = 5) -> None:
    """Record incoming message into lightweight local group buffer."""
    if not group_id:
        return
    if group_id not in _GROUP_BUFFERS:
        _GROUP_BUFFERS[group_id] = []
    _GROUP_BUFFERS[group_id].append(message_text)
    if len(_GROUP_BUFFERS[group_id]) > max_size:
        _GROUP_BUFFERS[group_id] = _GROUP_BUFFERS[group_id][-max_size:]


def check_group_panic_buffer(group_id: str) -> bool:
    """Check if 3 out of the last 5 messages in group buffer contain panic keywords."""
    buf = _GROUP_BUFFERS.get(group_id, [])
    if len(buf) < 3:
        return False
    panic_pat = re.compile(r"\b(?:rug|rugged|rugpull|scam|scams|scammed|scammer|hacked|hack|dump|dumping|dumped|dumps)\b", re.IGNORECASE)
    panic_count = sum(1 for m in buf[-5:] if panic_pat.search(m))
    return panic_count >= 3


def classify_sentiment_heuristics(messages: List[str]) -> str:
    """Analyze a batch of messages using weighted sentiment heuristics."""
    if not messages:
        return "calm"

    # Check if 3 out of 5 messages contain panic keywords
    panic_pat = re.compile(r"\b(?:rug|rugged|rugpull|scam|scams|scammed|scammer|hacked|hack|dump|dumping|dumped|dumps)\b", re.IGNORECASE)
    last_5 = messages[-5:] if len(messages) >= 5 else messages
    panic_count = sum(1 for m in last_5 if panic_pat.search(m))
    if panic_count >= 3:
        return "panicked/fud"

    fud_hits = 0
    severe_fud_hits = 0
    hype_hits = 0

    for msg in messages:
        clean = msg.strip()
        if not clean:
            continue
        for pat in SEVERE_WEB3_FUD_KEYWORDS:
            if pat.search(clean):
                severe_fud_hits += 1
                break
        for pat in FUD_PANIC_PATTERNS:
            if pat.search(clean):
                fud_hits += 1
                break
        for pat in HYPE_PATTERNS:
            if pat.search(clean):
                hype_hits += 1
                break

    # Immediate intervention on severe Web3 FUD (rug, honeypot, devs dumping, liquidity pulled, scam, hacked)
    if severe_fud_hits >= 1:
        return "panicked/fud"

    # If 2 or more panic/FUD messages in recent window, or >=25% of messages
    if fud_hits >= 2 or (len(messages) >= 3 and fud_hits / len(messages) >= 0.25) or (len(messages) == 1 and fud_hits >= 1):
        return "panicked/fud"

    if hype_hits >= 2 or (len(messages) >= 3 and hype_hits / len(messages) >= 0.35):
        return "hyped"

    return "calm"


def analyze_group_sentiment_sync(
    recent_messages: List[str],
    llm_client: Optional[Any] = None,
) -> str:
    """Classify group sentiment as 'calm', 'hyped', or 'panicked/fud'.
    
    Uses high-precision weighted regex heuristics with local buffer tracking
    for instant (<0.1ms) execution without blocking the event loop or wasting LLM roundtrips.
    """
    if not recent_messages:
        return "calm"

    return classify_sentiment_heuristics(recent_messages)


async def analyze_group_sentiment(
    recent_messages: List[str],
    llm_client: Optional[Any] = None,
) -> str:
    """Asynchronous entrypoint for analyze_group_sentiment."""
    return analyze_group_sentiment_sync(recent_messages, llm_client)

