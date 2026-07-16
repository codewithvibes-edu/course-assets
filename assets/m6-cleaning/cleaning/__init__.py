"""Cleaning + dedup + schema enforcement utilities."""

from .html import extract_main_content, strip_html_tags
from .encoding import normalize_text, fix_mojibake, normalize_punctuation
from .boilerplate import strip_email_boilerplate, strip_pdf_boilerplate
from .dedup import exact_dedup, fuzzy_dedup, jaccard_similarity
from .schema import EnforcedRecord, validate_records

__all__ = [
    "extract_main_content",
    "strip_html_tags",
    "normalize_text",
    "fix_mojibake",
    "normalize_punctuation",
    "strip_email_boilerplate",
    "strip_pdf_boilerplate",
    "exact_dedup",
    "fuzzy_dedup",
    "jaccard_similarity",
    "EnforcedRecord",
    "validate_records",
]
