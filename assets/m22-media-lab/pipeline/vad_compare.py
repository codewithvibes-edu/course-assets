"""Lesson 3, first half: compare fixed-window chunking with voice-activity segments.

Runs Silero VAD over the working copy, lays fixed windows over the same audio, and
writes a comparison record: where each approach puts boundaries, how much silence each
one would send to the transcriber, and which fixed boundaries land inside speech
(the clipped-word risk).

Usage, from assets/m22-media-lab/ with the recipe venv active:
    python pipeline/vad_compare.py [--window-seconds 5.0]
"""

from __future__ import annotations

import argparse

import torch
from silero_vad import get_speech_timestamps, load_silero_vad

from common import WORKING_COPY, load_wav_mono16k, require, work_dir, write_record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window-seconds", type=float, default=5.0)
    args = parser.parse_args()

    require(WORKING_COPY, "run the normalize step from the recipe first")
    samples, sr = load_wav_mono16k(WORKING_COPY)
    total = len(samples) / sr

    model = load_silero_vad()
    speech = get_speech_timestamps(
        torch.tensor(samples), model, sampling_rate=sr, return_seconds=True
    )
    vad_segments = [{"start": s["start"], "end": s["end"]} for s in speech]
    speech_seconds = sum(s["end"] - s["start"] for s in vad_segments)

    fixed = []
    t = 0.0
    while t < total:
        fixed.append({"start": round(t, 2), "end": round(min(t + args.window_seconds, total), 2)})
        t += args.window_seconds

    def inside_speech(t: float) -> bool:
        return any(s["start"] < t < s["end"] for s in vad_segments)

    clipped = [w["end"] for w in fixed[:-1] if inside_speech(w["end"])]

    record = {
        "tool": "silero-vad via pipeline/vad_compare.py",
        "audio_seconds": round(total, 2),
        "speech_seconds": round(speech_seconds, 2),
        "silence_seconds": round(total - speech_seconds, 2),
        "vad_segments": vad_segments,
        "fixed_windows": fixed,
        "fixed_boundaries_inside_speech": clipped,
        "reading": (
            "Every boundary listed in fixed_boundaries_inside_speech cuts through "
            "someone talking; a transcriber fed those windows can clip or duplicate "
            "the words at the cut. The VAD segments skip the silence entirely, which "
            "is also the processing you do not pay for."
        ),
    }
    write_record(work_dir() / "segmentation-comparison.json", record)

    print(f"\naudio {total:.1f}s, speech {speech_seconds:.1f}s, "
          f"silence {total - speech_seconds:.1f}s")
    print(f"VAD segments: {len(vad_segments)}, fixed {args.window_seconds:.0f}s windows: {len(fixed)}")
    print(f"fixed boundaries landing inside speech: {[round(x, 1) for x in clipped]}")
    for s in vad_segments:
        print(f"  speech {s['start']:6.2f} - {s['end']:6.2f}")


if __name__ == "__main__":
    main()
