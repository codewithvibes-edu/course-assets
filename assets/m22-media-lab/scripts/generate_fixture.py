"""Generate the m22 synthetic support-call fixture. This file IS the source record
generator: the shipped recording was produced by running it, and fixture/source-record.json
records the hashes and tool versions of that run.

The recording is SYNTHETIC. Both voices are macOS text-to-speech voices (Eddy and Flo)
reading a scripted fake support call written for this course. No real person appears in
the audio or the video. That is the consent story: there is nobody to ask, and the
lesson prose still teaches consent as YOUR obligation for YOUR OWN media.

Platform: macOS only (uses the `say` command and a system font). Learners never need to
run this; the fixture ships frozen. Rerunning it on a different macOS version may produce
different audio bytes because the TTS voices are OS-versioned. The frozen copy is the
fixture; this script is its provenance.

Usage, from assets/m22-media-lab/:
    python3 scripts/generate_fixture.py [--workdir /tmp/m22-fixture-build]

Requires: macOS `say`, ffmpeg/ffprobe on PATH, Pillow.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

KIT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = KIT_ROOT / "fixture"

# ---------------------------------------------------------------------------
# The script. Two speakers, one fictional garden-supply company.
# Beat notes name what each line exists to exercise in the lessons.
# ---------------------------------------------------------------------------

AGENT = "agent"    # voice Eddy, support agent "Riley"
CALLER = "caller"  # voice Flo, unnamed caller

VOICES = {AGENT: "Eddy (English (US))", CALLER: "Flo (English (US))"}
RATES = {AGENT: 182, CALLER: 168}

# (speaker, text, gap_before_seconds, beat_note)
# gap_before is silence inserted before the line starts, measured from the end of
# the previous line. The hold gap is the VAD lesson's long silence.
LINES = [
    (AGENT, "Thanks for calling Maple and Finch Garden Supply, this is Riley. What can I help you with today?", 0.0, "greeting"),
    (CALLER, "Hi Riley. I placed an order last week, order four two one seven, and the status page still says processing.", 0.7, "problem statement, digit sequence for the confidence lesson"),
    (AGENT, "Let me pull that up. One moment.", 0.6, "leads into the hold"),
    (AGENT, "Okay, I see it. Order four two one seven, one cedar planter box, placed July fourteenth.", 3.5, "HOLD GAP before this line: long silence for VAD versus fixed windows"),
    (CALLER, "Right.", 0.25, "short backchannel turn, diarization split risk"),
    (AGENT, "The warehouse shows it packed, but the carrier never picked it up. That is why the status is stuck.", 0.5, "explanation, scene changes to the timeline chart"),
    (CALLER, "So is it lost, or...", 0.6, "OVERLAP BASE: the next agent line starts before this one ends"),
    (AGENT, "No, no, it is still on the shelf.", -1.0, "OVERLAP: starts about one second before the caller line ends"),
    (CALLER, "Okay. So what happens now?", 0.6, "turn after overlap"),
    (AGENT, "Two options. I can reship it tomorrow with two day shipping at no charge, or refund the whole order today.", 0.5, "options"),
    (CALLER, "Hmm.", 0.5, "short turn, diarization split risk"),
    (CALLER, "Reship it. I still want the planter.", 0.8, "same speaker twice in a row, tests turn merging"),
    (AGENT, "Done. The new tracking number goes out to your email tonight. Anything else?", 0.5, "resolution, scene changes to the confirmation screen"),
    (CALLER, "No, that covers it. Thanks.", 0.5, "close"),
    (AGENT, "Thanks for calling Maple and Finch. Have a good one.", 0.4, "close"),
]

# Scene boundaries anchor to line indices (scene starts when that line starts).
# Scene 2 instead anchors to the start of the hold gap.
SCENES = [
    ("s1-order-status", "order status page", None),        # from 0.0
    ("s2-hold-screen", "hold screen", "hold"),             # from hold start
    ("s3-order-detail", "order detail page", 3),           # "Okay, I see it"
    ("s4-fulfillment-timeline", "timeline chart", 5),      # "The warehouse shows"
    ("s5-resolution", "confirmation screen", 12),          # "Done."
]

BG = "#101418"
FG = "#e8ecef"
DIM = "#9aa4ad"
ACCENT = "#7fb069"  # fictional Maple + Finch brand green
WARN = "#d9a05b"
W, H = 960, 540


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = "/System/Library/Fonts/Helvetica.ttc"
    return ImageFont.truetype(path, size, index=1 if bold else 0)


def draw_frame(name: str) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((48, 32), "Maple + Finch Garden Supply", font=font(28, bold=True), fill=ACCENT)
    d.line([(48, 78), (W - 48, 78)], fill="#2a3138", width=2)

    if name == "s1-order-status":
        d.text((48, 120), "Order lookup", font=font(24, bold=True), fill=FG)
        d.text((48, 180), "Order 4217", font=font(34, bold=True), fill=FG)
        d.text((48, 236), "Status: Processing", font=font(28), fill=WARN)
        d.text((48, 292), "Placed: July 14", font=font(24), fill=DIM)
        d.text((48, 332), "Items: 1", font=font(24), fill=DIM)
        d.text((48, 420), "support.maple-finch.example", font=font(20), fill=DIM)
    elif name == "s2-hold-screen":
        d.text((48, 220), "Please hold", font=font(40, bold=True), fill=FG)
        d.text((48, 290), "Your agent is checking the order record.", font=font(24), fill=DIM)
    elif name == "s3-order-detail":
        d.text((48, 120), "Order 4217, detail", font=font(24, bold=True), fill=FG)
        d.text((48, 180), "1 x Cedar Planter Box, 24 inch", font=font(26), fill=FG)
        d.text((48, 236), "Placed: July 14", font=font(24), fill=DIM)
        d.text((48, 276), "Packed: July 15", font=font(24), fill=DIM)
        d.text((48, 316), "Carrier pickup: not recorded", font=font(24), fill=WARN)
        d.text((48, 380), "Reshipment policy: a stalled order reships free,", font=font(20), fill=DIM)
        d.text((48, 410), "or refunds in full. Customer chooses.", font=font(20), fill=DIM)
    elif name == "s4-fulfillment-timeline":
        d.text((48, 110), "Fulfillment timeline, order 4217", font=font(24, bold=True), fill=FG)
        steps = [
            ("Placed", "July 14", ACCENT, 1.0),
            ("Packed", "July 15", ACCENT, 1.0),
            ("Carrier pickup", "missed", WARN, 0.45),
            ("Delivery", "pending", "#4a5560", 0.15),
        ]
        y = 180
        for label, when, color, frac in steps:
            d.text((48, y), label, font=font(22), fill=FG)
            d.text((260, y), when, font=font(22), fill=DIM)
            d.rectangle([430, y + 4, 430 + int(440 * frac), y + 24], fill=color)
            y += 70
    elif name == "s5-resolution":
        d.text((48, 130), "Resolution", font=font(24, bold=True), fill=FG)
        d.text((48, 190), "Reshipment scheduled", font=font(32, bold=True), fill=ACCENT)
        d.text((48, 250), "Ships: tomorrow, two day service", font=font(24), fill=FG)
        d.text((48, 290), "Charge: none", font=font(24), fill=FG)
        d.text((48, 330), "Tracking number: emailed tonight", font=font(24), fill=FG)
    return img


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default="/tmp/m22-fixture-build")
    args = parser.parse_args()
    work = Path(args.workdir)
    (work / "lines").mkdir(parents=True, exist_ok=True)
    (work / "slides").mkdir(exist_ok=True)
    FIXTURE_DIR.mkdir(exist_ok=True)

    # 1. Synthesize each line and measure it.
    print("synthesizing lines...")
    line_files: list[Path] = []
    durations: list[float] = []
    for i, (speaker, text, _gap, _note) in enumerate(LINES):
        aiff = work / "lines" / f"line{i:02d}.aiff"
        wav = work / "lines" / f"line{i:02d}.wav"
        run(["say", "-v", VOICES[speaker], "-r", str(RATES[speaker]), "-o", str(aiff), text])
        run(["ffmpeg", "-y", "-v", "error", "-i", str(aiff), "-ar", "44100", "-ac", "1", str(wav)])
        line_files.append(wav)
        durations.append(probe_duration(wav))

    # 2. Lay lines on an absolute timeline. Negative gap creates the overlap.
    starts: list[float] = []
    cursor = 0.0
    hold_start = None
    for i, (_speaker, _text, gap, note) in enumerate(LINES):
        start = max(0.0, cursor + gap)
        if "HOLD GAP" in note:
            hold_start = cursor  # silence begins when the previous line ends
        starts.append(round(start, 3))
        cursor = max(cursor, start + durations[i])
    total = cursor + 1.2  # closing pad

    # 3. Mix: each line delayed to its start. Caller lines get a phone-band EQ.
    #    A faint fixed-seed line noise sits under everything.
    inputs: list[str] = []
    filters: list[str] = []
    amix_tags: list[str] = []
    for i, (speaker, _text, _gap, _note) in enumerate(LINES):
        inputs += ["-i", str(line_files[i])]
        delay_ms = int(starts[i] * 1000)
        chain = f"[{i}]adelay={delay_ms}|{delay_ms}"
        if speaker == CALLER:
            chain += ",highpass=f=300,lowpass=f=3400,volume=0.9"
        chain += f"[a{i}]"
        filters.append(chain)
        amix_tags.append(f"[a{i}]")
    n = len(LINES)
    filters.append(
        f"anoisesrc=r=44100:color=pink:amplitude=0.003:seed=4217:duration={total:.2f}[noise]"
    )
    filters.append(
        "".join(amix_tags) + f"[noise]amix=inputs={n + 1}:normalize=0[premix]"
    )
    filters.append("[premix]loudnorm=I=-19:TP=-1.5:LRA=11[mix]")
    mix_wav = work / "mix.wav"
    run(["ffmpeg", "-y", "-v", "error", *inputs,
         "-filter_complex", ";".join(filters), "-map", "[mix]",
         "-ar", "44100", "-ac", "1", "-t", f"{total:.2f}", str(mix_wav)])

    # 4. Scene boundaries from the timeline, then slides, then the slideshow.
    assert hold_start is not None
    scene_starts = []
    for name, _desc, anchor in SCENES:
        if anchor is None:
            scene_starts.append(0.0)
        elif anchor == "hold":
            scene_starts.append(round(hold_start + 0.4, 3))
        else:
            scene_starts.append(starts[anchor])
    scene_ends = scene_starts[1:] + [round(total, 3)]

    concat_lines = []
    for (name, _desc, _anchor), s, e in zip(SCENES, scene_starts, scene_ends):
        png = work / "slides" / f"{name}.png"
        draw_frame(name).save(png)
        concat_lines.append(f"file '{png}'\nduration {e - s:.3f}")
    concat_lines.append(f"file '{work / 'slides' / SCENES[-1][0]}.png'")
    concat_txt = work / "slides.txt"
    concat_txt.write_text("\n".join(concat_lines) + "\n")

    out_mp4 = FIXTURE_DIR / "maple-finch-support-call.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
         "-i", str(mix_wav),
         "-c:v", "libx264", "-r", "10", "-pix_fmt", "yuv420p", "-crf", "28",
         "-c:a", "aac", "-b:a", "96k", "-t", f"{total:.2f}", "-movflags", "+faststart",
         str(out_mp4)])

    # 5. Ground-truth timeline + source record.
    timeline = {
        "note": "Generation ground truth for the synthetic fixture. Lesson tools must NOT read this file; it exists so reviews can be checked against what was actually staged.",
        "total_seconds": round(total, 3),
        "hold_silence": {"start": round(hold_start, 3), "end": starts[3]},
        "overlap": {"caller_line": 6, "agent_line": 7,
                    "region": [starts[7], round(starts[6] + durations[6], 3)]},
        "lines": [
            {"index": i, "speaker": sp, "start": starts[i],
             "end": round(starts[i] + durations[i], 3), "text": tx, "beat": note}
            for i, (sp, tx, _g, note) in enumerate(LINES)
        ],
        "scenes": [
            {"name": name, "description": desc, "start": s, "end": e}
            for (name, desc, _a), s, e in zip(SCENES, scene_starts, scene_ends)
        ],
    }
    (FIXTURE_DIR / "timeline.json").write_text(json.dumps(timeline, indent=2) + "\n")

    def sha256(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    ffmpeg_version = subprocess.run(["ffmpeg", "-version"], capture_output=True,
                                    text=True, check=True).stdout.splitlines()[0]
    record = {
        "fixture": "maple-finch-support-call.mp4",
        "synthetic": True,
        "consent": "Synthetic recording. Both voices are macOS text-to-speech voices reading a script written for this course. No real person appears, no real customer data exists, the company is fictional.",
        "retention": "Ships with the course indefinitely as a labeled synthetic fixture. Derived learner artifacts follow the deletion exercise in lesson 7.",
        "generated_on": str(date.today()),
        "generator": "scripts/generate_fixture.py",
        "platform": f"{platform.system()} {platform.mac_ver()[0]}",
        "python": platform.python_version(),
        "ffmpeg": ffmpeg_version,
        "voices": VOICES,
        "sha256": {
            "maple-finch-support-call.mp4": sha256(out_mp4),
            "timeline.json": sha256(FIXTURE_DIR / "timeline.json"),
        },
        "reproducibility": "Rerunning this script may not reproduce identical bytes; TTS voices change with macOS versions. The committed files are the frozen fixture, and these hashes identify them.",
    }
    (FIXTURE_DIR / "source-record.json").write_text(json.dumps(record, indent=2) + "\n")

    print(f"fixture: {out_mp4}  ({out_mp4.stat().st_size / 1e6:.2f} MB, {total:.1f}s)")
    print(f"timeline lines: {len(LINES)}, scenes: {len(SCENES)}")


if __name__ == "__main__":
    sys.exit(main())
