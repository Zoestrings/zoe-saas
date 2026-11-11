"""Conversation classifier categorizing incoming community messages."""

from dataclasses import dataclass
import re
from typing import Any, List, Optional

from zoe.utils.logging import get_logger

logger = get_logger("zoe.conversation.classifier")

# 6 Standard categories per Spec §9.2
VALID_CATEGORIES = {
    "casual",
    "project_discussion",
    "direct_question",
    "escalation_trigger",
    "spam",
    "irrelevant",
}

ESCALATION_KEYWORDS = [
    re.compile(r"\b(?:admin|mod|moderator)\b", re.IGNORECASE),
    re.compile(r"\b(?:scam|scammer|phishing|compromised|hacked|stolen)\b", re.IGNORECASE),
    re.compile(r"\b(?:urgent|emergency|funds\s+lost|lost\s+funds)\b", re.IGNORECASE),
]

SPAM_PATTERNS = [
    re.compile(r"\b(?:claim\s+(?:free\s+)?airdrop|free\s+tokens|giveaway|bonus\s+drop)\b", re.IGNORECASE),
    re.compile(r"\b(?:dm\s+me\s+for\s+help|inbox\s+me|whatsapp|t\.me/)\b", re.IGNORECASE),
    re.compile(r"\b(?:pump\s+and\s+dump|100x\s+guaranteed|doubler)\b", re.IGNORECASE),
]

CASUAL_PATTERNS = [
    re.compile(r"^\s*(?:gm|gn|hello|hi|hey|good\s+morning|good\s+evening|good\s+night|yo|sup)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:thanks|thank\s+you|ty|thx|lol|haha|lfg|nice|cool|great|gg|wow|awesome|sweet)\s*[\.!]?$", re.IGNORECASE),
]

FOLLOW_UP_CONFIRMATION_PATTERNS = [
    re.compile(r"^\s*(?:really|for\s+real|are\s+you\s+sure|fr|wait\s+really)\??\s*$", re.IGNORECASE),
]

DIRECT_QUESTION_INDICATORS = [
    re.compile(r"\?"),
    re.compile(r"\b(?:wen|when)\b", re.IGNORECASE),
    re.compile(r"\b(?:how\s+(?:do|can|to|does)|what(?:\s*\'?s|\s+is|\s+are)|where\s+(?:can|is|to)|when\s+(?:is|will)|why\s+(?:does|is)|who\s+is|is\s+there)\b", re.IGNORECASE),
    re.compile(r"\b(?:can\s+(?:someone|anyone|you)|could\s+you|please\s+explain|help\s+with|tell\s+me\s+about)\b", re.IGNORECASE),
    re.compile(r"\b(?:token\s+address|contract\s+address|\bca\b|how\s+to\s+buy|where\s+to\s+buy|unbonding\s+period)\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class ClassificationResult:
    category: str
    confidence: float
    reason: Optional[str] = None
    escalation_keyword: Optional[str] = None


def classify_message(
    text: str,
    context: Optional[List[str]] = None,
    llm_client: Optional[Any] = None,
) -> ClassificationResult:
    """Classify message into one of: casual, project_discussion, direct_question, escalation_trigger, spam, irrelevant."""
    if not text or not text.strip():
        return ClassificationResult(category="irrelevant", confidence=1.0, reason="empty_text")

    clean_text = text.strip()

    # 1. Spam Detection
    for pattern in SPAM_PATTERNS:
        m = pattern.search(clean_text)
        if m:
            return ClassificationResult(
                category="spam",
                confidence=0.90,
                reason="spam_pattern_matched",
            )

    # 2. Escalation Triggers
    for pattern in ESCALATION_KEYWORDS:
        m = pattern.search(clean_text)
        if m:
            return ClassificationResult(
                category="escalation_trigger",
                confidence=0.95,
                reason=f"keyword_{m.group(0).lower()}",
                escalation_keyword=m.group(0).lower(),
            )

    # 3. Casual Small Talk
    for pattern in CASUAL_PATTERNS:
        if pattern.search(clean_text):
            return ClassificationResult(
                category="casual",
                confidence=0.90,
                reason="casual_salutation_or_reaction",
            )

    # 4. Follow-up Confirmations (e.g. "really?", "for real?", "are you sure?")
    for pattern in FOLLOW_UP_CONFIRMATION_PATTERNS:
        if pattern.search(clean_text):
            return ClassificationResult(
                category="direct_question",
                confidence=0.90,
                reason="follow_up_confirmation",
            )

    # 5. Direct Question Detection
    is_question = False
    for pattern in DIRECT_QUESTION_INDICATORS:
        if pattern.search(clean_text):
            is_question = True
            break

    if is_question:
        return ClassificationResult(
            category="direct_question",
            confidence=0.85,
            reason="question_indicator_detected",
        )

    # 5. Project Discussion vs Irrelevant
    # Default non-question, non-spam conversation text is project discussion
    return ClassificationResult(
        category="project_discussion",
        confidence=0.75,
        reason="general_discussion",
    )
