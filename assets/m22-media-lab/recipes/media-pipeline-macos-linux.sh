# DATED RECIPE: the m22 media pipeline environment on macOS / Linux.
# Status: macOS current, verified 2026-07-25 (macOS 15, Apple silicon, Python 3.12,
# ffmpeg 8.1, tesseract 5.5.3) by the Code With Vibes course team, end to end against
# the shipped fixture. Linux lines are canary: desk-checked, not yet run on a real
# machine; the commands are the distro-standard equivalents.
#
# Everything runs on CPU. No GPU, no account, no API key, no paid anything. First
# runs download open models over the network: whisper tiny is about 75 MB, small
# about 460 MB, the speaker-embedding model about 80 MB. Budget roughly 1 GB of
# disk for models plus the Python environment.
#
# These are commands to run one at a time and READ, not a script to execute.

# ---- system tools ----------------------------------------------------------
# macOS (Homebrew):
brew install ffmpeg tesseract
# Ubuntu / Debian (canary):
#   sudo apt update && sudo apt install -y ffmpeg tesseract-ocr python3-venv

ffmpeg -version        # expect: a recent major (tested against 8.1)
tesseract --version    # expect: 5.x

# ---- python environment, from assets/m22-media-lab/ ------------------------
python3 -m venv .venv
source .venv/bin/activate
pip install faster-whisper==1.2.1 silero-vad==6.2.1 speechbrain==1.1.0 scikit-learn==1.9.0
# torch arrives as a dependency of the two model packages; that is expected and
# is the big download in this step.

# ---- lesson 2: inspect the source, then make the working copy --------------
ffprobe -v error -show_format -show_streams fixture/maple-finch-support-call.mp4
# expect: one h264 video stream 960x540, one aac audio stream, duration 73.1

mkdir -p work
ffmpeg -y -v error -i fixture/maple-finch-support-call.mp4 \
  -ar 16000 -ac 1 -c:a pcm_s16le work/call-16k-mono.wav
# expect: work/call-16k-mono.wav, 16 kHz mono, about 2.3 MB. The source file is
# never overwritten; every tool reads the working copy.

# ---- lesson 3: segmentation, then the model and mode comparison ------------
python pipeline/vad_compare.py
# expect: work/segmentation-comparison.json; about 53s speech, 20s silence,
# and a list of fixed-window boundaries that land inside speech

python pipeline/transcribe.py --model tiny  --mode batch
python pipeline/transcribe.py --model small --mode batch
python pipeline/transcribe.py --model small --mode stream
# expect: three transcript records in work/; the stream run prints segments as
# they decode. First small run downloads the model; later runs are warm.

# ---- lesson 4: review the low-confidence spans -----------------------------
python pipeline/review_alignment.py
# expect: the review queue, lowest probability first, and the corrections.json
# format to fill in. After writing work/corrections.json, rerun the same
# command; expect work/transcript-reviewed.json with originals preserved.

# ---- lesson 5: anonymous speaker turns -------------------------------------
python pipeline/diarize.py
# expect: work/speaker-turns.json, 2-speaker turn list plus a review queue of
# short turns and ambiguous windows

# ---- lesson 6: frames and OCR ----------------------------------------------
python pipeline/sample_frames.py --cue 32.0 --cue 60.0
python pipeline/ocr_frames.py
# expect: work/frames/ plus frame-manifest.json and frame-ocr.json; all four
# scene cuts of the fixture appear with reason scene-change

# ---- lesson 7: join, then the deletion drill -------------------------------
python pipeline/join_transcript.py
# expect: work/transcript.json, schema-valid, with consent and retention filled

python pipeline/delete_derived.py           # dry run: lists everything derived
python pipeline/delete_derived.py --apply   # removes it and verifies nothing is left

# ---- stop / undo ------------------------------------------------------------
deactivate                      # leave the venv
# rm -rf .venv work            # removes the environment and all derived data;
#                                the fixture and the pipeline tools remain
# brew uninstall ffmpeg tesseract   # only if you installed them for this and
#                                     nothing else on your machine uses them

# ---- common errors ----------------------------------------------------------
# "not a 16 kHz mono 16-bit WAV": you skipped the normalize step, or pointed a
#   tool at the mp4. Every tool reads work/call-16k-mono.wav on purpose.
# "missing work/...": the tools declare their order; run the named prerequisite.
# "tesseract not found": install it with your package manager, then reopen the
#   terminal so PATH updates.
# Slow first transcription: that is the one-time model download, not the decode.
