"""Text sanitizer cleaning unnecessary characters, markdown artifacts, and non-standard Unicode."""

import re


def clean_unnecessary_characters(text: str) -> str:
    """Clean text so it reads as pure, crisp, natural human chat on Telegram.
    
    Removes:
    - Non-standard Unicode spaces (NBSP, narrow NBSP, zero-width spaces)
    - Non-standard hyphens and em-dashes (e.g. \\u2011, \\u2014)
    - Smart/curly quotes and backticks
    - Markdown bold/italic asterisks (* and **)
    - Markdown headers (###)
    - List bullets (- , * , • )
    - Redundant whitespace and blank lines
    """
    if not text:
        return ""

    # 1. Normalize non-standard Unicode whitespace and zero-width characters
    text = re.sub(r"[\u00a0\u202f\u2000-\u200a]", " ", text)
    text = re.sub(r"[\u200b-\u200d\ufeff]", "", text)

    # 2. Normalize hyphens, dashes, and bars
    text = text.replace("\u2011", "-")  # non-breaking hyphen
    text = text.replace("—", ", ")       # em-dash
    text = text.replace("–", "-")        # en-dash
    text = text.replace("―", "-")        # horizontal bar

    # 3. Normalize smart quotes and apostrophes to standard ASCII
    text = text.replace("‘", "'").replace("’", "'").replace("`", "'")
    text = text.replace("“", '"').replace("”", '"')

    # 4. Remove markdown bold/italic asterisks
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = text.replace("*", "")
    text = text.replace("~", "")

    # 5. Remove markdown headers (e.g. ### Header -> Header)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)

    # 6. Remove list bullets at the beginning of lines or after punctuation (e.g. - item -> item, . - item -> . item)
    text = re.sub(r"(?:^|(?<=[.:;?!]))\s*[\-•*]\s+", " ", text, flags=re.MULTILINE)

    # 7. Clean broken/stiff citation prefixes like "According to official project records, ." or "According to official project records."
    text = re.sub(
        r"^(?:According\s+to\s+official\s+project\s+records|Based\s+on\s+official\s+documentation)\s*(?:,\s*\.|\.|\s*,)\s*",
        "Based on the official docs, ",
        text,
        flags=re.IGNORECASE,
    )

    # 8. Normalize spaces and linebreaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    # 9. Fix spacing around slashes, hyphens, and currency symbols
    text = re.sub(r"([A-Za-z0-9_])\s*/\s*([A-Za-z0-9_])", r"\1/\2", text)
    text = re.sub(r"([A-Za-z0-9_])\s*-\s*([A-Za-z0-9_])", r"\1-\2", text)
    text = re.sub(r"(\$|€|£)\s+([A-Za-z0-9_])", r"\1\2", text)
    text = re.sub(r"\s+([²³°%])", r"\1", text)
    text = re.sub(r"\s*,\s*\.", ".", text)
    text = re.sub(r"\s+([,.:;?!])", r"\1", text)

    # 10. Strict Ban on AI Excuses, Text Box Statements, and Limitation Claims
    ai_excuses = [
        r"(?i)\b(?:i\s+cannot\s+see\s+the\s+group|i\s+am\s+a\s+text\s+box|i\s+have\s+a\s+(?:hard\s+)?technical\s+limitation|i\s+cannot\s+see\s+the\s+live\s+(?:group\s+chat\s+)?feed|i(?:\s+do\s+not|\s*\'?m\s+unable\s+to|\s+cannot)\s+see\s+the\s+live\s+feed)\b[.,]?",
        r"(?i)\bplease\s+(?:copy\s+and\s+paste|paste)\s+(?:the\s+)?(?:text|question|message|it)\b[.,]?",
    ]
    for pattern in ai_excuses:
        text = re.sub(pattern, "", text)

    return text.strip()

