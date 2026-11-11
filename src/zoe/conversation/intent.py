"""Intent detection engine for autonomous community participation.

Classifies incoming messages into 4 core intents:
- project_question: Questions about the project, staking, tokens, pricing, roadmap, etc.
- project_misinformation: Rumors, panic, FUD, scam/rug accusations.
- casual_chat: Greetings, general reactions, banter not about the project.
- members_talking: General chat/questions between community members about non-project topics.
"""

from dataclasses import dataclass
import re
from typing import Any, List, Optional

from zoe.utils.logging import get_logger

logger = get_logger("zoe.conversation.intent")

VALID_INTENTS = {
    "project_question",
    "project_misinformation",
    "casual_chat",
    "members_talking",
    "crypto_intelligence",
    "api_call",
}

# Contract Address Patterns: EVM (0x + 40 hex) and Solana (Base58 32-44 chars)
EVM_CA_PATTERN = re.compile(r"\b(0x[a-fA-F0-9]{40})\b")
SOLANA_CA_PATTERN = re.compile(r"\b([1-9A-HJ-NP-Za-km-z]{32,44})\b")


def is_tagging_other_human(text: str, bot_names: Optional[List[str]] = None) -> bool:
    """Check if the text tags another human user (@username) and does NOT tag Zoe or a project bot."""
    if not text:
        return False
    bots = {"zoe", "zoetest123_bot", "zoecommunity_bot", "onelove", "onelovemanager_bot"}
    if bot_names:
        bots.update(b.lower().lstrip("@") for b in bot_names if b)
    mentions = re.findall(r"@([A-Za-z0-9_]+)", text)
    if not mentions:
        return False
    # In Telegram, bot usernames strictly end with 'bot'
    has_bot = any(m.lower() in bots or m.lower().endswith("bot") for m in mentions)
    has_human = any(m.lower() not in bots and not m.lower().endswith("bot") for m in mentions)
    return has_human and not has_bot


def detect_contract_address(text: str) -> Optional[str]:
    """Detect EVM (0x...) or Solana (Base58 32-44 characters) contract address in text."""
    if not text or not text.strip():
        return None

    # Check EVM address first
    evm_match = EVM_CA_PATTERN.search(text)
    if evm_match:
        return evm_match.group(1)

    # Check Solana Base58 address (strictly excluding 0, O, I, l)
    for match in SOLANA_CA_PATTERN.finditer(text):
        candidate = match.group(1)
        if not any(c in candidate for c in "0OIl"):
            return candidate

    return None

PROJECT_MISINFO_PATTERNS = [
    re.compile(
        r"\b(?:rug|rugged|rugpull|scam|scams|scammed|scammer|honeypot|fake\s+ca|fake\s+contract|"
        r"devs?\s+dump(?:ed|ing|s)?|liquidity\s+pulled|pull(?:ed)?\s+liquidity|slow\s+rug|drained|"
        r"stolen\s+funds|ponzi|exit\s+scam)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:is\s+this\s+(?:a\s+)?(?:rug|scam|honeypot)|why\s+did\s+devs?\s+dump|"
        r"did\s+they\s+pull\s+liquidity|we\s+got\s+rugged)\b",
        re.IGNORECASE,
    ),
]

PROJECT_QUESTION_KEYWORDS = [
    re.compile(
        r"\b(?:stake|staking|unstake|unstaking|unbond|unbonding|reward|rewards|yield|apy|apr|"
        r"token|tokens|tokenomics|supply|circulating|contract|contract\s+address|\bca\b|"
        r"how\s+(?:do|can)\s+i\s+buy|where\s+(?:can|to)\s+buy|how\s+to\s+buy|where\s+to\s+buy|"
        r"ath|atl|"
        r"roadmap|whitepaper|docs|documentation|team|founder|utility|airdrop|allocation|vesting|lockup|"
        r"fly|hummingbird|protocol|upgrade|mainnet|testnet|nodes?|validators?|"
        r"kyc|kyb|verify|verification|identity|"
        r"solana|sol|bitcoin|btc|ethereum|eth|crypto|web3|blockchain|smart\s+contracts?|"
        r"python|coding|code|script|program|"
        r"hackathon|grant|bounty|ecosystem|bridge|dao|dex|amm|defi)\b",
        re.IGNORECASE,
    ),
]

CASUAL_CHAT_PATTERNS = [
    re.compile(
        r"^\s*(?:gm|gn|hello|hi|hey|good\s+morning|good\s+evening|good\s+night|yo|sup|what\'?s\s+up)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:thanks|thank\s+you|ty|thx|lol|haha|lfg|nice|cool|great|gg|wow|awesome|sweet|wagmi)\s*[\.!]?$",
        re.IGNORECASE,
    ),
]

MEMBERS_TALKING_PATTERNS = [
    re.compile(
        r"\b(?:who\s+watched|did\s+you\s+see|who\s+saw|the\s+match|the\s+game|football|soccer|champions\s+league|"
        r"what\s+did\s+you\s+eat|what\s+are\s+you\s+guys\s+doing|anyone\s+here|anyone\s+online|"
        r"how\s+was\s+your\s+day|how\s+was\s+your\s+weekend|going\s+to\s+the\s+gym|weather)\b",
        re.IGNORECASE,
    ),
]

INTENT_LLM_PROMPT = """You are an intent classification engine for a Web3 community chat.
Classify the given message into EXACTLY ONE of the following 4 categories:
- project_question: Questions about the crypto project, tokens, staking, buying, roadmap, price, liquidity, contract address, or documentation.
- project_misinformation: Accusations, rumors, panic, or FUD about rugs, scams, honeypots, fake contracts, pulled liquidity, or devs dumping.
- casual_chat: Casual greetings (GM, hey), personal pleasantries, or general slang without project questions.
- members_talking: Conversational chat or questions directed at other human community members about non-project topics (sports, food, weather, personal life).

Message: "{message}"

Respond with ONLY the exact category name. Nothing else."""


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float
    source: str  # 'heuristic' or 'llm'


def detect_intent(
    text: str,
    context: Optional[List[str]] = None,
    llm_client: Optional[Any] = None,
) -> IntentResult:
    """Classify the intent of an incoming community message."""
    if not text or not text.strip():
        return IntentResult(intent="casual_chat", confidence=1.0, source="heuristic")

    clean_text = text.strip()

    # --- ULTRA-FAST HEURISTIC CHECKS (Zero LLM Overhead) ---
    # 1. Exact greetings: GM, GN, hi, hello, hey, yo, sup
    if re.match(r"^(?:gm|gn|hi|hello|hey|yo|sup)$", clean_text, re.IGNORECASE):
        return IntentResult(intent="casual_chat", confidence=1.0, source="heuristic")

    # 2. Strict Price & Market Query Routing -> api_call
    if re.search(r"\b(?:price|chart|liquidity|volume|market\s*cap|mcap|fdv)\b", clean_text, re.IGNORECASE):
        return IntentResult(intent="api_call", confidence=1.0, source="heuristic")

    # 3. Contract Address Detection (0x... or 32-44 base58 chars) -> crypto_intelligence
    ca = detect_contract_address(clean_text)
    if ca:
        return IntentResult(intent="crypto_intelligence", confidence=1.0, source="heuristic")

    # 4. Explicit Bot Tagging Check: If the message explicitly tags the bot, ensure it routes directly
    if re.search(r"@(zoe|onelove|onelovemanager_bot|zoecommunity_bot|zoetest123_bot|\w*bot)\b", clean_text, re.IGNORECASE):
        if re.search(r"^\s*@\w+\s+(?:gm|gn|hi|hello|hey|yo|sup)$", clean_text, re.IGNORECASE):
            return IntentResult(intent="casual_chat", confidence=0.95, source="heuristic")
        if re.search(r"\b(?:price|chart|liquidity|volume|market\s*cap|mcap|fdv)\b", clean_text, re.IGNORECASE):
            return IntentResult(intent="api_call", confidence=1.0, source="heuristic")
        return IntentResult(intent="project_question", confidence=0.95, source="heuristic")

    # Inquiries about unreleased, upcoming, or future tokens are knowledge queries
    if re.search(r"\b(?:unreleased|upcoming|future\s+token|new\s+token)\b", clean_text, re.IGNORECASE):
        return IntentResult(intent="project_question", confidence=0.95, source="heuristic")

    # Human-to-Human Tagging check: If message tags another human (not Zoe) and is conversational, classify as casual_chat
    if is_tagging_other_human(clean_text):
        return IntentResult(intent="casual_chat", confidence=0.95, source="heuristic")

    # 4. Project Misinformation / FUD check (Highest priority for community health)
    for pat in PROJECT_MISINFO_PATTERNS:
        if pat.search(clean_text):
            return IntentResult(intent="project_misinformation", confidence=0.95, source="heuristic")

    # 5. Project Question check
    has_project_kw = any(pat.search(clean_text) for pat in PROJECT_QUESTION_KEYWORDS)
    is_question = "?" in clean_text or bool(
        re.search(r"\b(?:how|what|where|when|why|who|can\s+i|can\s+someone|is\s+there)\b", clean_text, re.IGNORECASE)
    )

    if has_project_kw:
        # If it has project keywords, it's either a question or project topic
        return IntentResult(intent="project_question", confidence=0.90, source="heuristic")

    # 6. Members talking between themselves about non-project topics
    for pat in MEMBERS_TALKING_PATTERNS:
        if pat.search(clean_text):
            return IntentResult(intent="members_talking", confidence=0.90, source="heuristic")

    # 7. Casual greetings or reactions
    for pat in CASUAL_CHAT_PATTERNS:
        if pat.search(clean_text):
            return IntentResult(intent="casual_chat", confidence=0.90, source="heuristic")

    # 8. Fallback or general conversational question between members
    if is_question and not has_project_kw:
        return IntentResult(intent="members_talking", confidence=0.75, source="heuristic")

    # ONLY call the LLM for intent classification if the heuristics fail
    if llm_client is not None:
        try:
            resp = llm_client.generate(
                system_prompt="You are an intent classifier.",
                user_prompt=INTENT_LLM_PROMPT.format(message=clean_text),
                max_tokens=20,
            )
            parsed = resp.strip().lower()
            if parsed in VALID_INTENTS:
                return IntentResult(intent=parsed, confidence=0.85, source="llm")
        except Exception as exc:
            logger.debug("LLM intent classification fallback to heuristic: %s", exc)

    return IntentResult(intent="casual_chat", confidence=0.60, source="heuristic")
