"""Suite loader + orchestration."""

from __future__ import annotations

import importlib
import time
from pathlib import Path
from typing import Any, Callable

import yaml

from .deterministic import run_deterministic_check
from .model_graded import ModelGrader
from .types import EvalCase, EvalResult, Score, SuiteResult, now_iso


def load_suite(path: Path) -> tuple[dict[str, Any], list[EvalCase]]:
    """Load a suite YAML and parse cases."""
    raw = yaml.safe_load(path.read_text())
    cases = [
        EvalCase(
            id=c["id"],
            input=c["input"],
            deterministic=c.get("deterministic", []),
            model_graded=c.get("model_graded", []),
            human_review_sample_rate=c.get("human_review_sample_rate", 0.0),
            metadata=c.get("metadata", {}),
        )
        for c in raw.get("cases", [])
    ]
    return raw, cases


def _resolve_prompt_fn(module_name: str, fn_name: str) -> Callable[[str], str]:
    """Import the prompt function under test."""
    module = importlib.import_module(module_name)
    fn = getattr(module, fn_name)
    if not callable(fn):
        raise TypeError(f"{module_name}.{fn_name} is not callable")
    return fn


def run_suite(
    suite_path: Path,
    *,
    skip_model_graded: bool = False,
    grader_model: str = "claude-opus-4-7",
) -> SuiteResult:
    suite_config, cases = load_suite(suite_path)
    suite_name = suite_config.get("suite_name", suite_path.stem)
    prompt_module = suite_config["prompt_module"]
    prompt_function = suite_config.get("prompt_function", "run")

    prompt_fn = _resolve_prompt_fn(prompt_module, prompt_function)
    grader = None if skip_model_graded else ModelGrader(model=grader_model)

    started_at = now_iso()
    results: list[EvalResult] = []

    for case in cases:
        result = _run_one_case(case, prompt_fn, grader)
        results.append(result)

    finished_at = now_iso()
    return SuiteResult(
        suite_name=suite_name,
        started_at=started_at,
        finished_at=finished_at,
        results=results,
    )


def _run_one_case(
    case: EvalCase,
    prompt_fn: Callable[[str], str],
    grader: ModelGrader | None,
) -> EvalResult:
    t0 = time.perf_counter()
    error: str | None = None
    output = ""
    try:
        output = prompt_fn(case.input)
    except Exception as exc:
        error = f"prompt_fn raised: {exc}"

    scores: list[Score] = []
    if not error:
        for check in case.deterministic:
            scores.append(run_deterministic_check(check, output))
        if grader:
            for grade_spec in case.model_graded:
                rubric = grade_spec.get("rubric", "")
                threshold = grade_spec.get("passing_threshold", 0.8)
                scores.append(
                    grader.grade(output, rubric, case.input, passing_threshold=threshold)
                )

    duration_ms = int((time.perf_counter() - t0) * 1000)
    passed = bool(scores) and all(s.passed for s in scores) and error is None
    return EvalResult(
        case_id=case.id,
        output=output,
        scores=scores,
        passed=passed,
        duration_ms=duration_ms,
        error=error,
    )
