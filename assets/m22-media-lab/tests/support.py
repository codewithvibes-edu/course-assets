"""Test support: make pipeline/ importable and share tiny builders.

The suite imports only the standard-library pipeline modules (common,
review_alignment, join_transcript, delete_derived, sample_frames helpers). The
model-backed tools (transcribe, diarize, vad_compare, ocr_frames) are exercised by
running the pipeline itself; their outputs are frozen in reference-outputs/.
"""

import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT_ROOT / "pipeline"))


def segment(words, start=None, end=None, text=None):
    """Build a transcript segment from (word, start, end, probability) tuples."""
    rows = [
        {"word": w, "start": s, "end": e, "probability": p} for w, s, e, p in words
    ]
    return {
        "start": start if start is not None else rows[0]["start"],
        "end": end if end is not None else rows[-1]["end"],
        "text": text or " ".join(r["word"] for r in rows),
        "words": rows,
    }
