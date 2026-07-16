"""
Output validators. Checks before delivering LLM output to a user, customer,
or downstream system. Composable: configure once, run on every output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from .redact import PATTERNS, PIIType


@dataclass
class ValidationFailure:
    rule: str
    detail: str


@dataclass
class ValidationResult:
    passed: bool
    failures: list[ValidationFailure] = field(default_factory=list)

    def fail(self, rule: str, detail: str) -> None:
        self.passed = False
        self.failures.append(ValidationFailure(rule=rule, detail=detail))


@dataclass
class OutputValidator:
    """
    Compose a validator from a set of rules. Run check() on every output
    before delivery; route failed outputs to human review or a retry path.
    """
    banned_phrases: list[str] = field(default_factory=list)
    banned_pii: set[PIIType] = field(default_factory=set)
    block_internal_hostnames: bool = False
    internal_patterns: list[str] = field(default_factory=list)
    min_length: int = 1
    max_length: int = 10_000
    require_json: bool = False
    schema_validator: Callable[[str], bool] | None = None
    custom_rules: list[Callable[[str], ValidationFailure | None]] = field(default_factory=list)

    def check(self, text: str) -> ValidationResult:
        result = ValidationResult(passed=True)

        # Length sanity
        n = len(text)
        if n < self.min_length:
            result.fail("length_too_short", f"length={n} < min={self.min_length}")
        if n > self.max_length:
            result.fail("length_too_long", f"length={n} > max={self.max_length}")

        # Banned phrases (case-insensitive substring match)
        lower = text.lower()
        for phrase in self.banned_phrases:
            if phrase.lower() in lower:
                result.fail("banned_phrase", phrase)

        # PII leakage
        for ptype in self.banned_pii:
            pattern = PATTERNS.get(ptype)
            if pattern and pattern.search(text):
                result.fail("pii_leak", ptype.value)

        # Internal hostname leakage (e.g., prod-db-1.internal, /var/log/secret)
        if self.block_internal_hostnames:
            default_internal = re.compile(
                r"\b\w+\.internal\b|/var/log/[\w/.-]+|prod[-_]\w+|stage[-_]\w+",
                re.IGNORECASE,
            )
            if default_internal.search(text):
                result.fail("internal_hostname_leaked", "matched internal pattern")
        for pattern_str in self.internal_patterns:
            try:
                if re.search(pattern_str, text):
                    result.fail("internal_pattern", pattern_str)
            except re.error as exc:
                result.fail("invalid_pattern_config", f"{pattern_str}: {exc}")

        # JSON requirement
        if self.require_json:
            import json
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                result.fail("invalid_json", str(exc))

        # Schema validator (caller-provided)
        if self.schema_validator:
            try:
                if not self.schema_validator(text):
                    result.fail("schema_invalid", "schema_validator returned False")
            except Exception as exc:
                result.fail("schema_error", str(exc))

        # Custom rules
        for rule_fn in self.custom_rules:
            failure = rule_fn(text)
            if failure is not None:
                result.fail(failure.rule, failure.detail)

        return result
