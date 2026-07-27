# Module 19: API lab

The mock service, fixtures, worksheets, and recipes for the whole module.
Standard library only, local only, no keys, no cost. The one real-provider
file is optional and clearly marked.

## What's in here

```
m19-api-lab/
├── README.md                          # this file
├── mock_service.py                    # the lab service (port 8124)
├── worksheets/
│   ├── flow-diagram.md                # lesson 1
│   ├── annotated-request.md           # lesson 2
│   └── decision-tree.template.md      # lesson 5
├── fixtures/
│   ├── malformed/                     # lesson 3: five broken bodies + target + answer
│   └── responses/                     # lesson 5: the seven exhibits, captured raw
└── recipes/
    ├── raw-requests-macos-linux.sh    # dated: every command in the module (curl)
    ├── raw-requests-windows.ps1       # dated: same commands, curl.exe + PowerShell
    └── real-provider-examples.md      # dated, OPTIONAL: same anatomy, real services
```

## Start the lab

```sh
python3 mock_service.py        # Windows: python mock_service.py
```

It listens on `http://127.0.0.1:8124` and prints one log line per request.
Port 8124 on purpose: the Module 0 mock owns 8123 and both can run at
once. Stop it with Ctrl+C. If the port is busy, you diagnosed exactly this
in the setup lab (m0-11).

Endpoints:

| Endpoint | Method | What it teaches |
| --- | --- | --- |
| `/v1/echo` | POST | the request anatomy, reflected back at you |
| `/v1/error/<kind>` | GET or POST | the seven exhibits; kinds: bad-input, auth, forbidden, missing, rate-limit, server |
| `/v1/stream` | POST | events arriving one at a time; cancel with Ctrl+C |
| `/v1/slow` | POST | 8 seconds of nothing, so your timeout fires |

`/v1/echo`, `/v1/stream`, and `/v1/slow` want the lab key:
`Authorization: Bearer mock-key-local-only`. The error exhibits answer
without it; they are museum pieces.

The `fixtures/responses/` files are raw captures of each exhibit, saved
with `curl -i`, for reading offline or comparing against what you got
live. Byte-for-byte identical except the date and request ID, which is
itself worth noticing: request IDs are per-request, that is their job.
