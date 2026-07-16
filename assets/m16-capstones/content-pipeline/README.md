# Capstone Track 3 — Content: multi-platform production pipeline

## Scenario

A content creator produces long-form content (videos, podcasts, essays).
They want to extract shorter pieces (clips, social posts, newsletter
blurbs) without duplicating the work. The pipeline ingests long-form,
identifies clip-worthy moments, generates platform-specific copy in the
creator's voice, queues posts for human review.

## Architecture

```
transcript JSON + prior posts archive
            │
            ▼
       data_layer.py
   (segmentation, M6 cleaning,
    SQLite store, voice RAG corpus)
            │
            ▼
         agent.py
   ┌────────────────────────────┐
   │  clip_scorer (Claude)      │
   │      │                      │
   │      ▼                      │
   │  caption_writer (Claude     │
   │      few-shot from voice    │
   │      examples)              │
   │      │                      │
   │      ▼                      │
   │  review_queue (no publish)  │
   └────────────────────────────┘
            │
            ▼
   human approves → external scheduler
```

## What's in here

```
content-pipeline/
├── README.md
├── requirements.txt
├── data_layer.py         # transcript ingest + cleaning + SQLite store
├── agent.py              # clip_scorer + caption_writer (Anthropic Messages API)
├── eval_set.yaml         # 8 eval cases
├── example.py            # runnable end-to-end
├── fixtures/
│   ├── transcript.json   # 8-segment sample transcript
│   └── voice_history.jsonl  # 7 prior posts (few-shot fodder)
└── src/                  # reference module pattern (heuristic baseline)
    ├── data.py
    ├── agents.py
    ├── eval.py
    └── main.py
```

## How to run

```bash
cd assets/m15-capstones/content-pipeline
pip install -r requirements.txt

# Optional: real Anthropic calls. Without this, fallback mode runs
# the deterministic heuristics so the example still completes.
export ANTHROPIC_API_KEY=sk-ant-...

# Walk through scoring + captioning + review queue
python example.py

# Run the eval set
python example.py --eval

# Score one segment by ID
python example.py --score seg-002
```

## In scope (v1)

- Transcript -> segmented + cleaned turns
- Clip scoring on a 1-10 scale with reasoning
- Caption generation per platform (X / IG / LinkedIn)
- Few-shot voice consistency drawn from a prior-posts archive
- Eval set with deterministic pass criteria (score ranges, caption-length bounds)
- Human review queue before any post is published

## Out of scope (v1)

- Real video editing (this works on transcripts only)
- Direct posting (human review queue is the final step; integrate
  with your own scheduler downstream)
- Fully autonomous voice cloning (requires per-creator training data)

## Build first

The clip identifier. Everything downstream depends on which moments
the system picks. Get the eval set + scorer right before adding
caption-generation flair.

## Migration notes

For a real production setup:

1. Replace `ingest_transcript` with Whisper output that carries
   word-level timestamps (Module 5 covers the patterns).
2. Replace SQLite with Postgres + pgvector if your voice corpus grows
   past a few thousand posts and you need real similarity retrieval
   (Module 7).
3. Wire `caption_writer` to your actual posting platform's draft queue
   (Buffer, Later, custom).
4. Add a per-post `audit_log` row when a human approves; Module 14
   covers patterns.

## Educational only

Reference code for learning the assembly. Posting on someone else's
behalf has consequences (FTC disclosure rules, platform ToS, audience
trust). Treat the review queue as load-bearing in any real deployment.
