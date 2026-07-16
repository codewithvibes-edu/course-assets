"""
HTML cleanup. Strip tags; extract main content from messy HTML.
"""

from __future__ import annotations

import re


_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
_STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html_tags(html: str) -> str:
    """
    Remove HTML tags and script/style blocks. Returns plain text with
    whitespace collapsed. Suitable for short HTML; for full pages use
    extract_main_content() instead.
    """
    text = _SCRIPT_RE.sub(" ", html)
    text = _STYLE_RE.sub(" ", text)
    text = _COMMENT_RE.sub(" ", text)
    text = _TAG_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def extract_main_content(html: str) -> str:
    """
    Extract the main article content from a full HTML page using
    trafilatura. Falls back to strip_html_tags if trafilatura is not
    installed or returns nothing.
    """
    try:
        import trafilatura
    except ImportError:
        return strip_html_tags(html)

    extracted = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    )
    if extracted:
        return extracted
    return strip_html_tags(html)
