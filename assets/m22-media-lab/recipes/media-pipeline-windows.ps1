# DATED RECIPE: the m22 media pipeline environment on Windows 11.
# Status: CANARY, authored 2026-07-25. Desk-checked against vendor documentation,
# not yet run on a real Windows machine; it flips to current after an on-OS
# run. The pipeline itself is the same Python either way; only the installs and
# activation differ from the macOS / Linux recipe.
#
# Everything runs on CPU. No GPU, no account, no API key, no paid anything.
# First runs download open models (about 1 GB of disk across models and venv).
#
# These are commands to run one at a time and READ, not a script to execute.

# ---- system tools -----------------------------------------------------------
winget install --id Gyan.FFmpeg -e
winget install --id tesseract-ocr.tesseract -e
# Reopen the terminal after installs so PATH updates.

ffmpeg -version        # expect: a recent major (course-tested against 8.x)
tesseract --version    # expect: 5.x

# ---- python environment, from assets\m22-media-lab\ -------------------------
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install faster-whisper==1.2.1 silero-vad==6.2.1 speechbrain==1.1.0 scikit-learn==1.9.0
# torch arrives as a dependency of the two model packages; that is the big
# download in this step.

# ---- lesson 2: inspect the source, then make the working copy ---------------
ffprobe -v error -show_format -show_streams fixture\maple-finch-support-call.mp4
# expect: one h264 video stream 960x540, one aac audio stream, duration 73.1

mkdir work -Force
ffmpeg -y -v error -i fixture\maple-finch-support-call.mp4 `
  -ar 16000 -ac 1 -c:a pcm_s16le work\call-16k-mono.wav
# expect: work\call-16k-mono.wav, 16 kHz mono, about 2.3 MB

# ---- lessons 3 through 7: identical to the macOS / Linux recipe -------------
python pipeline\vad_compare.py
python pipeline\transcribe.py --model tiny  --mode batch
python pipeline\transcribe.py --model small --mode batch
python pipeline\transcribe.py --model small --mode stream
python pipeline\review_alignment.py
python pipeline\diarize.py
python pipeline\sample_frames.py --cue 32.0 --cue 60.0
python pipeline\ocr_frames.py
python pipeline\join_transcript.py
python pipeline\delete_derived.py
python pipeline\delete_derived.py --apply
# expected outputs per step are documented in the macOS / Linux recipe and in
# reference-outputs\README.md; the records have the same shape.

# ---- stop / undo -------------------------------------------------------------
deactivate
# Remove-Item -Recurse -Force .venv, work    # environment and derived data
# winget uninstall Gyan.FFmpeg               # only if nothing else uses them
# winget uninstall tesseract-ocr.tesseract

# ---- common errors -----------------------------------------------------------
# "running scripts is disabled": Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#   then reopen the terminal, is the standard fix for venv activation.
# "tesseract not found" after winget: the installer sometimes skips PATH; add
#   C:\Program Files\Tesseract-OCR to PATH and reopen the terminal.
# Everything else matches the macOS / Linux recipe's common errors.
