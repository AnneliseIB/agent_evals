from __future__ import annotations

import re
import unicodedata

_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")


def slugify(text: str, separator: str = "-") -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return _NON_ALPHANUMERIC.sub(separator, ascii_text.lower()).strip(separator)


def truncate(text: str, limit: int, suffix: str = "...") -> str:
    if limit < len(suffix):
        raise ValueError("limit must be at least the length of suffix")
    if len(text) <= limit:
        return text
    return text[: limit - len(suffix)].rstrip() + suffix


def word_count(text: str) -> int:
    return len(text.split())
