"""Lesson 6, first half: sample frames three ways and build the manifest.

Three strategies over the same video, so their tradeoffs are visible side by side:
periodic (cheap, blind, catches slow content drift), scene-change (catches cuts,
misses gradual change), and cue-targeted (frames pulled at timestamps you already
care about, usually from the transcript). Every retained frame records its source
time and why it was kept. Nothing here generates imagery; frames are extracted
evidence from the source recording.

The scene threshold is content-dependent and that is a lesson, not a footnote.
Tutorials quote 0.25 to 0.4, which suits photographic footage where a cut changes
most pixels. On this fixture's screen share, slides keep the same dark layout and
header, so the four real cuts score between 0.03 and 0.10 while non-cut frames sit
under 0.01 (measured 2026-07-25, ffmpeg 8.1). The default below was chosen from
that measurement. On your own media, measure before you trust a threshold.

Usage, from assets/m22-media-lab/ with the recipe venv active:
    python pipeline/sample_frames.py [--period 10] [--scene-threshold 0.02] [--cue 32.0 --cue 60.0]
"""

from __future__ import annotations

import argparse
import re
import subprocess

from common import SOURCE_FIXTURE, sha256_file, work_dir, write_record

MERGE_WINDOW_S = 0.75


def showinfo_times(stderr: str) -> list[float]:
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", stderr)]


def extract(video, vf: str, pattern) -> list[tuple[float, str]]:
    """Run one ffmpeg extraction, return (source_time, file) pairs."""
    pattern.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["ffmpeg", "-y", "-v", "info", "-i", str(video),
         "-vf", f"{vf},showinfo", "-fps_mode", "vfr", str(pattern)],
        capture_output=True, text=True, check=True,
    )
    times = showinfo_times(proc.stderr)
    files = sorted(pattern.parent.glob(pattern.name.replace("%03d", "*")))
    return list(zip(times, [str(f) for f in files]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", type=float, default=10.0)
    parser.add_argument("--scene-threshold", type=float, default=0.02)
    parser.add_argument("--cue", type=float, action="append", default=None,
                        help="timestamp in seconds to pull a targeted frame at; repeatable")
    args = parser.parse_args()
    cues = args.cue or []

    frames_dir = work_dir() / "frames"
    candidates: list[dict] = []

    for t, f in extract(SOURCE_FIXTURE, f"fps=1/{args.period}", frames_dir / "periodic-%03d.png"):
        candidates.append({"source_time": round(t, 2), "file": f, "reasons": ["periodic"]})
    for t, f in extract(SOURCE_FIXTURE, f"select='gt(scene,{args.scene_threshold})'",
                        frames_dir / "scene-%03d.png"):
        candidates.append({"source_time": round(t, 2), "file": f, "reasons": ["scene-change"]})
    for i, cue in enumerate(cues):
        pattern = frames_dir / f"cue-{i:03d}.png"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(cue), "-i", str(SOURCE_FIXTURE),
             "-frames:v", "1", str(pattern)],
            capture_output=True, check=True,
        )
        candidates.append({"source_time": cue, "file": str(pattern), "reasons": [f"cue at {cue}s"]})

    # Merge near-duplicate times so one moment does not become three manifest rows.
    candidates.sort(key=lambda c: c["source_time"])
    retained: list[dict] = []
    for cand in candidates:
        if retained and cand["source_time"] - retained[-1]["source_time"] < MERGE_WINDOW_S:
            retained[-1]["reasons"] = sorted(set(retained[-1]["reasons"] + cand["reasons"]))
        else:
            retained.append(cand)
    for row in retained:
        row["sha256"] = sha256_file(row["file"])
        row["file"] = str(row["file"]).split("work/", 1)[-1]

    record = {
        "tool": "ffmpeg frame extraction, pipeline/sample_frames.py",
        "source": SOURCE_FIXTURE.name,
        "strategies": {
            "periodic_seconds": args.period,
            "scene_threshold": args.scene_threshold,
            "cues": cues,
        },
        "frames": retained,
        "reading": (
            "Periodic sampling never misses for long but wastes frames on a static "
            "screen; scene-change catches every hard cut and nothing between them; "
            "cues get exactly what the transcript told you to look for. The manifest "
            "records reasons so a later reader knows why each frame exists."
        ),
    }
    write_record(work_dir() / "frame-manifest.json", record)

    print(f"\n{len(candidates)} extracted, {len(retained)} retained after merging")
    for row in retained:
        print(f"  {row['source_time']:6.2f}s  {row['file']:24s}  {', '.join(row['reasons'])}")


if __name__ == "__main__":
    main()
