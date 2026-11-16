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
    "onelovesailingcoin.com",
    "tiktok.com",
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

# Inbound Scam & Phishing Detection Patterns
INBOUND_SCAM_LINK_KEYWORDS = re.compile(
    r"(?:airdrop|claim|freemint|presale|whitelist|bonus[-_]?drop|drainer|wallet[-_]?sync|rectif|dapp[-_]?resolver|gift[-_]?tokens|giveaway)",
    re.IGNORECASE,
)

SUSPICIOUS_SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "is.gd", "cutt.ly", "rb.gy", "shorturl.at", "grabify.link"
}

PHISHING_CREDENTIAL_PATTERNS = [
    re.compile(r"\b(?:seed\s+phrase|private\s+key|mnemonic(?:\s+phrase)?|recovery\s+phrase)\b", re.IGNORECASE),
    re.compile(r"\b(?:enter|provide|share|input|send)\s+(?:your\s+)?(?:12|24)\s+words\b", re.IGNORECASE),
    re.compile(r"\b(?:sync|validate|rectify|authenticate|connect)\s+(?:your\s+)?wallet\b", re.IGNORECASE),
    re.compile(r"\b(?:dapp\s+sync|wallet\s+node|manual\s+synchronization)\b", re.IGNORECASE),
]

FAKE_ADMIN_IMPERSONATION_PATTERNS = [
    re.compile(r"\b(?:official|telegram|admin|customer|support)\s+(?:support|team|mod|agent|desk|representative)\b", re.IGNORECASE),
    re.compile(r"\b(?:dm\s+(?:me|our\s+team|support|admin)|send\s+(?:me\s+)?a\s+dm|inbox\s+me|message\s+(?:me\s+)?privately|contact\s+(?:our\s+)?support)\b", re.IGNORECASE),
    re.compile(r"\b(?:i\s+am\s+(?:the\s+)?admin|admin\s+here|mod\s+here|support\s+desk\s+here)\b", re.IGNORECASE),
    re.compile(r"\b(?:kindly\s+dm|reach\s+out\s+in\s+private|text\s+me\s+directly)\b", re.IGNORECASE),
]

SCAM_GIVEAWAY_PATTERNS = [
    re.compile(r"\b(?:send\s+\d+\s*(?:sol|eth|btc)\s+(?:to\s+get|receive)\s+\d+)\b", re.IGNORECASE),
    re.compile(r"\b(?:claim\s+(?:your\s+)?\d+[\d,]*\s*(?:usdt|usdc|sol|tokens?)\s+(?:now|free))\b", re.IGNORECASE),
]

SAFE_FALLBACK_TEXT = "I'm not sure about that, better check the official announcements."


@dataclass(frozen=True)
class InboundSafetyResult:
    is_safe: bool
    is_scam: bool
    violations: List[str]
    violation_type: Optional[str] = None  # "scam_link", "phishing", "fake_admin", "credential_theft"
    reason: Optional[str] = None


def validate_inbound_message(
    text: str,
    approved_domains: Optional[set] = None,
) -> InboundSafetyResult:
    """Evaluate an incoming community message for scam links, phishing, or fake admin impersonation."""
    if not text or not text.strip():
        return InboundSafetyResult(is_safe=True, is_scam=False, violations=[])

    clean = text.strip()
    violations: List[str] = []

    # 1. Phishing & Credential Theft
    for pattern in PHISHING_CREDENTIAL_PATTERNS:
        m = pattern.search(clean)
        if m:
            violations.append(f"phishing_credentials:{m.group(0)}")
            return InboundSafetyResult(
                is_safe=False,
                is_scam=True,
                violations=violations,
                violation_type="phishing",
                reason=f"Phishing or credential theft attempt: '{m.group(0)}'",
            )

    # 2. Fake Admin Impersonation
    for pattern in FAKE_ADMIN_IMPERSONATION_PATTERNS:
        m = pattern.search(clean)
        if m:
            violations.append(f"fake_admin:{m.group(0)}")
            return InboundSafetyResult(
                is_safe=False,
                is_scam=True,
                violations=violations,
                violation_type="fake_admin",
                reason=f"Fake admin impersonation: '{m.group(0)}'",
            )

    # 3. Scam Giveaway / Doubler
    for pattern in SCAM_GIVEAWAY_PATTERNS:
        m = pattern.search(clean)
        if m:
            violations.append(f"scam_giveaway:{m.group(0)}")
            return InboundSafetyResult(
                is_safe=False,
                is_scam=True,
                violations=violations,
                violation_type="scam_link",
                reason=f"Scam giveaway detected: '{m.group(0)}'",
            )

    # 4. Scam Link and URL Inspection
    urls = re.findall(r"https?://[^\s<>\"'()]+", clean)
    tg_links = re.findall(r"\b(?:t\.me|telegram\.me)/[^\s<>\"'()]+", clean)
    for tgl in tg_links:
        full_tgl = f"https://{tgl}" if not tgl.startswith("http") else tgl
        urls.append(full_tgl)

    for u in urls:
        try:
            parsed = urlparse(u if "://" in u else f"https://{u}")
            netloc = (parsed.netloc or "").lower().split(":")[0]
            if netloc.startswith("www."):
                netloc = netloc[4:]

            # Shorteners
            if netloc in SUSPICIOUS_SHORTENER_DOMAINS:
                violations.append(f"suspicious_shortener:{netloc}")
                return InboundSafetyResult(
                    is_safe=False,
                    is_scam=True,
                    violations=violations,
                    violation_type="scam_link",
                    reason=f"Suspicious URL shortener detected: {netloc}",
                )

            # Scam keywords in URL (airdrop, claim, etc.)
            if INBOUND_SCAM_LINK_KEYWORDS.search(u):
                violations.append(f"scam_keyword_in_url:{u}")
                return InboundSafetyResult(
                    is_safe=False,
                    is_scam=True,
                    violations=violations,
                    violation_type="scam_link",
                    reason=f"Scam keyword in unverified URL: {u}",
                )

            # Phishing domains mimicking wallets/exchanges
            if any(brand in netloc for brand in ["phantom-", "metamask-", "solana-claim", "raydium-claim"]):
                violations.append(f"phishing_domain:{netloc}")
                return InboundSafetyResult(
                    is_safe=False,
                    is_scam=True,
                    violations=violations,
                    violation_type="phishing",
                    reason=f"Known phishing domain pattern: {netloc}",
                )
        except Exception:
            pass

    return InboundSafetyResult(is_safe=True, is_scam=False, violations=[])


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
