"""Tests for guardrails.redact."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardrails.redact import PIIType, redact, restore


def test_credit_card_redacted():
    text = "Charge to 4111 1111 1111 1111 please."
    result = redact(text, types={PIIType.CREDIT_CARD})
    assert "4111" not in result.text
    assert len(result.redactions) == 1
    assert result.redactions[0].type == PIIType.CREDIT_CARD


def test_credit_card_not_redacted_if_invalid_luhn():
    # 13-digit run that fails Luhn
    text = "Order number 1234567890123 is ready."
    result = redact(text, types={PIIType.CREDIT_CARD})
    assert "1234567890123" in result.text
    assert result.redactions == []


def test_ssn_redacted():
    text = "SSN: 123-45-6789 on file."
    result = redact(text)
    assert "123-45-6789" not in result.text


def test_email_redacted():
    text = "Contact: alice@example.com and bob@example.com"
    result = redact(text)
    assert "@example.com" not in result.text
    assert len(result.redactions) == 2


def test_phone_redacted():
    text = "Call 555-123-4567 or (212) 867-5309."
    result = redact(text)
    types = {r.type for r in result.redactions}
    assert PIIType.PHONE in types


def test_ip_address_redacted():
    text = "Server at 10.0.0.1 had an issue. IPv4 addresses like 192.168.1.100 too."
    result = redact(text)
    types = {r.type for r in result.redactions}
    assert PIIType.IP_ADDRESS in types


def test_api_key_redacted():
    text = "Use sk_test_abcdef123456789012345 for testing."
    result = redact(text)
    types = {r.type for r in result.redactions}
    assert PIIType.API_KEY in types


def test_restore_round_trips():
    original = "Email me at alice@example.com any time."
    result = redact(original)
    restored = restore(result.text, result.mapping)
    assert restored == original


def test_no_mapping_when_preserve_false():
    text = "Email alice@example.com"
    result = redact(text, preserve_mapping=False)
    assert result.mapping == {}
    # Cannot restore
    restored = restore(result.text, result.mapping)
    assert "alice@example.com" not in restored


def test_overlapping_patterns_handled_in_priority_order():
    # Phone-shaped substring inside a credit-card-shaped string should
    # not double-redact.
    text = "Card: 4111-1111-1111-1111"
    result = redact(text)
    # One redaction (the credit card), not two
    assert len(result.redactions) == 1
