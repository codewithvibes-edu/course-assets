"""
Deterministic eval checks. Cheap, fast, free. Run on every prompt change.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .types import Score, ScoreSource


def run_deterministic_check(check: dict[str, Any], output: str) -> Score:
    """
    Dispatch a single deterministic check against the output.
    `check` is a dict from the suite YAML; the 'type' key drives dispatch.
    """
    check_type = check.get("type", "")
    handler = _HANDLERS.get(check_type)
    if handler is None:
        return Score(
            source=ScoreSource.DETERMINISTIC,
            rule=f"unknown_check:{check_type}",
            passed=False,
            detail=f"no handler for check type '{check_type}'",
        )
    return handler(check, output)


def _exact_match(check: dict[str, Any], output: str) -> Score:
    expected = check.get("expected", "")
    passed = output.strip() == str(expected).strip()
    return Score(
        source=ScoreSource.DETERMINISTIC,
        rule="exact_match",
        passed=passed,
        detail="" if passed else f"expected {expected!r}",
    )


def _regex_match(check: dict[str, Any], output: str) -> Score:
    pattern = check.get("pattern", "")
    flags = re.IGNORECASE if check.get("ignore_case") else 0
    try:
        compiled = re.compile(pattern, flags)
    except re.error as exc:
        return Score(
            source=ScoreSource.DETERMINISTIC,
            rule="regex_match",
            passed=False,
            detail=f"invalid pattern: {exc}",
        )
    passed = bool(compiled.search(output))
    if check.get("must_not_match"):
        passed = not passed
    return Score(
        source=ScoreSource.DETERMINISTIC,
        rule="regex_match",
        passed=passed,
        detail="" if passed else f"pattern {pattern!r} {'matched' if check.get('must_not_match') else 'did not match'}",
    )


def _length(check: dict[str, Any], output: str) -> Score:
    n = len(output)
    min_len = check.get("min", 0)
    max_len = check.get("max", float("inf"))
    if n < min_len:
        return Score(
            source=ScoreSource.DETERMINISTIC,
            rule="length",
            passed=False,
            detail=f"length={n} < min={min_len}",
        )
    if n > max_len:
        return Score(
            source=ScoreSource.DETERMINISTIC,
            rule="length",
            passed=False,
            detail=f"length={n} > max={max_len}",
        )
    return Score(source=ScoreSource.DETERMINISTIC, rule="length", passed=True)


def _json_schema(check: dict[str, Any], output: str) -> Score:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return Score(
            source=ScoreSource.DETERMINISTIC,
            rule="json_schema",
            passed=False,
            detail="jsonschema not installed",
        )
    schema_path = check.get("schema_path")
    if schema_path:
        try:
            schema = json.loads(Path(schema_path).read_text())
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            return Score(
                source=ScoreSource.DETERMINISTIC,
                rule="json_schema",
                passed=False,
                detail=f"could not load schema: {exc}",
            )
    elif "schema" in check:
        schema = check["schema"]
    else:
        return Score(
            source=ScoreSource.DETERMINISTIC,
            rule="json_schema",
            passed=False,
            detail="no schema_path or inline schema",
        )

    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as exc:
        return Score(
            source=ScoreSource.DETERMINISTIC,
            rule="json_schema",
            passed=False,
            detail=f"output is not valid JSON: {exc}",
        )

    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(parsed))
    if errors:
        first = errors[0]
        return Score(
            source=ScoreSource.DETERMINISTIC,
            rule="json_schema",
            passed=False,
            detail=f"{first.message} at {list(first.absolute_path)}",
        )
    return Score(source=ScoreSource.DETERMINISTIC, rule="json_schema", passed=True)


def _field_value(check: dict[str, Any], output: str) -> Score:
    field_name = check.get("field", "")
    expected = check.get("expected")
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as exc:
        return Score(
            source=ScoreSource.DETERMINISTIC,
            rule="field_value",
            passed=False,
            detail=f"output is not JSON: {exc}",
        )
    actual = _get_nested(parsed, field_name)
    passed = actual == expected
    return Score(
        source=ScoreSource.DETERMINISTIC,
        rule="field_value",
        passed=passed,
        detail="" if passed else f"{field_name}={actual!r}, expected {expected!r}",
    )


def _field_in_set(check: dict[str, Any], output: str) -> Score:
    field_name = check.get("field", "")
    allowed = set(check.get("allowed", []))
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return Score(
            source=ScoreSource.DETERMINISTIC,
            rule="field_in_set",
            passed=False,
            detail="output is not JSON",
        )
    actual = _get_nested(parsed, field_name)
    passed = actual in allowed
    return Score(
        source=ScoreSource.DETERMINISTIC,
        rule="field_in_set",
        passed=passed,
        detail="" if passed else f"{field_name}={actual!r} not in {sorted(allowed)}",
    )


def _no_banned_phrase(check: dict[str, Any], output: str) -> Score:
    banned = check.get("phrases", [])
    lower = output.lower()
    matches = [p for p in banned if p.lower() in lower]
    return Score(
        source=ScoreSource.DETERMINISTIC,
        rule="no_banned_phrase",
        passed=not matches,
        detail="" if not matches else f"matched: {matches}",
    )


def _get_nested(obj: Any, path: str) -> Any:
    """Get a field by dot-path: 'a.b.c'."""
    parts = path.split(".") if path else []
    cursor = obj
    for part in parts:
        if isinstance(cursor, dict) and part in cursor:
            cursor = cursor[part]
        else:
            return None
    return cursor


_HANDLERS = {
    "exact_match": _exact_match,
    "regex_match": _regex_match,
    "length": _length,
    "json_schema": _json_schema,
    "field_value": _field_value,
    "field_in_set": _field_in_set,
    "no_banned_phrase": _no_banned_phrase,
}
