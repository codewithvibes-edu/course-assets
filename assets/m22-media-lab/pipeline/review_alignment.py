"""Lesson 4: surface the low-confidence spans, then apply reviewed corrections.

First run lists the words most worth checking, lowest probability first. You listen
to those spans in the source, decide what was actually said, and write your verdicts
into work/corrections.json (the format is printed below and shipped as an example in
reference-outputs/). A second run applies them: the corrected text replaces the
transcript reading, and the original machine hypothesis stays in the record next to
who corrected it and why. Corrections that erase their own history are how transcripts
stop being auditable.

Usage, from assets/m22-media-lab/ with the recipe venv active:
    python pipeline/review_alignment.py [--transcript transcript-small-batch.json] [--threshold 0.5]
"""

from __future__ import annotations

import argparse
import json

from common import WORK_DIR, read_record, require, work_dir, write_record

EXAMPLE = {
    "corrections": [
        {
            "span": [25.4, 26.6],
            "original": "one-seater",
            "corrected": "one cedar",
            "corrected_by": "your name or tool, never blank",
            "reason": "listened to the span; the product is a cedar planter box",
        }
    ]
}


def apply_correction(segment: dict, corr: dict) -> bool:
    """Mark every word inside the correction span; return True if any matched."""
    hit = False
    for word in segment["words"]:
        if word["start"] < corr["span"][1] and word["end"] > corr["span"][0]:
            word.setdefault("original_hypothesis", word["word"])
            word["corrected_by"] = corr["corrected_by"]
            hit = True
    if hit:
        segment.setdefault("applied_corrections", []).append(corr)
    return hit


def corrected_text(segment: dict) -> str:
    """Render segment text with correction spans spliced in."""
    out: list[str] = []
    emitted: set[int] = set()
    for i, word in enumerate(segment["words"]):
        if i in emitted:
            continue
        corr = next(
            (c for c in segment.get("applied_corrections", [])
             if word["start"] < c["span"][1] and word["end"] > c["span"][0]),
            None,
        )
        if corr is None:
            out.append(word["word"])
            continue
        out.append(corr["corrected"])
        for j in range(i, len(segment["words"])):
            w = segment["words"][j]
            if w["start"] < corr["span"][1] and w["end"] > corr["span"][0]:
                emitted.add(j)
    return " ".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript", default="transcript-small-batch.json")
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    transcript = read_record(
        require(WORK_DIR / args.transcript, "run pipeline/transcribe.py first")
    )

    queue = [
        {"start": w["start"], "end": w["end"], "word": w["word"], "probability": w["probability"]}
        for s in transcript["segments"]
        for w in s["words"]
        if w["probability"] < args.threshold
    ]
    queue.sort(key=lambda w: w["probability"])

    corrections_path = WORK_DIR / "corrections.json"
    if not corrections_path.exists():
        print(f"review queue ({len(queue)} words under p={args.threshold}), lowest first:")
        for w in queue:
            print(f"  {w['start']:6.2f}-{w['end']:6.2f}s  p={w['probability']:.3f}  {w['word']}")
        print("\nno work/corrections.json yet. Listen to the spans above in the source,")
        print("then write your verdicts in this shape and rerun:")
        print(json.dumps(EXAMPLE, indent=2))
        return

    corrections = read_record(corrections_path)["corrections"]
    required = {"span", "original", "corrected", "corrected_by", "reason"}
    for corr in corrections:
        missing = required - set(corr)
        if missing:
            raise SystemExit(f"correction {corr} is missing {sorted(missing)}")

    applied, unmatched = [], []
    for corr in corrections:
        if any(apply_correction(seg, corr) for seg in transcript["segments"]):
            applied.append(corr)
        else:
            unmatched.append(corr)

    for seg in transcript["segments"]:
        if seg.get("applied_corrections"):
            seg["text_reviewed"] = corrected_text(seg)

    transcript["review"] = {
        "threshold": args.threshold,
        "review_queue_size": len(queue),
        "corrections_applied": applied,
        "corrections_unmatched": unmatched,
    }
    write_record(work_dir() / "transcript-reviewed.json", transcript)

    print(f"\napplied {len(applied)} corrections, {len(unmatched)} matched nothing")
    for seg in transcript["segments"]:
        if "text_reviewed" in seg:
            print(f"  {seg['start']:6.2f}s  was : {seg['text']}")
            print(f"  {'':8s} now : {seg['text_reviewed']}")
    if unmatched:
        print("unmatched spans (check the times):")
        for corr in unmatched:
            print(f"  {corr['span']}  {corr['original']!r}")


if __name__ == "__main__":
    main()
