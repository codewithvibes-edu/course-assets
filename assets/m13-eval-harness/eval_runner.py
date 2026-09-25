"""
CLI entry point for running an eval suite.

Usage:
    python eval_runner.py --suite examples/classifier.suite.yaml --output results.json
    python eval_runner.py --suite ... --skip-model-graded   # deterministic only
    python eval_runner.py --suite ... --review              # also run human review
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add the package root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_harness import run_suite, HumanReviewer
from eval_harness.human import merge_human_into_results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an eval suite.")
    parser.add_argument("--suite", required=True, type=Path, help="Path to a suite YAML")
    parser.add_argument("--output", type=Path, default=Path("results.json"))
    parser.add_argument("--skip-model-graded", action="store_true")
    parser.add_argument(
        "--review",
        action="store_true",
        help="Run human review on a sampled subset after the suite finishes",
    )
    parser.add_argument(
        "--review-output",
        type=Path,
        default=Path("human_reviews.json"),
        help="Where to record human review scores",
    )
    parser.add_argument(
        "--grader-model",
        default="claude-opus-5-5",
        help="Stronger model used for model-graded scoring",
    )
    args = parser.parse_args()

    if not args.suite.exists():
        print(f"Suite not found: {args.suite}", file=sys.stderr)
        return 2

    print(f"Running {args.suite}...")
    suite_result = run_suite(
        args.suite,
        skip_model_graded=args.skip_model_graded,
        grader_model=args.grader_model,
    )

    if args.review:
        reviewer = HumanReviewer(out_path=args.review_output)
        # Use the first case's sample rate as default; per-case rates are
        # preserved in suite YAML for future expansion.
        reviewer.review(suite_result.results, sample_rate=0.1)
        merge_human_into_results(suite_result.results, args.review_output)

    args.output.write_text(json.dumps(suite_result.to_dict(), indent=2))
    print(f"\nWrote {args.output}")
    print(
        f"Pass rate: {suite_result.pass_rate:.0%} "
        f"({sum(1 for r in suite_result.results if r.passed)}/{len(suite_result.results)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
