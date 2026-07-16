"""Tests for the deterministic check dispatchers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval_harness.deterministic import run_deterministic_check


def test_exact_match_pass():
    score = run_deterministic_check({"type": "exact_match", "expected": "yes"}, "yes")
    assert score.passed


def test_exact_match_fail():
    score = run_deterministic_check({"type": "exact_match", "expected": "yes"}, "no")
    assert not score.passed
    assert "expected" in score.detail


def test_regex_match_pass():
    score = run_deterministic_check(
        {"type": "regex_match", "pattern": r"^\d{3}-\d{4}$"},
        "555-1234",
    )
    assert score.passed


def test_regex_must_not_match():
    score = run_deterministic_check(
        {"type": "regex_match", "pattern": r"\bemail\b", "must_not_match": True},
        "this output mentions email which is not allowed",
    )
    assert not score.passed


def test_length_min():
    score = run_deterministic_check({"type": "length", "min": 10}, "short")
    assert not score.passed


def test_length_max():
    score = run_deterministic_check({"type": "length", "max": 5}, "way too long")
    assert not score.passed


def test_length_within_range():
    score = run_deterministic_check({"type": "length", "min": 3, "max": 10}, "hello")
    assert score.passed


def test_field_value_pass():
    output = json.dumps({"category": "billing", "urgency": "high"})
    score = run_deterministic_check(
        {"type": "field_value", "field": "category", "expected": "billing"}, output
    )
    assert score.passed


def test_field_value_fail():
    output = json.dumps({"category": "feedback"})
    score = run_deterministic_check(
        {"type": "field_value", "field": "category", "expected": "billing"}, output
    )
    assert not score.passed


def test_field_value_nested_path():
    output = json.dumps({"meta": {"info": {"category": "billing"}}})
    score = run_deterministic_check(
        {"type": "field_value", "field": "meta.info.category", "expected": "billing"},
        output,
    )
    assert score.passed


def test_field_in_set_pass():
    output = json.dumps({"urgency": "high"})
    score = run_deterministic_check(
        {"type": "field_in_set", "field": "urgency", "allowed": ["medium", "high"]},
        output,
    )
    assert score.passed


def test_field_in_set_fail():
    output = json.dumps({"urgency": "low"})
    score = run_deterministic_check(
        {"type": "field_in_set", "field": "urgency", "allowed": ["medium", "high"]},
        output,
    )
    assert not score.passed


def test_no_banned_phrase_pass():
    score = run_deterministic_check(
        {"type": "no_banned_phrase", "phrases": ["guaranteed", "promise"]},
        "This is a normal output.",
    )
    assert score.passed


def test_no_banned_phrase_fail():
    score = run_deterministic_check(
        {"type": "no_banned_phrase", "phrases": ["guaranteed"]},
        "We GUARANTEED this would work.",
    )
    assert not score.passed


def test_unknown_check_type():
    score = run_deterministic_check({"type": "no_such_check"}, "anything")
    assert not score.passed
    assert "unknown_check" in score.rule


def test_field_value_invalid_json():
    score = run_deterministic_check(
        {"type": "field_value", "field": "category", "expected": "x"}, "not json"
    )
    assert not score.passed
    assert "JSON" in score.detail
