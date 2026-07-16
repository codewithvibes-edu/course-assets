"""
Strip common boilerplate from email replies, PDFs, and HTML pages.
"""

from __future__ import annotations

import re


# Email reply chains: "On Mon, Jan 5, 2026, Alice <alice@example.com> wrote:"
_REPLY_HEADER_RE = re.compile(
    r"^On\s+\w+,?\s*\w*\s*\d+,?\s*\d{4}.+wrote:$",
    re.MULTILINE,
)
# Outlook-style: "From: Alice\nSent: Mon, ...\nTo: Bob\n..."
_OUTLOOK_HEADER_RE = re.compile(
    r"^(From|Sent|To|Cc|Subject|Date):\s*.+$",
    re.MULTILINE,
)
# Common email signatures
_SIG_PATTERNS = [
    r"--\s*\n.*",                         # standard sig delimiter
    r"\nSent from my (?:iPhone|iPad|Android|mobile).*",
    r"\nGet Outlook for (?:iOS|Android).*",
    r"\nThis email and any attachments.*confidential.*",
]


def strip_email_boilerplate(text: str) -> str:
    """
    Remove reply chains, signatures, and common email trailer boilerplate.
    Aggressive: takes the original message + signature out. Tune patterns
    if you need different behavior.
    """
    # Cut at the first reply-chain header.
    match = _REPLY_HEADER_RE.search(text)
    if match:
        text = text[: match.start()]
    # Strip Outlook-style headers anywhere in the body.
    text = _OUTLOOK_HEADER_RE.sub("", text)
    # Strip signatures from the bottom up.
    for pattern in _SIG_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()


# PDF page-header / footer artifacts: "Confidential", "Page 3 of 12",
# "Chapter 2: ..." repeating.
_PDF_PAGE_NUM_RE = re.compile(r"^Page \d+ of \d+\s*$", re.MULTILINE)
_PDF_CONFIDENTIAL_RE = re.compile(r"^(Confidential|Internal Use Only|Draft)\s*$", re.MULTILINE | re.IGNORECASE)


def strip_pdf_boilerplate(text: str) -> str:
    """
    Remove the most common PDF cross-page boilerplate: page numbers,
    'Confidential' stamps, and any line that appears more than 3 times
    (a heuristic that catches repeating headers and footers).
    """
    text = _PDF_PAGE_NUM_RE.sub("", text)
    text = _PDF_CONFIDENTIAL_RE.sub("", text)

    # Repeating-line heuristic
    lines = text.split("\n")
    counts: dict[str, int] = {}
    for line in lines:
        stripped = line.strip()
        if 5 < len(stripped) < 80:
            counts[stripped] = counts.get(stripped, 0) + 1
    repeats = {line for line, c in counts.items() if c > 3}
    cleaned = [line for line in lines if line.strip() not in repeats]
    return "\n".join(cleaned)
