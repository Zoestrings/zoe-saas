"""Fail-closed safety validator filtering output before delivery."""

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from zoe.knowledge.retriever import RetrievedChunk
from zoe.utils.logging import get_logger

logger = get_logger("zoe.safety.validator")

# Prohibited patterns
PRICE_PREDICTION_PATTERNS = [
    re.compile(r"\bto\s+the\s+moon\b", re.IGNORECASE),
    re.compile(r"\b(?:will\s+hit|reach(?:es)?)\s+\$?\d+", re.IGNORECASE),
    re.compile(r"\b(?:price\s+target|100x|10x\s+guaranteed|guaranteed\s+profit)\b", re.IGNORECASE),
    re.compile(r"\b(?:pump\s+incoming|moonshot|buy\s+before\s+it\s+explodes)\b", re.IGNORECASE),
]

KYC_PROMISE_PATTERNS = [
    re.compile(r"\b(?:guarantee|guaranteed|instant)\s+(?:kyc\s+)?approval\b", re.IGNORECASE),
    re.compile(r"\b(?:bypass\s+kyc|no\s+kyc\s+(?:required|needed))\b", re.IGNORECASE),
]

CREDENTIAL_REQUEST_PATTERNS = [
    re.compile(r"\b(?:seed\s+phrase|private\s+key|mnemonic(?:\s+phrase)?|recovery\s+phrase)\b", re.IGNORECASE),
    re.compile(r"\b(?:enter|provide|share|input)\s+(?:your\s+)?(?:12|24)\s+words\b", re.IGNORECASE),
    re.compile(r"\b(?:export|backup)\s+your\s+private\s+key\b", re.IGNORECASE),
]

# Permitted URLs: Known official project and Web3 service domains
DEFAULT_APPROVED_DOMAINS = {
    "dexscreener.com",
    "t.me",
    "twitter.com",
    "x.com",
    "github.com",
    "hummingbird.org",
    "solscan.io",
    "etherscan.io",
    "google.com",
    "duckduckgo.com",
    "coinmarketcap.com",
    "coingecko.com",
    "solana.com",
    "ethereum.org",
    "bitcoin.org",
    "docs.hummingbird.org",
}

SAFE_FALLBACK_TEXT = "I'm not sure about that, better check the official announcements."


@dataclass(frozen=True)
class SafetyResult:
    is_safe: bool
    violations: List[str]
    safe_text: Optional[str] = None


def validate_output(
    text: str,
    provenance: Optional[List[RetrievedChunk]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> SafetyResult:
    """Validate generated output against safety rules in a strictly fail-closed manner.

    If an exception occurs during validation, the response is rejected immediately.
    """
    try:
        if not text or not text.strip():
            return SafetyResult(is_safe=False, violations=["empty_output"], safe_text=SAFE_FALLBACK_TEXT)

        violations: List[str] = []

        # 1. Price prediction check
        for pattern in PRICE_PREDICTION_PATTERNS:
            if pattern.search(text):
                violations.append("prohibited_price_prediction")
                break

        # 2. KYC promises check
        for pattern in KYC_PROMISE_PATTERNS:
            if pattern.search(text):
                violations.append("prohibited_kyc_promise")
                break

        # 3. Seed phrase / credential requests check
        for pattern in CREDENTIAL_REQUEST_PATTERNS:
            if pattern.search(text):
                violations.append("prohibited_credential_request")
                break

        # 4. URL validation against malicious or unapproved domains
        urls = re.findall(r"https?://[^\s<>\"'()]+", text)
        url_allowlist = set(config.get("url_allowlist", [])) if config and "url_allowlist" in config else None
        effective_allowed = url_allowlist if url_allowlist is not None else DEFAULT_APPROVED_DOMAINS
        for url in urls:
            try:
                parsed = urlparse(url)
                hostname = (parsed.hostname or "").lower()
                if hostname and not any(hostname == d or hostname.endswith("." + d) for d in effective_allowed):
                    violations.append(f"unapproved_url_domain: {hostname}")
                    break
            except Exception:
                violations.append("unapproved_url_domain: parse_error")
                break

        if violations:
            logger.warning("Safety validation failed with violations: %s", violations)
            return SafetyResult(
                is_safe=False,
                violations=violations,
                safe_text=SAFE_FALLBACK_TEXT,
            )

        return SafetyResult(is_safe=True, violations=[], safe_text=text)

    except Exception as exc:
        # FAIL-CLOSED: Reject response upon ANY unexpected exception
        logger.error("Exception during safety validation (FAIL-CLOSED): %s", str(exc))
        return SafetyResult(
            is_safe=False,
            violations=[f"validation_exception: {str(exc)}"],
            safe_text=SAFE_FALLBACK_TEXT,
        )
