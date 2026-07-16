"""Shared types for the eval harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ScoreSource(str, Enum):
    DETERMINISTIC = "deterministic"
    MODEL_GRADED = "model_graded"
    HUMAN = "human"


@dataclass
class Score:
    source: ScoreSource
    rule: str               # what was checked (e.g., "json_schema", "tone_rubric")
    passed: bool
    value: float | None = None  # 0.0 to 1.0 where applicable
    detail: str = ""


@dataclass
class EvalCase:
    id: str
    input: str
    deterministic: list[dict[str, Any]] = field(default_factory=list)
    model_graded: list[dict[str, Any]] = field(default_factory=list)
    human_review_sample_rate: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    case_id: str
    output: str
    scores: list[Score]
    passed: bool
    duration_ms: int
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "output": self.output,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "scores": [
                {
                    "source": s.source.value,
                    "rule": s.rule,
                    "passed": s.passed,
                    "value": s.value,
                    "detail": s.detail,
                }
                for s in self.scores
            ],
        }


@dataclass
class SuiteResult:
    suite_name: str
    started_at: str
    finished_at: str
    results: list[EvalResult]

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.passed) / len(self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite_name": self.suite_name,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "pass_rate": round(self.pass_rate, 4),
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "results": [r.to_dict() for r in self.results],
        }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
