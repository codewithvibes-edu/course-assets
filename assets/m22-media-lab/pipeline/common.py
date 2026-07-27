"""Shared helpers for the m22 media pipeline. Standard library only.

Every tool in this folder reads from and writes to the work/ directory next to the
kit root (created on first use, ignored by git). Records are JSON with stable keys so
the join step in lesson 7 can assemble them without guessing.
"""

from __future__ import annotations

import hashlib
import json
import wave
from datetime import date
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = KIT_ROOT / "fixture"
WORK_DIR = KIT_ROOT / "work"

SOURCE_FIXTURE = FIXTURE_DIR / "maple-finch-support-call.mp4"
WORKING_COPY = WORK_DIR / "call-16k-mono.wav"


def work_dir() -> Path:
    WORK_DIR.mkdir(exist_ok=True)
    return WORK_DIR


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_record(path: Path, payload: dict) -> None:
    """Write a JSON record with a recorded date, creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"recorded_on": str(date.today()), **payload}
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {path.relative_to(KIT_ROOT)}")


def read_record(path: Path) -> dict:
    return json.loads(path.read_text())


def load_wav_mono16k(path: Path):
    """Load a 16 kHz mono 16-bit PCM WAV as (list_of_float, sample_rate).

    The normalize step produces exactly this shape; refusing anything else keeps
    every downstream tool honest about what it was tested on.
    """
    with wave.open(str(path), "rb") as f:
        if f.getframerate() != 16000 or f.getnchannels() != 1 or f.getsampwidth() != 2:
            raise SystemExit(
                f"{path} is not a 16 kHz mono 16-bit WAV. Run the normalize step "
                "from the recipe first; every tool here expects the working copy."
            )
        raw = f.readframes(f.getnframes())
    samples = [
        int.from_bytes(raw[i : i + 2], "little", signed=True) / 32768.0
        for i in range(0, len(raw), 2)
    ]
    return samples, 16000


def require(path: Path, hint: str) -> Path:
    if not path.exists():
        raise SystemExit(f"missing {path.relative_to(KIT_ROOT)}; {hint}")
    return path
