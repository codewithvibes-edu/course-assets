"""
PII detection + redaction with restoration support.

Pattern coverage:
- Credit card numbers (Luhn-validated where possible)
- US Social Security Numbers
- Email addresses
- US phone numbers
- IP addresses
- API keys (heuristic: long alphanumeric strings near "key" or "token")

For high-stakes contexts (PHI, EU PII, etc.), use a dedicated PII detector
like Microsoft Presidio. This module covers the common cases for general-
purpose LLM input/output sanitization.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from enum import Enum


class PIIType(str, Enum):
    CREDIT_CARD = "credit_card"
    SSN = "ssn"
    EMAIL = "email"
    PHONE = "phone"
    IP_ADDRESS = "ip_address"
    API_KEY = "api_key"


# Patterns are deliberately conservative. False positives are costly
# (data lost in logs); false negatives are fixable (a missed pattern
# can be added later). Add domain-specific patterns at the call site.
PATTERNS: dict[PIIType, re.Pattern[str]] = {
    PIIType.CREDIT_CARD: re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    PIIType.SSN: re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    PIIType.EMAIL: re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    PIIType.PHONE: re.compile(
        r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b"
    ),
    PIIType.IP_ADDRESS: re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
    ),
    PIIType.API_KEY: re.compile(
        r"\b(?:sk|pk|rk|api|key|token)[-_][A-Za-z0-9]{16,}\b",
        re.IGNORECASE,
    ),
}


@dataclass
class Redaction:
    type: PIIType
    placeholder: str
    start: int
    end: int


@dataclass
class RedactionResult:
    text: str
    redactions: list[Redaction] = field(default_factory=list)
    # mapping placeholder -> original. ONLY use restore() to put values back;
    # never log the mapping.
    mapping: dict[str, str] = field(default_factory=dict)


def _luhn_valid(digits: str) -> bool:
    """Luhn check for credit card numbers. Filters most false positives."""
    nums = [int(d) for d in digits if d.isdigit()]
    if len(nums) < 13 or len(nums) > 19:
        return False
    total = 0
    parity = len(nums) % 2
    for i, n in enumerate(nums):
        if i % 2 == parity:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def redact(
    text: str,
    types: set[PIIType] | None = None,
    *,
    preserve_mapping: bool = True,
) -> RedactionResult:
    """
    Detect and redact PII. Returns a RedactionResult containing the
    redacted text, the list of redactions, and a placeholder->original
    mapping for restoration if needed.

    types: which PII categories to redact. Default: all.
    preserve_mapping: if False, drop the original values entirely (no restore).
    """
    if types is None:
        types = set(PIIType)

    redactions: list[Redaction] = []
    mapping: dict[str, str] = {}

    # Process types in priority order so credit card matches before phone matches
    # on long digit runs.
    priority = [
        PIIType.CREDIT_CARD,
        PIIType.SSN,
        PIIType.IP_ADDRESS,
        PIIType.PHONE,
        PIIType.EMAIL,
        PIIType.API_KEY,
    ]
    pieces: list[tuple[int, int, PIIType, str]] = []
    occupied: list[tuple[int, int]] = []

    def overlaps(start: int, end: int) -> bool:
        for s, e in occupied:
            if start < e and end > s:
                return True
        return False

    for ptype in priority:
        if ptype not in types:
            continue
        pattern = PATTERNS[ptype]
        for match in pattern.finditer(text):
            start, end = match.span()
            if overlaps(start, end):
                continue
            value = match.group()
            if ptype == PIIType.CREDIT_CARD and not _luhn_valid(value):
                continue
            pieces.append((start, end, ptype, value))
            occupied.append((start, end))

    pieces.sort(key=lambda p: p[0])

    out_parts: list[str] = []
    cursor = 0
    for start, end, ptype, value in pieces:
        out_parts.append(text[cursor:start])
        token = f"<REDACTED_{ptype.value.upper()}_{uuid.uuid4().hex[:8]}>"
        out_parts.append(token)
        redactions.append(Redaction(type=ptype, placeholder=token, start=start, end=end))
        if preserve_mapping:
            mapping[token] = value
        cursor = end
    out_parts.append(text[cursor:])

    return RedactionResult(
        text="".join(out_parts),
        redactions=redactions,
        mapping=mapping if preserve_mapping else {},
    )


def restore(text: str, mapping: dict[str, str]) -> str:
    """
    Replace placeholders with their original values using the mapping
    from a prior redact() call. Use sparingly: restoration brings PII
    back into the data flow.
    """
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text
