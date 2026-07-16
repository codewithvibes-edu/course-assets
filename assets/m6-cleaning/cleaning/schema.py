"""
Pydantic-based schema enforcement at the cleaning boundary. Records
that don't match the schema are rejected before they reach storage,
which means downstream code never has to defend against malformed input.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from pydantic import BaseModel, Field, ValidationError, field_validator


class EnforcedRecord(BaseModel):
    """
    Reference enforced shape. Subclass or replace to fit your domain.
    The fields here cover the common cases: a stable id, the source
    pointers, the text content, structured metadata, and lineage.
    """

    id: str = Field(min_length=1, max_length=200)
    source_url: str | None = None
    source_name: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=10)
    title: str | None = Field(default=None, max_length=500)
    language: str = Field(default="en", pattern=r"^[a-z]{2,3}(-[A-Z]{2})?$")
    word_count: int | None = Field(default=None, ge=0)
    ingested_at: datetime
    cleaning_version: str = Field(default="1.0.0")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def must_have_alphabetic_content(cls, v: str) -> str:
        # Reject text that is mostly non-alphabetic (numbers, symbols, etc.).
        # Catches OCR garbage and binary-extracted noise.
        alpha = sum(c.isalpha() for c in v)
        if alpha / max(len(v), 1) < 0.3:
            raise ValueError("text has insufficient alphabetic content")
        return v


def validate_records(
    raw_records: Iterable[dict],
    *,
    model: type[BaseModel] = EnforcedRecord,
    on_error: str = "drop",
) -> tuple[list[BaseModel], list[dict]]:
    """
    Validate a stream of raw record dicts.

    Returns (valid, rejected). Rejected entries include the original
    record and the validation error.

    on_error:
      - 'drop' (default): drop and report rejected; keep going.
      - 'raise': raise on first failure.
    """
    valid: list[BaseModel] = []
    rejected: list[dict] = []
    for raw in raw_records:
        try:
            valid.append(model.model_validate(raw))
        except ValidationError as exc:
            if on_error == "raise":
                raise
            rejected.append({"record": raw, "error": str(exc)})
    return valid, rejected
