# Capstone Track 1 — Business: CRM intelligence assistant

## Scenario

A sales / customer success team has hundreds of accounts in a CRM.
Information about each account is scattered across notes, emails,
support tickets, contract docs, billing records. The team needs answers
to questions like "what is the latest with account X" or "which
renewals are at risk in the next 60 days" without reading 50 notes
per account.

## Architecture

```
CRM API + tickets + notes
            │
            ▼
        data_layer.py
   (typed schema, SQLite cache, M4-M6 patterns)
            │
            ▼
         agent.py
   (Anthropic Messages API tool-use loop;
    M9 single-agent + tools pattern)
            │
            ▼
   answer with citations
   + pending_action queue
   (human-approves writes; M14)
```

## What's in here

```
business-crm/
├── README.md
├── requirements.txt
├── data_layer.py         # ingest + clean + SQLite store
├── agent.py              # Anthropic tool-use agent
├── eval_set.yaml         # 8 eval cases
├── example.py            # runnable end-to-end
├── fixtures/
│   ├── accounts.json     # 6 sample accounts
│   ├── tickets.csv       # 12 sample tickets
│   └── notes.jsonl       # 10 sample notes
└── src/                  # reference module pattern (heuristic baseline)
    ├── data.py
    ├── agents.py
    ├── eval.py
    └── main.py
```

## How to run

```bash
cd assets/m15-capstones/business-crm
pip install -r requirements.txt

# Optional: real Anthropic calls. Without this, falls back to a
# deterministic stub so the example still runs end-to-end.
export ANTHROPIC_API_KEY=sk-ant-...

# Walk through the sample questions
python example.py

# Run the eval set
python example.py --eval

# Ask a one-off
python example.py --query "What's the latest with ACME?"
```

## In scope (v1)

- Read-only Q&A: "what's the latest with account X"
- Portfolio queries: "which renewals are at risk in 60 days"
- Citation-grounded responses (account ID + source field)
- Eval set of 8 hand-written queries with deterministic pass criteria
- Pending-action payloads for any non-read intent (human reviews)

## Out of scope (v1)

- Writing to the CRM (notes, status changes, deals) - those go through
  `propose_action` and a human approves before execution
- Sending customer-facing email
- Multi-step write workflows
- CRM-specific UI; this is an API + agent only

## Build first

The CRM read adapter. A single `assemble_account_context(account_id)`
plus a search-by-name function covers 80% of the value. Write
operations come later and always go through human approval.

## Migration notes

For a real CRM (Salesforce, HubSpot, Attio, custom):

1. Replace the `ingest_*` functions in `data_layer.py` with the CRM's
   API client. Keep the canonical `Account` / `Ticket` / `Note`
   dataclasses unchanged so the agent code doesn't need to know.
2. Swap SQLite for Postgres + pgvector once you need RAG over note bodies
   (module 7).
3. Replace the keyword fallback in `agent.py` with an actual LLM call
   for any specialist that needs reasoning instead of lookup. The tool
   schemas stay the same.

## Educational only

This is reference code for learning. Hooking it up to a real CRM with
write permissions has real-world consequences. Do not treat the
demo's pending-action review as a substitute for real authorization
in a production system.
