# Local-lane tested recipes (real lane)

The eleven-record registry from plan 06 section 5, real lane only; the three
mock fallback records live with the Orchard asset and overlay these, never
replace them.

All eleven records are authored. Status split (2026-07-25):

- CURRENT, executed start to finish on Cell A: local-v1-macos-apple-ollama,
  local-v1-macos-provider-adapter-swap, local-v1-macos-route-eval-and-rollback.
- CANARY, authored from the verified Cell A record plus vendor documentation,
  awaiting a start-to-finish run on real hardware: windows-nvidia-ollama (Cell B),
  windows-cpu-ollama (Cell C), ubuntu-nvidia-ollama (Cell D), ubuntu-cpu-ollama
  (Cell E), and the windows/ubuntu variants of the swap and eval records.

A canary record's expected outputs are desk expectations, labeled as such in the
record, and its last_verified date is the desk-check date (the schema requires a
date there); the on-OS verify replaces expectations with observations, refreshes
the date, and flips the status.

Pinned Cell A model at freeze: qwen3.5:2b (Ollama digest 324d162be6ca, upstream
Qwen/Qwen3.5-2B, Apache 2.0, Q8_0 GGUF, 2.7 GB artifact, course-validated 4096
context). The model THINKS by default; every record documents the handling
(reasoning_effort none on the compatible route, think false on the native one).

Validate any record against the course schema:

```sh
python3 assets/orchard-mock-runtime/scripts/validate_recipes.py --schema-only assets/local-lane-recipes/*.json
```

Freshness policy per plan 06: full retest within 30 days of publication, every
quarter while sold, and after runtime major releases, model revision changes,
OS majors, API-shape changes, or repeated learner failure reports. A stale
required recipe drops to canary or deprecated and pulls its module's verified
status with it.
