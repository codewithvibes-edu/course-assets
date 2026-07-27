"""Lesson 6, second half: OCR the retained frames and record bounded observations.

Runs Tesseract over every frame in the manifest and stores what it read, plus a
review flag wherever the output looks thin. OCR output is a hypothesis about pixels,
not ground truth: the fixture's own chart comes back with its bars read as stray
letters, and the lesson has you catch that against the frame itself.

Usage, from assets/m22-media-lab/ with the recipe venv active and tesseract installed:
    python pipeline/ocr_frames.py
"""

from __future__ import annotations

import shutil
import subprocess

from common import WORK_DIR, read_record, require, work_dir, write_record


def main() -> None:
    if not shutil.which("tesseract"):
        raise SystemExit("tesseract not found on PATH; install it per the recipe first")
    tess_version = subprocess.run(
        ["tesseract", "--version"], capture_output=True, text=True
    ).stdout.splitlines()[0]

    manifest = read_record(
        require(WORK_DIR / "frame-manifest.json", "run pipeline/sample_frames.py first")
    )

    results = []
    for frame in manifest["frames"]:
        path = WORK_DIR / frame["file"]
        proc = subprocess.run(
            ["tesseract", str(path), "stdout"], capture_output=True, text=True, check=True
        )
        lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        results.append(
            {
                "file": frame["file"],
                "source_time": frame["source_time"],
                "reasons": frame["reasons"],
                "ocr_lines": lines,
                "needs_review": len(lines) < 2,
            }
        )

    record = {
        "tool": tess_version,
        "frames_read": len(results),
        "results": results,
        "reading": (
            "Treat every ocr_lines entry as a claim to verify against its frame. "
            "Where a number matters, the frame image is the ground truth and the "
            "manifest's source_time is how you cite it."
        ),
    }
    write_record(work_dir() / "frame-ocr.json", record)

    print(f"\nOCR over {len(results)} frames ({tess_version})")
    for r in results:
        flag = "  REVIEW" if r["needs_review"] else ""
        first = r["ocr_lines"][0] if r["ocr_lines"] else "(nothing read)"
        print(f"  {r['source_time']:6.2f}s  {first[:60]}{flag}")


if __name__ == "__main__":
    main()
