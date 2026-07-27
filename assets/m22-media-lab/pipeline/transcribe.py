"""Lessons 3 and 4: transcribe the working copy with word-level timestamps.

Two models (tiny and small) and two consumption modes (batch and stream) cover the
comparison work: model size versus accuracy, and results-all-at-once versus results
-as-they-decode. The stream mode is honest about what it is: the same local decode,
consumed incrementally, which is what "streaming transcription" means for a local
model. A hosted streaming API differs in transport, not in this shape.

Usage, from assets/m22-media-lab/ with the recipe venv active:
    python pipeline/transcribe.py --model tiny --mode batch
    python pipeline/transcribe.py --model small --mode stream
"""

from __future__ import annotations

import argparse
import time

from faster_whisper import WhisperModel

from common import WORKING_COPY, require, work_dir, write_record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["tiny", "small"], default="small")
    parser.add_argument("--mode", choices=["batch", "stream"], default="batch")
    args = parser.parse_args()

    require(WORKING_COPY, "run the normalize step from the recipe first")

    t0 = time.monotonic()
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    load_s = time.monotonic() - t0

    t0 = time.monotonic()
    segments, info = model.transcribe(
        str(WORKING_COPY), word_timestamps=True, vad_filter=True
    )

    out_segments = []
    first_result_s = None
    for seg in segments:
        if first_result_s is None:
            first_result_s = time.monotonic() - t0
        words = [
            {
                "word": w.word.strip(),
                "start": round(float(w.start), 2),
                "end": round(float(w.end), 2),
                "probability": round(float(w.probability), 3),
            }
            for w in (seg.words or [])
        ]
        out_segments.append(
            {
                "start": round(float(seg.start), 2),
                "end": round(float(seg.end), 2),
                "text": seg.text.strip(),
                "words": words,
            }
        )
        if args.mode == "stream":
            elapsed = time.monotonic() - t0
            print(f"[{elapsed:5.1f}s elapsed] {seg.start:6.1f}-{seg.end:6.1f}  {seg.text.strip()}")
    total_s = time.monotonic() - t0

    n_words = sum(len(s["words"]) for s in out_segments)
    low_conf = [
        w for s in out_segments for w in s["words"] if w["probability"] < 0.5
    ]

    record = {
        "tool": f"faster-whisper, model {args.model}, int8 on cpu",
        "mode": args.mode,
        "language": info.language,
        "model_load_seconds": round(load_s, 1),
        "first_result_seconds": round(first_result_s or total_s, 1),
        "total_seconds": round(total_s, 1),
        "segments": out_segments,
        "word_count": n_words,
        "low_confidence_words": low_conf,
        "reading": (
            "first_result_seconds versus total_seconds is the latency story: batch "
            "callers wait for total, stream consumers start reading at first result. "
            "low_confidence_words is the review queue for lesson 4; probability is "
            "prioritization evidence, not calibrated certainty."
        ),
    }
    write_record(work_dir() / f"transcript-{args.model}-{args.mode}.json", record)

    print(f"\nmodel {args.model} ({args.mode}): {n_words} words, "
          f"first result {record['first_result_seconds']}s, total {record['total_seconds']}s")
    print(f"words under 0.5 probability: {len(low_conf)}")
    for w in low_conf:
        print(f"  {w['start']:6.2f}s  p={w['probability']:.3f}  {w['word']}")


if __name__ == "__main__":
    main()
