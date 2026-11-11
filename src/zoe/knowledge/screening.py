"""Prompt-injection screening for knowledge chunks."""

import re
from typing import List

PROMPT_INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\b", re.IGNORECASE),
    re.compile(r"forget\s+(?:all\s+)?prior\s+instructions", re.IGNORECASE),
    re.compile(r"bypass\s+safety\s+filters?", re.IGNORECASE),
    re.compile(r"developer\s+mode\s+enabled", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
]


def screen_chunk(text: str) -> bool:
    """Return True if prompt injection phrases are detected in text, False otherwise."""
    if not text:
        return False

    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False

