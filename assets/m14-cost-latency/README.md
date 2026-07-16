# Module 13 — Cost, latency, reliability starter

Reference implementation of the runtime engineering patterns from
module 13. Per-task budget caps, fallback chains, latency tracking,
trace logging, and a tiny cost dashboard that reads from the same
trace store.

Drop the package into a project, wrap your LLM calls with `tracked()`,
and you get cost / latency / reliability instrumentation for free.

## What's in here

```
m13-cost-latency/
├── README.md
├── requirements.txt
├── tracking/
│   ├── __init__.py
│   ├── pricing.py            # token-cost table for common models
│   ├── tracer.py             # trace store (SQLite by default; swap to Postgres)
│   ├── budget.py             # BudgetCap + BudgetError
│   ├── fallback.py           # Fallback chain dispatcher
│   ├── health.py             # Health-check helpers
│   └── tracked.py            # @tracked decorator + context manager
├── examples/
│   ├── tracked_call.py       # wrap a single LLM call
│   ├── fallback_chain.py     # primary -> secondary -> tertiary
│   └── cost_dashboard.py     # SQL-backed cost dashboard
└── tests/
    ├── test_budget.py
    ├── test_fallback.py
    └── test_tracer.py
```

## Quick start

```bash
cd m13-cost-latency
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest

# Run the worked examples (uses fake clients; no API keys required)
python examples/tracked_call.py
python examples/fallback_chain.py
python examples/cost_dashboard.py
```

## Three patterns covered

### Per-task budget caps

```python
from tracking.budget import BudgetCap, BudgetError

cap = BudgetCap(
    max_input_tokens=50_000,
    max_output_tokens=2_000,
    max_turns=10,
    max_cost_cents=50,
    max_wall_seconds=15,
)

# Inside an agent loop
cap.check_input_tokens(input_count)
# ... model call ...
cap.add_cost(response.cost_cents)
cap.add_turn()
cap.check_wall()
```

### Fallback chains

```python
from tracking.fallback import FallbackChain

chain = FallbackChain([
    {"name": "primary",   "fn": call_opus},
    {"name": "secondary", "fn": call_sonnet},
    {"name": "tertiary",  "fn": call_local_llama},
])

result = chain.run(prompt)  # tries each in order; logs fallback events
```

### Trace logging + cost dashboard

```python
from tracking.tracer import Tracer
from tracking.tracked import tracked

tracer = Tracer(db_path="traces.db")

@tracked(tracer, agent="support_responder")
def respond(ticket: str) -> str:
    return call_model(ticket)

# Later
from examples.cost_dashboard import cost_by_agent
print(cost_by_agent(tracer, days=7))
```

## License

MIT.
