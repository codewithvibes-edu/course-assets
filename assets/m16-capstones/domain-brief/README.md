# Capstone Track 4 - Domain intelligence: daily brief generator

> **Publishing is on you.**
>
> A recurring brief published under your own name has concrete failure
> modes. Data feeds almost always carry a license that limits how much
> raw data you can republish; read it before your newsletter quotes the
> feed wholesale. Getting a fact wrong about a named business is a
> correction at best and a legal problem at worst, so keep a
> corrections policy and keep the human-review step for anything that
> names a real company. This starter makes mistakes faster to publish;
> it does not make them safe.

## Scenario

A domain expert (analyst, journalist, researcher) produces a daily
brief synthesizing several data sources on an industry they know cold.
The running example: commercial construction permits in one metro
area. The pipeline pulls fresh permit filings, inspection results, and
zoning/variance calendar items, structures them, generates the brief
in the expert's voice, and drops it in a review queue for a human to
approve before publish. Swap in your own niche; the shape is
identical.

The brief answers the questions the analyst's readers actually have:
what got filed, which projects moved, which stalled, and what to watch
this week.

## Architecture

```
data feeds (permit aggregator + city open data + your brief archive)
                │
                ▼
       data_layer.py
   (canonical schema, M6 cleaning,
    SQLite store, accuracy-weighted
    voice RAG corpus)
                │
                ▼
         agent.py
   ┌──────────────────────────────┐
   │  analysis_agent (Claude)     │
   │      │                       │
   │      ▼                       │
   │  synthesis_agent (Claude,    │
   │      few-shot from prior     │
   │      briefs, accuracy-       │
   │      weighted)               │
   │      │                       │
   │      ▼                       │
   │  validate_brief              │
   │      (claims linter)         │
   └──────────────────────────────┘
                │
                ▼
   review queue (human approves before publish)
```

## What's in here

```
domain-brief/
├── README.md
├── requirements.txt
├── data_layer.py         # permits + inspections + zoning + brief-archive ingest
├── agent.py              # analysis + synthesis + claims linter
├── eval_set.yaml         # 10 cases: structural + linter
├── example.py            # runnable end-to-end
├── fixtures/
│   ├── permits.csv            # permit filings feed snapshot
│   ├── inspections.csv        # recent inspection results
│   ├── zoning.csv             # upcoming zoning/variance calendar items
│   ├── history.csv            # 10 prior periods with labeled outcomes
│   └── brief_archive.jsonl    # 4 past briefs (accuracy-weighted voice RAG)
└── src/                  # reference module pattern (heuristic baseline)
```

## How to run

```bash
cd assets/m16-capstones/domain-brief
pip install -r requirements.txt

# Optional: real Anthropic calls. Without this, fallback mode runs the
# deterministic heuristics so the example still produces a brief.
export ANTHROPIC_API_KEY=sk-ant-...

# Generate today's brief
python example.py

# Run the eval set (structural + linter)
python example.py --eval

# Generate then explicit-fail on linter issues
python example.py --validate
```

## In scope (v1)

- Data ingest from three sources: permit filings (paid-aggregator
  placeholder CSV), inspection results, zoning/variance calendar
- Activity-pattern tagging (permit surge, seasonal slowdown, approval
  backlog) with similar-period lookup and labeled outcomes (did the
  noted project advance or stall)
- Accuracy-weighted voice retrieval: past briefs whose calls held up
  on later review get retrieval preference
- Claims linter on every draft: every named business needs a permit id
  citation, every cited id needs a data row, no unsupported
  superlatives, mandatory data-gap disclosure
- Code-generated gap disclosure when a feed fails to load, so the
  brief discloses the gap instead of synthesizing around it
- Human review queue (every brief is `needs_human_review=true`)

## Out of scope (v1)

- Autopublish (every brief goes through human review, no exceptions)
- MCP server exposing the data feed (lesson extension)
- Subscriber management (handled by your newsletter platform)

## Claims-linter posture

The synthesis system prompt explicitly requires:

- Every named business or project cites its permit id in the same
  sentence. No id, no mention.
- No claim about a project without a corresponding data row.
- No superlatives the feed cannot prove ("largest", "first-ever",
  "record-breaking", "unprecedented").
- A closing "Data gaps" line that discloses missing or stale feeds.

The linter enforces all four deterministically on every draft, whether
or not the LLM ran. Module 14 (Safety) covers the patterns at depth;
this starter wires them into the pipeline.

## Build first

The data layer + the eval set. Get those right before the synthesis
agent so you can grade prompt changes against historical inputs.

## Migration notes

For a real feed + archive:

1. Replace `ingest_permits` with the paid-aggregator API client (with
   retries + idempotency from Module 5) and the inspection/zoning
   ingests with city open-data portal clients.
2. Replace `find_similar_periods` with vector similarity over a
   Postgres archive of prior daily snapshots (Module 7 RAG).
3. Score each published brief after the fact (did its calls hold up?)
   and write the accuracy back to the archive so the voice retrieval
   keeps favoring the briefs that got it right.
4. Wire `audit_log` writes for every published brief (Module 14).
5. Add cost dashboards (Module 13) once you have non-trivial volume.

## Educational only

Reference code for learning. Read the publishing-responsibility
comment block at the top of `data_layer.py` and `agent.py` before
putting anything like this in front of readers.
