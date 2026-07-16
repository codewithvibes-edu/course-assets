"""
End-to-end example for the content pipeline capstone.

Wires data_layer -> agent -> eval_set. Runs without an API key (uses
the deterministic fallback in agent.py); set ANTHROPIC_API_KEY to
exercise the real Anthropic Messages API call path.

Usage:
    python example.py                # full pipeline on fixtures
    python example.py --eval         # run eval_set.yaml
    python example.py --score seg-002
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

from agent import (
    PipelineRun,
    caption_writer,
    clip_scorer,
    run_pipeline,
)
from data_layer import all_segments, build_store, get_segment, voice_examples


def _print_pipeline(run: PipelineRun) -> None:
    print("=== Scoring ===")
    for s in run.scored:
        print(f"  {s.segment_id}  score={s.score}/10  ({s.reason})")
    print()
    print(f"Top segment: {run.top_segment_id}")
    print()
    print("=== Captions ===")
    for cap in run.captions:
        print(f"\n--- {cap.platform} (len={len(cap.text)}) ---")
        print(cap.text)
    print()
    print("=== Review queue (NOTHING IS PUBLISHED) ===")
    for item in run.review_queue:
        print(f"  [{item.status}] {item.platform}: from {item.segment_id} (score {item.score})")


def _check_case(case: dict, conn, segments: list) -> tuple[bool, list]:
    criteria = case.get("pass_criteria") or {}
    failures: list = []
    inp = case["input"]

    if "platform" in inp:
        seg = get_segment(conn, inp["segment_id"])
        if not seg:
            return False, [f"segment {inp['segment_id']} not found"]
        examples = voice_examples(conn, inp["platform"], limit=3)
        cap = caption_writer(seg, inp["platform"], examples)
        if "caption_max_len" in criteria and len(cap.text) > criteria["caption_max_len"]:
            failures.append(f"caption {len(cap.text)} chars > max {criteria['caption_max_len']}")
        if "caption_min_len" in criteria and len(cap.text) < criteria["caption_min_len"]:
            failures.append(f"caption {len(cap.text)} chars < min {criteria['caption_min_len']}")
        for forbidden in criteria.get("caption_must_not_contain", []) or []:
            if forbidden in cap.text:
                failures.append(f"caption contains forbidden token {forbidden!r}")
        must_any = criteria.get("caption_must_contain_any") or []
        if must_any and not any(t in cap.text for t in must_any):
            failures.append(f"caption missing any of {must_any!r}")
        return (len(failures) == 0, failures)

    if inp["segment_id"] == "any":
        # Pipeline-level checks
        run = run_pipeline(conn, segments)
        if "review_queue_min" in criteria and len(run.review_queue) < criteria["review_queue_min"]:
            failures.append(
                f"review queue has {len(run.review_queue)}, need at least {criteria['review_queue_min']}"
            )
        required_status = criteria.get("review_status_all")
        if required_status:
            for item in run.review_queue:
                if item.status != required_status:
                    failures.append(f"review item status {item.status!r} != {required_status!r}")
        return (len(failures) == 0, failures)

    # Scorer-only checks
    seg = get_segment(conn, inp["segment_id"])
    if not seg:
        return False, [f"segment {inp['segment_id']} not found"]
    result = clip_scorer(seg)
    score = result.score
    if "score_min" in criteria and score < criteria["score_min"]:
        failures.append(f"score {score} < min {criteria['score_min']}")
    if "score_max" in criteria and score > criteria["score_max"]:
        failures.append(f"score {score} > max {criteria['score_max']}")
    return (len(failures) == 0, failures)


def run_eval(path: Path) -> int:
    suite = yaml.safe_load(path.read_text(encoding="utf-8"))
    print(f"=== Eval suite: {suite.get('suite', 'unknown')} ===")
    conn = build_store()
    segments = all_segments(conn)
    cases = suite.get("cases", []) or []
    passed = 0
    failed: list = []
    for case in cases:
        ok, failures = _check_case(case, conn, segments)
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {case['id']}")
        if ok:
            passed += 1
        else:
            failed.append({"id": case["id"], "failures": failures})
            for f in failures:
                print(f"      - {f}")
    print()
    print(f"Pass rate: {passed}/{len(cases)}")
    return 0 if not failed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Content pipeline capstone example")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--score", type=str, help="Score a single segment by ID")
    args = parser.parse_args()

    if args.eval:
        return run_eval(Path(__file__).resolve().parent / "eval_set.yaml")

    conn = build_store()
    segments = all_segments(conn)

    if args.score:
        seg = get_segment(conn, args.score)
        if not seg:
            print(f"No segment {args.score}", file=sys.stderr)
            return 2
        result = clip_scorer(seg)
        print(f"{result.segment_id}: score={result.score}/10  ({result.reason})")
        return 0

    print("=== Content pipeline walkthrough ===")
    print("(set ANTHROPIC_API_KEY to run against the real model; otherwise fallback mode)")
    print()
    run = run_pipeline(conn, segments)
    _print_pipeline(run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
