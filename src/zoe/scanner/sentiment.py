"""Sentiment Intelligence Engine with crypto context, sarcasm detection, and spam filtering."""

import re
import hashlib
from typing import Any, Dict, List, Set, Tuple
from zoe.scanner.models import SentimentAnalysisResult, SentimentClass
from zoe.utils.logging import get_logger

logger = get_logger("zoe.scanner.sentiment")

# Crypto contextual lexicon
POSITIVE_TERMS = {
    "bullish", "moon", "breakout", "gem", "pump", "undervalued", "massive",
    "accumulate", "partnership", "mainnet", "listing", "buy", "hodl", "ath",
    "growth", "innovative", "audited", "safu", "builder", "alpha", "utility",
    "adoption", "milestone", "legit", "clean", "surging", "institutional",
}

NEGATIVE_TERMS = {
    "bearish", "dump", "rug", "scam", "exploit", "hack", "drain", "honeypot",
    "danger", "warning", "crash", "sell", "dead", "worthless", "exit scam",
    "insider", "unlocked", "dilution", "overvalued", "lawsuit", "sec",
    "investigation", "ponzi", "fake", "fud", "shady", "blacklisted",
}

SARCASM_INDICATORS = [
    re.compile(r"\b(?:yeah\s+right|totally\s+legit|surely\s+nothing\s+bad|what\s+could\s+go\s+wrong)\b", re.IGNORECASE),
    re.compile(r"\b(?:few\s+understand\s+how\s+broke|have\s+fun\s+staying\s+poor)\b", re.IGNORECASE),
    re.compile(r"\b(?:safe\s+and\s+sound|to\s+the\s+moon\s+📉|generational\s+wealth\s+💀)\b", re.IGNORECASE),
]

SPAM_PATTERNS = [
    re.compile(r"\b(?:airdrop\s+claim|claim\s+your\s+\$|connect\s+wallet\s+now|free\s+mint|dm\s+for\s+promo)\b", re.IGNORECASE),
    re.compile(r"\b(?:telegram\s+channel\s+link|whatsapp\s+group|guaranteed\s+100x)\b", re.IGNORECASE),
    re.compile(r"(\$[A-Z]{2,10}\s+){4,}", re.IGNORECASE),  # Cashtag stuffing (e.g. $BTC $ETH $SOL $PEPE $DOGE)
]


class SentimentIntelligenceEngine:
    """Classifies sentiment across Web3 discussions with anti-spam and coordinated activity detection."""

    def __init__(self):
        self._seen_hashes: Set[str] = set()

    def filter_and_deduplicate(self, posts: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
        """Strip spam and deduplicate syndicated/copied posts."""
        clean_posts: List[Dict[str, Any]] = []
        spam_count = 0
        duplicate_count = 0
        local_hashes: Set[str] = set()

        for post in posts:
            text = post.get("text") or post.get("snippet") or post.get("content") or ""
            if not text.strip():
                continue

            # Check spam
            is_spam = False
            for sp in SPAM_PATTERNS:
                if sp.search(text):
                    is_spam = True
                    break
            if is_spam:
                spam_count += 1
                continue

            # Check duplicate content (via normalized text hash)
            normalized = re.sub(r"[^a-zA-Z0-9]", "", text.lower())[:100]
            if len(normalized) > 20:
                h = hashlib.md5(normalized.encode("utf-8")).hexdigest()
                if h in local_hashes:
                    duplicate_count += 1
                    continue
                local_hashes.add(h)

            clean_posts.append(post)

        return clean_posts, spam_count, duplicate_count

    def classify_text_sentiment(self, text: str) -> Tuple[SentimentClass, float, bool]:
        """Classify single message sentiment with sarcasm detection."""
        lower_text = text.lower()
        words = set(re.findall(r"\b[a-z]{3,15}\b", lower_text))

        pos_matches = len(words.intersection(POSITIVE_TERMS))
        neg_matches = len(words.intersection(NEGATIVE_TERMS))

        # Check sarcasm
        is_sarcastic = any(p.search(lower_text) for p in SARCASM_INDICATORS)
        if is_sarcastic:
            # Invert sentiment if sarcasm detected
            pos_matches, neg_matches = 0, max(neg_matches, 2)

        total = pos_matches + neg_matches
        if total == 0:
            return SentimentClass.NEUTRAL, 0.0, False

        score = (pos_matches - neg_matches) / total

        if pos_matches > 0 and neg_matches > 0 and abs(pos_matches - neg_matches) <= 1:
            return SentimentClass.MIXED, round(score, 2), is_sarcastic
        elif score >= 0.25:
            return SentimentClass.POSITIVE, round(score, 2), is_sarcastic
        elif score <= -0.25:
            return SentimentClass.NEGATIVE, round(score, 2), is_sarcastic
        else:
            return SentimentClass.NEUTRAL, round(score, 2), is_sarcastic

    def analyze_corpus_sentiment(
        self,
        query: str,
        posts: List[Dict[str, Any]],
    ) -> SentimentAnalysisResult:
        """Perform comprehensive sentiment intelligence across a batch of posts."""
        if not posts:
            return SentimentAnalysisResult(
                query=query,
                primary_sentiment=SentimentClass.UNCERTAIN,
                sentiment_score=0.0,
                total_samples=0,
                unique_authors=0,
                context_notes="Insufficient public data coverage to determine sentiment accurately.",
            )

        clean_posts, spam_detected, duplicate_count = self.filter_and_deduplicate(posts)

        pos_count = 0
        neg_count = 0
        neu_count = 0
        mixed_count = 0
        uncertain_count = 0
        scores: List[float] = []
        authors: Set[str] = set()

        sample_posts_output = []

        for p in clean_posts:
            text = p.get("text") or p.get("snippet") or p.get("title") or ""
            author = p.get("author") or p.get("source") or "anonymous"
            authors.add(author)

            s_class, score, was_sarcastic = self.classify_text_sentiment(text)
            scores.append(score)

            if s_class == SentimentClass.POSITIVE:
                pos_count += 1
            elif s_class == SentimentClass.NEGATIVE:
                neg_count += 1
            elif s_class == SentimentClass.MIXED:
                mixed_count += 1
            else:
                neu_count += 1

            if len(sample_posts_output) < 5:
                sample_posts_output.append({
                    "text": text[:140] + ("..." if len(text) > 140 else ""),
                    "author": author,
                    "sentiment": s_class.value,
                    "score": score,
                    "sarcasm_detected": was_sarcastic,
                })

        total_valid = len(clean_posts)
        if total_valid == 0:
            return SentimentAnalysisResult(
                query=query,
                primary_sentiment=SentimentClass.UNCERTAIN,
                sentiment_score=0.0,
                total_samples=0,
                unique_authors=0,
                spam_detected_count=spam_detected,
                context_notes="All collected samples were flagged as spam or duplicate content.",
            )

        avg_score = round(sum(scores) / total_valid, 2)

        # Determine primary sentiment
        if pos_count > (neg_count * 1.5) and pos_count >= (total_valid * 0.4):
            primary = SentimentClass.POSITIVE
        elif neg_count > (pos_count * 1.5) and neg_count >= (total_valid * 0.4):
            primary = SentimentClass.NEGATIVE
        elif mixed_count >= (total_valid * 0.3) or (pos_count > 0 and neg_count > 0 and abs(pos_count - neg_count) <= 2):
            primary = SentimentClass.MIXED
        else:
            primary = SentimentClass.NEUTRAL

        # Check for coordinated activity: high post volume but very low unique authors
        unique_authors_count = len(authors)
        ratio = (unique_authors_count / total_valid) if total_valid > 0 else 1.0
        coordinated_flag = total_valid >= 8 and ratio < 0.35

        notes = (
            f"Analyzed {total_valid} non-spam samples across {unique_authors_count} unique sources. "
            f"Filtered {spam_detected} spam and {duplicate_count} syndicated items."
        )
        if coordinated_flag:
            notes += " Warning: Coordinated activity detected (multiple duplicate messages from concentrated accounts)."

        return SentimentAnalysisResult(
            query=query,
            primary_sentiment=primary,
            sentiment_score=avg_score,
            positive_count=pos_count,
            negative_count=neg_count,
            neutral_count=neu_count,
            mixed_count=mixed_count,
            uncertain_count=uncertain_count,
            total_samples=total_valid,
            unique_authors=unique_authors_count,
            spam_detected_count=spam_detected,
            coordinated_activity_flag=coordinated_flag,
            context_notes=notes,
            sample_posts=sample_posts_output,
        )
