"""
Encoding fixes. Mojibake repair, smart-quote normalization, dash
normalization, whitespace collapse.
"""

from __future__ import annotations

import re
import unicodedata


_QUOTE_MAP = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "′": "'",
    "″": '"',
    "´": "'",
    "`": "'",
}

_DASH_MAP = {
    "–": "-",
    "—": "-",
    "−": "-",
    "―": "-",
}

_OTHER_MAP = {
    "…": "...",
    " ": " ",
    "​": "",
    "﻿": "",
}

_WHITESPACE_RE = re.compile(r"[ \t]+")
_NEWLINE_RE = re.compile(r"\n{3,}")


def fix_mojibake(text: str) -> str:
    """
    Repair common mojibake (â€™ -> ', etc.) using ftfy when available.
    Falls through unchanged if ftfy is not installed.
    """
    try:
        import ftfy
    except ImportError:
        return text
    return ftfy.fix_text(text)


def normalize_punctuation(text: str) -> str:
    """Replace smart quotes, em/en dashes, ellipsis chars, NBSP with ASCII."""
    out = text
    for src, dst in _QUOTE_MAP.items():
        out = out.replace(src, dst)
    for src, dst in _DASH_MAP.items():
        out = out.replace(src, dst)
    for src, dst in _OTHER_MAP.items():
        out = out.replace(src, dst)
    return out


def normalize_text(text: str) -> str:
    """
    The kitchen sink. Apply mojibake fix + Unicode NFKC normalize +
    punctuation map + whitespace collapse. Idempotent: running twice is
    a no-op.
    """
    text = fix_mojibake(text)
    text = unicodedata.normalize("NFKC", text)
    text = normalize_punctuation(text)
    text = _WHITESPACE_RE.sub(" ", text)
    text = _NEWLINE_RE.sub("\n\n", text)
    return text.strip()
