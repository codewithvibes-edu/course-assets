# Module 16 — Capstone starter repos

Reference architectures for the 7 use-case tracks from module 15. Each
v1 track is a runnable starter showing the data layer, agent layer
(Anthropic Messages API), eval set, and end-to-end example for that
domain. Readers extend; the starter points at the right shape so they
do not start from zero.

## Tracks

Per the Phase 3 launch plan, 4 tracks ship at v1 and the remaining 3
ship as v1.1 over the following 60-90 days.

| #   | Track                                        | Status         |
| --- | -------------------------------------------- | -------------- |
| 1   | Business — CRM intelligence assistant        | v1             |
| 2   | Personal — calendar/email/notes life-OS      | v1.1 (planned) |
| 3   | Content — multi-platform production pipeline | v1             |
| 4   | Domain intelligence - daily brief generator  | v1             |
| 5   | Internal tooling — org-knowledge MCP server  | v1.1 (planned) |
| 6   | Ops — incident response copilot              | v1.1 (planned) |
| 7   | Research — paper-library research assistant  | v1             |

## What each v1 starter contains

```
m16-capstones/<track>/
├── README.md          # scenario, architecture, how to run
├── requirements.txt
├── data_layer.py      # data ingest + cleaning + storage
├── agent.py           # Anthropic Messages API agent loop
├── eval_set.yaml      # 8-10 eval cases with deterministic pass criteria
├── example.py         # runnable end-to-end (data_layer -> agent -> eval)
├── fixtures/          # realistic sample data
│   └── *.json, *.csv, *.jsonl
└── src/               # reference module pattern (heuristic baseline)
    ├── data.py
    ├── agents.py
    ├── eval.py
    └── main.py
```

The `src/` directory is the original heuristic-baseline scaffold; the
root-level `data_layer.py` / `agent.py` / `example.py` are the v1
substantive build with the Anthropic Messages API wired in. Both
ship; readers can compare the two as an instructive contrast.

## How to run any v1 starter

```bash
cd assets/m16-capstones/<track>
pip install -r requirements.txt

# Optional: real model calls. Without this, the agents fall back to
# deterministic heuristics so the example still runs end-to-end.
export ANTHROPIC_API_KEY=sk-ant-...

python example.py         # walkthrough on sample inputs
python example.py --eval  # run the YAML eval set
```

## Pattern that runs through all tracks

Every track follows the same shape (this is the point):

1. **Data layer first.** `data_layer.py` defines a canonical schema,
   ingests from realistic fixtures (JSON / CSV / JSONL), applies M6
   cleaning, and stores in SQLite. Real implementations swap the
   ingest source; the schema stays.
2. **Read-only operations first.** Tools the agent can call are
   read-only by default. Write operations (CRM updates, drafts,
   posts, publishes) route through a `propose_action` /
   `review_queue` payload that a human approves.
3. **Anthropic Messages API.** Agents use `claude-sonnet-4-7`-class
   models with tool-use loops bounded by `MAX_TOOL_ROUNDS` to prevent
   runaway cost (Module 13 pattern).
4. **Evals before scale.** `eval_set.yaml` has 8-10 cases with
   deterministic pass criteria. `python example.py --eval` runs
   them; a reader can verify the system works without an API key
   (fallback mode).
5. **Validation before publish.** Where applicable, output passes
   through a validator before reaching a user: claims linter
   (domain brief), citation validator (research), pending-action
   review queue (CRM, content).

## Voice + brand constraints

These starters are educational. They make no outcome promises. Where
applicable, publishing-responsibility or compliance comment blocks
appear at the top of relevant files. None of them name specific
real-world vendors or brands.

## License

MIT. Use, adapt, ship.
