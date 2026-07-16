# Module 10 — Multi-agent starter

Reference Python implementation of the supervisor pattern from module 10.
A 3-specialist customer support system orchestrated by a supervisor
agent, with shared state, conditional routing, and a human-in-loop
checkpoint for irreversible actions.

The patterns are framework-agnostic; the worked implementation uses
LangGraph because it is the dominant orchestration framework in 2026.
The same shape works in CrewAI, AutoGen, or raw Python.

## What's in here

```
m10-multi-agent-starter/
├── README.md
├── requirements.txt
├── agents/
│   ├── __init__.py
│   ├── state.py             # shared SupportState (TypedDict)
│   ├── supervisor.py        # classifies + routes
│   ├── billing.py           # billing specialist + tools
│   ├── technical.py         # technical specialist + tools
│   ├── escalation.py        # escalates to human; never resolves
│   └── tools.py             # tool implementations (placeholder; wire to real CRM)
├── graph.py                 # LangGraph wiring of the 5 nodes
├── examples/
│   ├── run_billing_case.py
│   └── run_outage_case.py
├── eval_set.yaml            # 8-entry eval set across categories
└── tests/
    ├── test_state.py
    ├── test_supervisor.py
    └── test_routing.py
```

## Quick start

```bash
cd m10-multi-agent-starter
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest

# Run worked examples (uses fake LLM clients; no API keys required)
python examples/run_billing_case.py
python examples/run_outage_case.py
```

## Architecture

```
User ticket
    │
    ▼
┌──────────────┐
│  Supervisor  │  classify(ticket) -> route based on category
└──────┬───────┘
       │
       ├──────────────┬──────────────┬──────────────┐
       ▼              ▼              ▼              ▼
   billing        technical      escalation     general
  specialist     specialist      specialist    (catch-all)
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                           │
                           ▼
                      Final answer
```

Each specialist has a narrow tool set:

- **billing**: `lookup_invoice`, `process_refund` (HUMAN APPROVAL), `update_payment_method`
- **technical**: `search_runbooks`, `check_service_status`, `create_bug_report`
- **escalation**: `summarize_for_human` (no resolution; routes to a queue)

## State contract

`agents/state.py` defines the shared state. Every node reads it; only
specific nodes write specific fields. This contract is the most
important thing to get right — agents that work against an undefined
state shape produce confusing bugs.

```python
class SupportState(TypedDict):
    user_input: str
    customer_id: str | None
    customer_data: dict | None
    classification: str | None         # 'billing' | 'technical' | 'escalation' | 'general'
    classification_confidence: float | None
    specialist_response: str | None    # written by the routed specialist
    pending_action: dict | None        # set by specialists for human-approval gates
    final_answer: str | None
    trace: list[dict]                  # per-step audit trail
```

## Human-in-loop pattern

Specialists that propose irreversible actions (refunds, deletes, sends
to customer) populate `state["pending_action"]` and return without
calling the action's tool. The graph terminates with `final_answer`
asking the user to approve. Approval flows back through a separate
graph entry point that executes the tool.

This means: the agent never autonomously sends a customer email or
processes a refund. Module 14 (safety) covers why.

## What this is NOT

- A working customer support system. The CRM tools are placeholders.
  Wire them to your real backend before treating it as a product.
- A complete LangGraph reference. The API has shifted across versions;
  this implementation works against the version pinned in
  requirements.txt. Verify against current LangGraph docs before
  upgrading.
- A guarantee that multi-agent beats single-agent for your use case.
  Module 10 covers when each pattern wins; pick deliberately.

## License

MIT.
