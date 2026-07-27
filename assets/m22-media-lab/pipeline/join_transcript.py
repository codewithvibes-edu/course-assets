"""Lesson 7, first half: join every record into one schema-versioned transcript.

Audio words, anonymous speaker turns, and visual events meet here, keyed by the one
thing they share: time in the source recording. Each side keeps its own uncertainty
(word probabilities, diarization review flags, OCR review flags) instead of the join
papering over them. The output validates against pipeline/transcript.schema.json
before it is written; an invalid join refuses to exist.

Usage, from assets/m22-media-lab/ with the recipe venv active:
    python pipeline/join_transcript.py
"""

from __future__ import annotations

from datetime import date

from common import FIXTURE_DIR, WORK_DIR, read_record, require, sha256_file, work_dir, write_record

SCHEMA_VERSION = 1


def validate(doc: dict) -> list[str]:
    """Enforce the shape documented in transcript.schema.json. Returns problems."""
    problems: list[str] = []

    def need(obj: dict, keys: list[str], where: str) -> None:
        for key in keys:
            if key not in obj:
                problems.append(f"{where}: missing required field {key!r}")

    need(doc, ["schema_version", "source", "provenance", "segments",
               "visual_events", "review", "derived_artifacts"], "document")
    if doc.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"document: schema_version must be {SCHEMA_VERSION}")
    if isinstance(doc.get("source"), dict):
        need(doc["source"], ["file", "sha256", "synthetic", "consent", "retention"], "source")
        for key in ("consent", "retention"):
            if not str(doc["source"].get(key, "")).strip():
                problems.append(f"source: {key} must not be empty")
    if isinstance(doc.get("provenance"), dict):
        need(doc["provenance"], ["tools", "joined_on"], "provenance")
    for i, seg in enumerate(doc.get("segments", [])):
        need(seg, ["start", "end", "speaker", "text", "words"], f"segments[{i}]")
        for j, word in enumerate(seg.get("words", [])):
            need(word, ["word", "start", "end", "probability"], f"segments[{i}].words[{j}]")
    for i, ev in enumerate(doc.get("visual_events", [])):
        need(ev, ["source_time", "file", "sha256", "reasons", "ocr_lines"], f"visual_events[{i}]")
    if isinstance(doc.get("review"), dict):
        need(doc["review"], ["corrections_applied", "diarization_flags"], "review")
    return problems


def assign_speaker(seg: dict, turns: list[dict]) -> str:
    """Label a segment with the turn it overlaps most, or unassigned."""
    best, best_overlap = "unassigned", 0.0
    for turn in turns:
        overlap = min(seg["end"], turn["end"]) - max(seg["start"], turn["start"])
        if overlap > best_overlap:
            best, best_overlap = turn["speaker"], overlap
    return best


def main() -> None:
    reviewed = WORK_DIR / "transcript-reviewed.json"
    transcript_path = reviewed if reviewed.exists() else WORK_DIR / "transcript-small-batch.json"
    transcript = read_record(require(transcript_path, "run pipeline/transcribe.py first"))
    turns_rec = read_record(require(WORK_DIR / "speaker-turns.json", "run pipeline/diarize.py first"))
    manifest = read_record(require(WORK_DIR / "frame-manifest.json", "run pipeline/sample_frames.py first"))
    ocr = read_record(require(WORK_DIR / "frame-ocr.json", "run pipeline/ocr_frames.py first"))
    source_rec = read_record(FIXTURE_DIR / "source-record.json")

    ocr_by_file = {r["file"]: r for r in ocr["results"]}
    visual_events = []
    for frame in manifest["frames"]:
        read = ocr_by_file.get(frame["file"], {})
        visual_events.append(
            {
                "source_time": frame["source_time"],
                "file": frame["file"],
                "sha256": frame["sha256"],
                "reasons": frame["reasons"],
                "ocr_lines": read.get("ocr_lines", []),
                "needs_review": read.get("needs_review", True),
            }
        )

    segments = []
    for seg in transcript["segments"]:
        row = {
            "start": seg["start"],
            "end": seg["end"],
            "speaker": assign_speaker(seg, turns_rec["turns"]),
            "text": seg["text"],
            "words": seg["words"],
        }
        if "text_reviewed" in seg:
            row["text_reviewed"] = seg["text_reviewed"]
        segments.append(row)

    derived = sorted(
        str(p.relative_to(WORK_DIR))
        for p in WORK_DIR.rglob("*")
        if p.is_file() and "ecapa-model" not in p.parts
    ) + ["transcript.json"]

    doc = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "file": source_rec["fixture"],
            "sha256": source_rec["sha256"][source_rec["fixture"]],
            "synthetic": source_rec["synthetic"],
            "consent": source_rec["consent"],
            "retention": source_rec["retention"],
        },
        "provenance": {
            "tools": [
                transcript["tool"],
                turns_rec["tool"],
                manifest["tool"],
                ocr["tool"],
                "pipeline/join_transcript.py",
            ],
            "joined_on": str(date.today()),
        },
        "segments": segments,
        "visual_events": visual_events,
        "review": {
            "corrections_applied": transcript.get("review", {}).get("corrections_applied", []),
            "diarization_flags": turns_rec["review_queue"],
        },
        "derived_artifacts": derived,
    }

    problems = validate(doc)
    if problems:
        for p in problems:
            print(f"INVALID: {p}")
        raise SystemExit("join refused: fix the problems above")

    write_record(work_dir() / "transcript.json", doc)
    unassigned = [s for s in segments if s["speaker"] == "unassigned"]
    print(f"\n{len(segments)} segments, {len(visual_events)} visual events, "
          f"{len(doc['derived_artifacts'])} derived artifacts listed")
    if unassigned:
        print("segments with no speaker turn (cross-check these against the audio):")
        for seg in unassigned:
            print(f"  {seg['start']:6.2f}-{seg['end']:6.2f}s  {seg['text'][:50]}")


if __name__ == "__main__":
    main()
