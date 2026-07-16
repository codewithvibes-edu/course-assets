"""Tests for guardrails.validate."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardrails.redact import PIIType
from guardrails.validate import OutputValidator, ValidationFailure


def test_passes_clean_output():
    v = OutputValidator()
    result = v.check("This is a perfectly normal output.")
    assert result.passed
    assert result.failures == []


def test_min_length_fails():
    v = OutputValidator(min_length=10)
    result = v.check("short")
    assert not result.passed
    assert any(f.rule == "length_too_short" for f in result.failures)


def test_max_length_fails():
    v = OutputValidator(max_length=20)
    result = v.check("x" * 50)
    assert not result.passed
    assert any(f.rule == "length_too_long" for f in result.failures)


def test_banned_phrases_fail():
    v = OutputValidator(banned_phrases=["guaranteed refund", "we will fix"])
    result = v.check("We will fix this for you immediately.")
    assert not result.passed
    rules = {f.rule for f in result.failures}
    assert "banned_phrase" in rules


def test_banned_phrases_case_insensitive():
    v = OutputValidator(banned_phrases=["GUARANTEED"])
    result = v.check("Some guaranteed claim here.")
    assert not result.passed


def test_pii_in_output_fails():
    v = OutputValidator(banned_pii={PIIType.SSN})
    result = v.check("The SSN we have is 111-22-3333.")
    assert not result.passed
    assert any(f.rule == "pii_leak" for f in result.failures)


def test_internal_hostnames_default_pattern():
    v = OutputValidator(block_internal_hostnames=True)
    result = v.check("Database is on prod-db-1.internal at /var/log/audit.")
    assert not result.passed
    assert any(f.rule == "internal_hostname_leaked" for f in result.failures)


def test_require_json():
    v = OutputValidator(require_json=True)
    bad = v.check("Not JSON at all.")
    good = v.check('{"key": "value"}')
    assert not bad.passed
    assert good.passed


def test_custom_rule():
    def no_caps(text: str):
        if text.upper() == text and len(text) > 10:
            return ValidationFailure(rule="all_caps", detail="too shouty")
        return None

    v = OutputValidator(custom_rules=[no_caps])
    fail = v.check("THIS IS WAY TOO LOUD")
    pass_ = v.check("This is fine")
    assert not fail.passed
    assert pass_.passed


def test_multiple_failures_collected():
    v = OutputValidator(
        banned_phrases=["bad_word"],
        max_length=20,
        block_internal_hostnames=True,
    )
    result = v.check("bad_word " * 10 + " prod-db.internal")
    assert not result.passed
    rules = {f.rule for f in result.failures}
    assert "banned_phrase" in rules
    assert "length_too_long" in rules
    assert "internal_hostname_leaked" in rules
