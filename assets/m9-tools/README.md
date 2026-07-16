# Module 9 — Tools library

Reference JSON Schema definitions for 20+ commonly-needed tools across
domains. Each tool is a complete `name + description + input_schema`
ready to paste into an Anthropic / OpenAI tool-use call.

These are educational starting points showing what good tool definitions
look like. Real implementations need to wire each tool to its underlying
service (CRM API, database, file system, etc.) per module 9.

## What's in here

```
m9-tools/
├── README.md
├── tools.json          # all 20+ tool definitions in one file, grouped by domain
└── examples/
    └── customer-support-agent.json   # example: agent using a subset of these tools
```

## Tool definition shape

Every tool follows this shape:

```json
{
  "name": "verb_object",
  "description": "Short, optimized for the model to decide WHEN to call. May span multiple sentences if the constraints are non-obvious.",
  "input_schema": {
    "type": "object",
    "properties": {
      "param_name": {
        "type": "string",
        "description": "What to pass. Optional for the model; required for clarity."
      }
    },
    "required": ["param_name"]
  }
}
```

## Conventions used

- **Names are verb_object format** (`lookup_customer`, `search_runbooks`). Clear, grep-able, easy for the model to choose.
- **Descriptions name the side-effects.** "Sends an email to the customer" appears in the description, not buried in implementation. The model and the calling user need to know.
- **Idempotency is documented.** Tools that are safe to call repeatedly say so; tools that aren't (like `process_refund`) say to avoid retries.
- **Strict enums where possible.** `severity: P0|P1|P2|P3` is a string enum; avoid free-form strings the model will improvise on.
- **Required fields explicit.** Optional parameters default sensibly; required ones are listed in `required`.
- **Examples in the description for non-obvious tools.** "Returns up to 5 tickets matching the query" is concrete; "search the ticketing system" is vague.

## Using a subset

Most agents use 3-7 tools from these domains, not all 20+. The
`examples/customer-support-agent.json` shows a 5-tool subset chosen for
that specific use case. Build narrow, scoped tool sets per agent rather
than handing every agent every tool.

## License

MIT. Use, adapt, ship. No attribution required.
