# Module 11 — MCP server starter

A minimal MCP (Model Context Protocol) server in Python using FastMCP.
Demonstrates the three primitives covered in module 11: tools, resources,
and prompts. Runs locally as a stdio subprocess for use with Claude
Desktop or any other MCP-compatible client.

## What's in here

```
m11-mcp-starter/
├── README.md              # this file
├── requirements.txt       # pinned deps
├── server.py              # the MCP server itself
├── notes.db.sql           # SQLite schema + seed data for the example
├── seed.py                # populate notes.db with sample data
├── claude_config.json.example   # Claude Desktop config snippet
└── tests/
    └── test_server.py     # basic smoke tests
```

## Quick start

```bash
cd m11-mcp-starter
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Seed the example notes database
python seed.py

# Run the server (stdio transport, talks to Claude Desktop)
python server.py
```

To use with Claude Desktop, copy `claude_config.json.example` into
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or the equivalent on Windows. Restart Claude Desktop.

## What the server exposes

Three primitives, all wired to a SQLite database of personal notes:

### Tools (3)

- `search_notes(query, limit)` — keyword search over note bodies
- `add_note(title, body)` — append a new note
- `count_notes_by_day()` — aggregation showing notes-per-day for the last 30 days

### Resources (1)

- `notes://recent` — the 10 most recent notes as plain text, for inclusion in prompts

### Prompts (1)

- `weekly_review` — a templated prompt that asks the model to summarize the week's notes

## Adapting to your data

The notes database is illustrative. To wrap your own data:

1. Replace `notes.db.sql` schema with yours.
2. Update the tool implementations in `server.py` to query your schema.
3. Adjust tool names + descriptions to match what your tools actually do.
4. Re-seed and restart.

The MCP protocol layer stays the same; only the underlying queries change.

## Distribution patterns

For internal tools: ship the server alongside an internal AI assistant; users
get it automatically. For public-facing tools: register with a public MCP
registry (mcp-registry, awesome-mcp). For ad-hoc personal use: a Git repo
with a one-line install command in the README.

## License

MIT.
