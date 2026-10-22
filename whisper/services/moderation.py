import re

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"@[A-Za-z0-9_]{5,}"), "link"),
    (re.compile(r"t\.me/", re.IGNORECASE), "link"),
    (re.compile(r"https?://", re.IGNORECASE), "link"),
    (re.compile(r"\bwww\.", re.IGNORECASE), "link"),
]


def check_text(text: str, forbidden_words: list[str]) -> str | None:
    """Return 'link' / 'forbidden' if the message is blocked, else None."""
    for pattern, reason in _PATTERNS:
        if pattern.search(text):
            return reason
    lowered = text.lower()
    for word in forbidden_words:
        if word and word.lower() in lowered:
            return "forbidden"
    return None
