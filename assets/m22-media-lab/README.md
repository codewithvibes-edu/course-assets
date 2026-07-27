# m22 media lab: turn one recording into a usable data product

The working kit for Module 22. One synthetic support-call recording goes in; a
schema-versioned, speaker-labeled, visually joined, deletable transcript comes out,
with every intermediate record saved and every uncertainty kept visible.

## What is in here

| Folder | What it holds |
|--------|---------------|
| `fixture/` | The frozen synthetic recording (73s, two TTS voices, staged screen share), its annotated script, generation ground truth, and the source record with hashes. Frozen: never regenerate casually. |
| `scripts/` | `generate_fixture.py`, the generator that produced the fixture. It ships as the fixture's provenance (lesson 2's source record), not as something learners run. macOS only. |
| `pipeline/` | The eight lesson tools, run in order, plus common.py, the shared helper they all import. Each tool writes a JSON record into `work/` and refuses to run before its prerequisites. |
| `recipes/` | Dated setup-and-run recipes. macOS / Linux verified 2026-07-25; Windows canary until an on-OS run. |
| `reference-outputs/` | The course team's verified run against the fixture, for comparison and for the measured numbers the module quotes. |
| `tests/` | Offline suite (`python3 -m unittest discover -s tests`): fixture freeze, correction semantics, join validation, deletion drill, kit hygiene. No model downloads. |
| `work/` | Created by the tools, ignored by git, and removed entirely by the lesson 7 deletion drill. |

## Run order

Follow `recipes/media-pipeline-macos-linux.sh` (or the Windows recipe) top to
bottom. It maps one-to-one onto lessons 2 through 7: inspect and normalize,
VAD versus fixed windows, transcribe three ways, review and correct, diarize,
sample frames and OCR, join, delete.

## The hardware and honesty rules

Everything here runs on CPU on an ordinary laptop: whisper tiny and small, a small
public speaker-embedding model, ffmpeg, and Tesseract. That is the course's
majority-hardware rule applied to media. Where this free local lane genuinely runs
out (long recordings on a slow machine, many-speaker diarization, hard OCR), the
module says so and names the hosted option as a real path instead of pretending. In the other direction, nothing here phones home: after the one-time
model downloads, the pipeline runs offline, and your media never leaves the machine.

The fixture is synthetic on purpose: scripted, TTS-voiced, fictional company, no
real person, which is why it can ship with the course at all. Your own recordings
need what it did not: every recorded person's consent, written down before the
first tool runs. Lesson 2 holds that line.
