"""Tests for cleaning.dedup."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cleaning.dedup import exact_dedup, fuzzy_dedup, jaccard_similarity


def test_exact_dedup_drops_identical():
    records = [
        {"id": 1, "text": "Hello world."},
        {"id": 2, "text": "Hello world."},
        {"id": 3, "text": "Goodbye world."},
    ]
    deduped = exact_dedup(records)
    assert len(deduped) == 2
    assert deduped[0]["id"] == 1
    assert deduped[1]["id"] == 3


def test_exact_dedup_normalizes_whitespace_and_case():
    records = [
        {"id": 1, "text": "Hello   World"},
        {"id": 2, "text": "hello world"},
    ]
    deduped = exact_dedup(records)
    assert len(deduped) == 1


def test_jaccard_identical():
    assert jaccard_similarity("the quick brown fox", "the quick brown fox") == 1.0


def test_jaccard_disjoint():
    assert jaccard_similarity("apple banana cherry", "dog cat fish") == 0.0


def test_jaccard_partial_overlap():
    # Two one-token edits ("the" -> "a", twice) break every 3-shingle that
    # touches an edited token: only 3 of the 11 distinct shingles survive in
    # both texts, so similarity is 3/11, not the ~0.8 token-level overlap.
    # Shingle Jaccard punishes small edits hard; that sensitivity is the point.
    sim = jaccard_similarity(
        "the quick brown fox jumps over the lazy dog",
        "a quick brown fox jumps over a lazy dog",
    )
    assert abs(sim - 3 / 11) < 1e-9
    assert 0.0 < sim < 0.5


def test_fuzzy_dedup_drops_near_dupes():
    records = [
        {"id": 1, "text": "The quick brown fox jumps over the lazy dog."},
        {"id": 2, "text": "The   quick brown fox jumps over the lazy DOG."},
        {"id": 3, "text": "Completely unrelated content here, totally different."},
    ]
    deduped = fuzzy_dedup(records, threshold=0.7)
    # The first two should collapse to one; the third is preserved.
    assert len(deduped) == 2


def test_fuzzy_dedup_keeps_longer_text():
    # Near-identical pair: the second record shares all 7 of the first
    # record's shingles and adds 2 of its own (Jaccard 7/9). Above threshold,
    # the longer record wins the tie-break.
    records = [
        {"id": 1, "text": "The quick brown fox jumps over the lazy dog."},
        {"id": 2, "text": "The quick brown fox jumps over the lazy dog. Extra tail."},
    ]
    deduped = fuzzy_dedup(records, threshold=0.5)
    assert len(deduped) == 1
    assert deduped[0]["id"] == 2


def test_fuzzy_dedup_jaccard_misses_containment():
    # A short doc fully contained in a longer one shares ALL of its shingles,
    # but the union is dominated by the longer doc, so Jaccard stays low
    # (2/7 here) and neither record is dropped. Plain Jaccard under-detects
    # containment; to catch it, divide the intersection by the SMALLER
    # shingle set instead of the union.
    records = [
        {"id": 1, "text": "Brief version of text."},
        {"id": 2, "text": "Brief version of text. With substantially more content here."},
    ]
    deduped = fuzzy_dedup(records, threshold=0.5)
    assert len(deduped) == 2
