"""Validate recipe records against the course recipe schema. Stdlib only.

    python3 scripts/validate_recipes.py [recipe.json ...]

With no arguments it validates every record under recipes/. The real
jsonschema package is not standard library, so this file implements the
small subset of JSON Schema the recipe schema actually uses: type,
required, properties, additionalProperties, items, enum, and the date
and uri formats. If the schema ever grows past that subset, this
validator fails loudly rather than passing silently.

It also enforces the fixed fallback-overlay values the 06c contract
spells out for mock recipes, so a mock record can never quietly drift
into claiming model hardware, downloads, or measured memory.

Schema location: $CWV_RECIPE_SCHEMA if set, else the course reference
tree this asset ships beside (reference/v4-byollm/).
"""

import datetime
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SUPPORTED_KEYWORDS = {
    "$schema", "title", "type", "required", "properties",
    "additionalProperties", "items", "enum", "format",
}

MOCK_OVERLAY = {
    "runtime": "Code With Vibes Orchard Mock Runtime",
    "model_id": "orchard-3b-instruct",
    "model_revision": "fixture-v1",
    "format_or_quant": None,
    "estimated_download": "0 B network; bundled fixture only",
    "hardware_class": "fallback fixture; no model hardware claim",
    "expected_memory": "mock-reported scenario metadata only",
}

TYPES = {
    "object": dict, "array": list, "string": str,
    "number": (int, float), "integer": int, "boolean": bool,
    "null": type(None),
}


def locate_schema():
    override = os.environ.get("CWV_RECIPE_SCHEMA")
    candidates = [Path(override)] if override else []
    candidates.append(ROOT.parent.parent / "reference" / "v4-byollm"
                      / "13_Recipe_Registry_Schema.json")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise SystemExit(
        "Could not find 13_Recipe_Registry_Schema.json. Point "
        "CWV_RECIPE_SCHEMA at your copy of the course recipe schema and "
        "run this again.")


def check_format(value, fmt, path, errors):
    if fmt == "date":
        try:
            datetime.date.fromisoformat(value)
        except ValueError:
            errors.append(f"{path}: '{value}' is not a YYYY-MM-DD date")
    elif fmt == "uri":
        if "://" not in value:
            errors.append(f"{path}: '{value}' is not a URI")
    else:
        errors.append(f"{path}: unsupported format '{fmt}' in schema; "
                      "extend validate_recipes.py deliberately")


def validate(instance, schema, path, errors):
    unsupported = set(schema) - SUPPORTED_KEYWORDS
    if unsupported:
        errors.append(f"{path}: schema uses unsupported keywords "
                      f"{sorted(unsupported)}; extend validate_recipes.py "
                      "deliberately")
        return

    declared = schema.get("type")
    if declared is not None:
        allowed = declared if isinstance(declared, list) else [declared]
        expected = tuple(TYPES[name] for name in allowed)
        if not isinstance(instance, expected) or (
                isinstance(instance, bool) and "boolean" not in allowed):
            errors.append(f"{path}: expected {' or '.join(allowed)}, "
                          f"got {type(instance).__name__}")
            return

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: '{instance}' not in {schema['enum']}")

    if "format" in schema and isinstance(instance, str):
        check_format(instance, schema["format"], path, errors)

    if isinstance(instance, dict):
        for name in schema.get("required", []):
            if name not in instance:
                errors.append(f"{path}: missing required field '{name}'")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for name in instance:
                if name not in properties:
                    errors.append(f"{path}: unknown field '{name}'")
        for name, value in instance.items():
            if name in properties:
                validate(value, properties[name], f"{path}.{name}", errors)

    if isinstance(instance, list) and "items" in schema:
        for position, value in enumerate(instance):
            validate(value, schema["items"], f"{path}[{position}]", errors)


def check_overlay(record, path, errors):
    for name, expected in MOCK_OVERLAY.items():
        if record.get(name) != expected:
            errors.append(
                f"{path}.{name}: mock fallback records must carry exactly "
                f"{expected!r}, found {record.get(name)!r}")
    if not record.get("privacy_notes"):
        errors.append(f"{path}.privacy_notes: must not be empty")
    if not record.get("known_failures"):
        errors.append(f"{path}.known_failures: must not be empty")
    if not record.get("reviewer"):
        errors.append(f"{path}.reviewer: a tested recipe names its reviewer")
    for position, step in enumerate(record.get("steps", [])):
        for name in ("expected_output", "stop", "undo"):
            if not str(step.get(name, "")).strip():
                errors.append(f"{path}.steps[{position}].{name}: every "
                              "command records this, even when it is "
                              "'nothing to do'")
        if "common_errors" not in step:
            errors.append(f"{path}.steps[{position}].common_errors: every "
                          "command lists its common errors, even when the "
                          "list is empty")


def check_file(path, schema, schema_only=False):
    errors = []
    raw = path.read_text()
    if "\u2014" in raw:
        errors.append(f"{path.name}: contains an em dash")
    try:
        record = json.loads(raw)
    except json.JSONDecodeError as err:
        return [f"{path.name}: not valid JSON: {err}"]
    validate(record, schema, path.stem, errors)
    if record.get("id") != path.stem:
        errors.append(f"{path.stem}.id: must match the file name")
    if not schema_only:
        check_overlay(record, path.stem, errors)
    return errors


def main(argv):
    schema = json.loads(locate_schema().read_text())
    schema_only = "--schema-only" in argv
    argv = [arg for arg in argv if arg != "--schema-only"]
    paths = ([Path(arg) for arg in argv]
             or sorted((ROOT / "recipes").glob("*.json")))
    if not paths:
        print("no recipe records found")
        return 1
    failed = False
    for path in paths:
        errors = check_file(path, schema, schema_only)
        if errors:
            failed = True
            print(f"FAIL {path.name}")
            for error in errors:
                print(f"  {error}")
        else:
            print(f"OK   {path.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
