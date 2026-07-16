"""
Human review CLI workflow. Walks through a sampled subset of outputs,
prompts the reviewer for a 1-5 score and a free-form note, records to
JSON.

Sample rate is configured per case in the suite. The recorded reviews
feed back into model-graded calibration.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .types import EvalResult, Score, ScoreSource


@dataclass
class HumanReviewer:
    """Interactive CLI human reviewer."""

    out_path: Path

    def review(self, results: Iterable[EvalResult], sample_rate: float = 0.05) -> None:
        results_list = list(results)
        if not results_list or sample_rate <= 0:
            return
        n_to_review = max(1, int(round(len(results_list) * sample_rate)))
        sampled = random.sample(results_list, min(n_to_review, len(results_list)))

        records: list[dict] = []
        if self.out_path.exists():
            try:
                records = json.loads(self.out_path.read_text())
            except json.JSONDecodeError:
                records = []

        print(f"\n=== Human review: {len(sampled)} samples ===\n")
        for i, result in enumerate(sampled, 1):
            print(f"--- Sample {i}/{len(sampled)} (case {result.case_id}) ---")
            print(f"Output:\n{result.output[:1500]}")
            print()
            score = self._prompt_score()
            note = self._prompt_note()
            records.append(
                {
                    "case_id": result.case_id,
                    "score": score,
                    "note": note,
                    "output_preview": result.output[:500],
                }
            )
            self.out_path.write_text(json.dumps(records, indent=2))

        print(f"\nRecorded {len(sampled)} review(s) to {self.out_path}")

    def _prompt_score(self) -> int:
        while True:
            raw = input("Score 1-5 (1=bad, 3=ok, 5=excellent), or 's' to skip: ").strip().lower()
            if raw == "s":
                return 0
            if raw.isdigit() and 1 <= int(raw) <= 5:
                return int(raw)
            print("Enter 1-5 or 's'.")

    def _prompt_note(self) -> str:
        return input("Note (optional, press enter to skip): ").strip()


def merge_human_into_results(results: list[EvalResult], reviews_path: Path) -> None:
    """
    Merge recorded human reviews back into the EvalResult list. Adds a
    Score with source=HUMAN. Mutates the list in place.
    """
    if not reviews_path.exists():
        return
    try:
        records = json.loads(reviews_path.read_text())
    except json.JSONDecodeError:
        return

    by_case: dict[str, list[dict]] = {}
    for record in records:
        by_case.setdefault(record["case_id"], []).append(record)

    for result in results:
        for record in by_case.get(result.case_id, []):
            score_value = record["score"] / 5.0 if record["score"] else None
            result.scores.append(
                Score(
                    source=ScoreSource.HUMAN,
                    rule="human_review",
                    passed=record["score"] >= 4 if record["score"] else False,
                    value=score_value,
                    detail=record.get("note", ""),
                )
            )
