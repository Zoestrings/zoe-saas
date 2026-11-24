"""Tool and intent router categorizing incoming user inquiries."""

import re
from typing import Optional

# 1. External Asset Patterns (non-native cryptocurrency assets)
EXTERNAL_ASSET_PATTERNS = [
    re.compile(r"\b(?:bitcoin|btc)\b", re.IGNORECASE),
    re.compile(r"\b(?:ethereum|eth)\b", re.IGNORECASE),
    re.compile(r"\b(?:solana|sol)\b", re.IGNORECASE),
    re.compile(r"\b(?:tether|usdt|usdc)\b", re.IGNORECASE),
    re.compile(r"\b(?:binance|bnb|xrp|ripple|cardano|ada|doge|dogecoin|shib|shiba)\b", re.IGNORECASE),
    re.compile(r"\b(?:avalanche|avax|polkadot|dot|near|sui|aptos|ton|tron|trx|pepe|wif|bonk)\b", re.IGNORECASE),
]

# 1.5. Live Crypto News & X Intelligence Patterns
CRYPTO_NEWS_PATTERNS = [
    re.compile(r"\b(?:latest\s+news|crypto\s+news|token\s+news|market\s+news|breaking\s+news)\b", re.IGNORECASE),
    re.compile(r"\b(?:what(?:'s|\s+is)\s+(?:the\s+)?(?:latest\s+)?news\b|any\s+(?:crypto\s+)?news\b|news\s+(?:on|about|regarding)\b)", re.IGNORECASE),
    re.compile(r"\b(?:what(?:'s|\s+is)\s+happening\s+(?:with|to|in)\b|what\s+happened\s+(?:with|to|in)\b|what(?:'s|\s+is)\s+going\s+on\s+with\b)", re.IGNORECASE),
    re.compile(r"\b(?:did\s+[a-zA-Z0-9$]+\s+(?:break|hit|reach|dump|pump|crash|skyrocket|announce|release|win|lose)\b)", re.IGNORECASE),
    re.compile(r"\b(?:sec\s+(?:drops?|appeals?|lawsuit)|etf\s+approval|upgrade\s+(?:goes\s+)?live|airdrop\s+news)\b", re.IGNORECASE),
]

X_INTELLIGENCE_PATTERNS = [
    re.compile(r"\b(?:what\s+(?:is|are)\s+(?:ct|crypto\s+twitter|people\s+on\s+x|people\s+on\s+twitter)\s+saying)\b", re.IGNORECASE),
    re.compile(r"\b(?:sentiment\s+(?:on|in|for)\s+(?:x|twitter|ct)|x\s+sentiment|twitter\s+sentiment|ct\s+sentiment)\b", re.IGNORECASE),
    re.compile(r"\b(?:trending\s+on\s+(?:crypto\s+twitter|twitter|x)|what\s+is\s+trending\s+on\s+(?:x|twitter|ct))\b", re.IGNORECASE),
    re.compile(r"\b(?:what(?:'s|\s+is)\s+ct\s+saying\b|what\s+is\s+twitter\s+saying\b|what\s+is\s+x\s+saying\b)", re.IGNORECASE),
    re.compile(r"\b(?:narrative\s+on\s+(?:x|twitter)|ct\s+narratives?)\b", re.IGNORECASE),
]

CATALYST_PATTERNS = [
    re.compile(r"\b(?:upcoming\s+(?:events?|catalysts?|conferences?|unlocks?))\b", re.IGNORECASE),
    re.compile(r"\b(?:next\s+(?:[a-zA-Z0-9$]+\s+)?(?:upgrade|hard\s*fork|mainnet(?:\s+launch)?|halving|unlock|token\s+unlock))\b", re.IGNORECASE),
    re.compile(r"\b(?:when\s+is\s+(?:the\s+)?(?:next\s+)?(?:token\s+unlock|unlock|upgrade|mainnet|conference|event)\b)", re.IGNORECASE),
    re.compile(r"\b(?:token\s+unlock\s+date|event\s+calendar|crypto\s+calendar|unlock\s+schedule)\b", re.IGNORECASE),
    re.compile(r"\b(?:any\s+upcoming\s+events\b|catalysts?\s+for\b)", re.IGNORECASE),
]

# 2. Project Native Token Patterns
NATIVE_TOKEN_PATTERNS = [
    re.compile(r"\b(?:\$fly|fly\b|hummingbird|\$hb)\b", re.IGNORECASE),
]

# 3. API Call / Price and Market Patterns
PRICE_AND_MARKET_PATTERNS = [
    re.compile(r"\b(?:price|how\s+much\s+is|current\s+price|token\s+price|worth)\b", re.IGNORECASE),
    re.compile(r"\b(?:liquidity|lp\s+pool|trading\s+pair|pair\s+address)\b", re.IGNORECASE),
    re.compile(r"\b(?:market\s*cap|mcap|fdv|fully\s+diluted|circulating\s+supply|total\s+supply)\b", re.IGNORECASE),
    re.compile(r"\b(?:24h\s+)?volume\b", re.IGNORECASE),
    re.compile(r"\b(?:contract\s+address|token\s+address|\bca\b|dexscreener|dextools|chart|geckoterminal)\b", re.IGNORECASE),
    re.compile(r"\bwen\s+(?:price|token|launch|listing|moon|mint)\b", re.IGNORECASE),
]

# 4. Knowledge Patterns: project docs, mechanisms, whitepaper, staking, KYC
KNOWLEDGE_PATTERNS = [
    re.compile(r"\b(?:hummingbird|\$fly|fly\s+token|onelove|\$onelove|one\s+love)\b", re.IGNORECASE),
    re.compile(r"\b(?:what\s+is\s+(?:the\s+)?project|about\s+(?:the\s+)?project|project\s+all\s+about)\b", re.IGNORECASE),
    re.compile(r"\b(?:whitepaper|documentation|docs|roadmap|tokenomics|audit)\b", re.IGNORECASE),
    re.compile(r"\b(?:creator|founder|team|yacht|vessel|captain|robbie)\b", re.IGNORECASE),
    re.compile(r"\b(?:staking|stake|unstake|unbonding|validator|commission)\b", re.IGNORECASE),
    re.compile(r"\b(?:kyc|kyb|know\s+your\s+(?:customer|business)|verify\s+identity)\b", re.IGNORECASE),
    re.compile(r"\b(?:social\s+campaigns?|b2b\s+campaigns?|rewards?|referral|waitlist|points?|vouchers?)\b", re.IGNORECASE),
    re.compile(r"\b(?:key\s+metrics|creator\s+ad\s+spend|how\s+to\s+join|how\s+does\s+it\s+work)\b", re.IGNORECASE),
    re.compile(r"\b(?:what\s+is\s+the\s+token\s+used\s+for|token\s+utility|use\s+case)\b", re.IGNORECASE),
]

# 5. General & Follow-up Patterns: casual greetings, banter, jokes, follow-ups
CASUAL_PATTERNS = [
    re.compile(r"^\s*(?:gm|gn|hello|hi|hey|good\s+morning|good\s+evening|good\s+night|yo|sup)\b", re.IGNORECASE),
    re.compile(r"\b(?:tell\s+me\s+a\s+joke|make\s+me\s+laugh|who\s+are\s+you|who\s+made\s+you)\b", re.IGNORECASE),
    re.compile(r"\b(?:how\s+are\s+you|how's\s+it\s+going|what's\s+up|thank\s+you|thanks|lol|haha)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:really|for\s+real|are\s+you\s+sure|fr|wait\s+really)\??\s*$", re.IGNORECASE),
]


# EVM & Solana Contract Address Patterns
EVM_CA_PATTERN = re.compile(r"\b(0x[a-fA-F0-9]{40})\b")
SOLANA_CA_PATTERN = re.compile(r"\b([1-9A-HJ-NP-Za-km-z]{32,44})\b")

# General Knowledge & Coding Patterns
GENERAL_KNOWLEDGE_PATTERNS = [
    re.compile(r"\b(?:how\s+do\s+i\s+(?:write|code|create|build)|write\s+a\s+(?:python|script|program|code|loop|function))\b", re.IGNORECASE),
    re.compile(r"\b(?:explain\s+(?:how\s+)?(?:a\s+)?(?:blockchain|smart\s+contracts?|defi|staking|proof\s+of\s+work|proof\s+of\s+stake|layer\s+2|rollup|programming))\b", re.IGNORECASE),
    re.compile(r"\b(?:what\s+is\s+(?:a\s+)?(?:smart\s+contract|cryptocurrency|amm|dex|merkle\s+tree|python\s+loop))\b", re.IGNORECASE),
    re.compile(r"\b(?:how\s+(?:does\s+)?(?:a\s+)?(?:blockchain|smart\s+contract|bitcoin|ethereum)\s+work)\b", re.IGNORECASE),
    re.compile(r"\b(?:python|javascript|typescript|solidity|rust|golang|algorithm|data\s+structure)\b", re.IGNORECASE),
]


def extract_detected_ca(text: str) -> Optional[str]:
    """Detect EVM (0x...) or Solana (base58 32-44 chars) contract address in text."""
    evm_match = EVM_CA_PATTERN.search(text)
    if evm_match:
        return evm_match.group(1)

    for match in SOLANA_CA_PATTERN.finditer(text):
        candidate = match.group(1)
        # Solana addresses strictly exclude 0, O, I, l
        if not any(c in candidate for c in "0OIl"):
            return candidate
    return None


def extract_crypto_news_target(text: str) -> str:
    """Extract the target token, asset, or topic from a crypto news query."""
    clean = text.strip()
    # Check for direct mentions of specific assets
    for pattern in EXTERNAL_ASSET_PATTERNS:
        m = pattern.search(clean)
        if m:
            return m.group(0).upper()

    for pattern in NATIVE_TOKEN_PATTERNS:
        m = pattern.search(clean)
        if m:
            return m.group(0).upper()

    # Look for capitalized ticker or word after 'on', 'about', 'with', 'for'
    topic_match = re.search(r"\b(?:on|about|with|for|regarding|is)\s+([$]?[a-zA-Z0-9]+)\b", clean, re.IGNORECASE)
    if topic_match:
        cand = topic_match.group(1).strip()
        if cand.lower() not in {"the", "a", "an", "any", "this", "today", "now", "it"}:
            return cand.upper()

    # Did X break / hit
    did_match = re.search(r"\bdid\s+([$]?[a-zA-Z0-9]+)\b", clean, re.IGNORECASE)
    if did_match:
        return did_match.group(1).upper()

    return "crypto"


def extract_x_intel_target(text: str) -> str:
    """Extract the target token, ticker, or topic from an X intelligence query."""
    clean = text.strip()
    # 1. Direct $TICKER (e.g. $BTC, $SOL, $ONELOVE)
    ticker_match = re.search(r"(\$[a-zA-Z0-9]+)\b", clean)
    if ticker_match:
        return ticker_match.group(1).upper()

    # 2. Known external assets and native tokens
    for pattern in EXTERNAL_ASSET_PATTERNS + NATIVE_TOKEN_PATTERNS:
        m = pattern.search(clean)
        if m:
            return m.group(0).upper()

    # 3. Topic after 'about', 'on', 'for'
    topic_match = re.search(r"\b(?:about|on|for|regarding|saying\s+about)\s+([$]?[a-zA-Z0-9]+)\b", clean, re.IGNORECASE)
    if topic_match:
        cand = topic_match.group(1).strip()
        if cand.lower() not in {"x", "twitter", "ct", "crypto", "the", "a", "an", "this", "today", "now", "it"}:
            return cand.upper()

    return "Crypto"


def extract_catalyst_target(text: str) -> str:
    """Extract token ticker ($TICKER) or project name for catalyst/event calendar query."""
    clean = text.strip()
    ticker_match = re.search(r"(\$[a-zA-Z0-9]+)\b", clean)
    if ticker_match:
        return ticker_match.group(1).upper()

    for pattern in EXTERNAL_ASSET_PATTERNS + NATIVE_TOKEN_PATTERNS:
        m = pattern.search(clean)
        if m:
            return m.group(0).upper()

    # Look for word after 'for', 'about', 'regarding', 'on'
    target_match = re.search(r"\b(?:for|about|regarding|on)\s+([$]?[a-zA-Z0-9]+)\b", clean, re.IGNORECASE)
    if target_match:
        cand = target_match.group(1).strip()
        if cand.lower() not in {"the", "a", "an", "any", "this", "it", "next", "upcoming"}:
            return cand.upper()

    # Look for word before or after 'upgrade', 'unlock', 'hard fork', 'mainnet'
    event_target_match = re.search(r"\b([$]?[a-zA-Z0-9]+)\s+(?:upgrade|hard\s*fork|mainnet|unlock)\b", clean, re.IGNORECASE)
    if event_target_match:
        cand = event_target_match.group(1).strip()
        if cand.lower() not in {"the", "a", "an", "next", "upcoming", "any", "token"}:
            return cand.upper()

    return "Crypto"


def route_intent(message_text: str) -> str:
    """Route message intent to one of:
    - 'ca_detection': for raw contract addresses (Solana or EVM)
    - 'crypto_news': for real-time crypto news, breaking events, and market intelligence briefs
    - 'general_knowledge': for broad coding or general crypto concepts
    - 'web_search': for price or market inquiries about specific non-native assets
    - 'api_call': for live market or on-chain data for the project's native token
    - 'knowledge': for questions regarding project documentation, mechanics, staking, KYC
    - 'general': for casual chat, greetings, banter
    """
    if not message_text or not message_text.strip():
        return "general"

    text = message_text.strip()

    # 0. Contract Address Detection (Crypto Intelligence Module)
    detected_ca = extract_detected_ca(text)
    if detected_ca:
        return "ca_detection"

    # 0.5. Live Web3 News, X Intelligence, Catalyst Calendar & Web Search Routing
    if any(p.search(text) for p in CATALYST_PATTERNS):
        return "catalyst_calendar"

    if any(p.search(text) for p in X_INTELLIGENCE_PATTERNS):
        return "x_intelligence"

    if re.search(r"\b(?:search\s+(?:the\s+)?web|look\s+up\s+online|google\s+this|browse\s+the\s+web)\b", text, re.IGNORECASE):
        return "web_search"

    if any(p.search(text) for p in CRYPTO_NEWS_PATTERNS):
        return "crypto_news"

    # Inquiries about unreleased, upcoming, or future tokens are knowledge queries
    if re.search(r"\b(?:unreleased|upcoming|future\s+token|new\s+token)\b", text, re.IGNORECASE):
        return "knowledge"

    # 1. Strict Price & Market Query Routing: Must classify as api_call (or web_search for external crypto assets)
    is_price_or_market = any(p.search(text) for p in PRICE_AND_MARKET_PATTERNS) or bool(
        re.search(r"\b(?:price|chart|liquidity|volume|market\s*cap|mcap|fdv)\b", text, re.IGNORECASE)
    )
    is_native = any(p.search(text) for p in NATIVE_TOKEN_PATTERNS)
    is_external = any(p.search(text) for p in EXTERNAL_ASSET_PATTERNS)

    if is_price_or_market:
        # If user asks about an external asset (e.g. Bitcoin, Ethereum, Solana) and not the native token:
        if is_external and not is_native:
            return "web_search"
        # Otherwise, project native token or generic price inquiry routes to DexScreener
        return "api_call"

    # 2. General Knowledge & Coding Routing: Check BEFORE casual chat so questions like
    # "explain how a blockchain works", "what is crypto", "how to write a python script" route to general_knowledge!
    is_project_specific = any(p.search(text) for p in KNOWLEDGE_PATTERNS) or is_native
    if any(p.search(text) for p in GENERAL_KNOWLEDGE_PATTERNS) and not is_project_specific:
        return "general_knowledge"

    # 3. Check for obvious general / casual chat (greetings, jokes, follow-ups)
    for pattern in CASUAL_PATTERNS:
        if pattern.search(text):
            return "general"

    # Explicit web search requests
    if re.search(r"\b(?:search\s+(?:the\s+)?web|look\s+up\s+online|google\s+this)\b", text, re.IGNORECASE):
        return "web_search"

    # 2. Check for project-specific knowledge / documentation inquiry
    for pattern in KNOWLEDGE_PATTERNS:
        if pattern.search(text):
            return "knowledge"

    # 3. Check for obvious general / casual chat
    for pattern in CASUAL_PATTERNS:
        if pattern.search(text):
            return "general"

    # 4. If message mentions project words, route to knowledge
    if re.search(r"\b(?:project|token|app|platform|network|team|founder|hackathon|ecosystem|protocol)\b", text, re.IGNORECASE):
        return "knowledge"

    return "general"
