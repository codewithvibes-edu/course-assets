"""Regenerate fixtures/golden/ from a live serve run.

Run this ONLY after an intentional change to the catalog, the fixtures, or
the protocol. The golden tests exist to make accidental changes loud; a
regeneration that follows a surprise test failure defeats the entire point
of gate 4.

    python3 scripts/make_goldens.py

Golden files hold configured, deterministic bytes only. This script
refuses to write a golden containing a PID or an observed_* field.
"""

import json
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

from support import Serve, pull  # noqa: E402

GOLDEN = ROOT / "fixtures" / "golden"
MODEL = "orchard-3b-instruct"
CANARY = "orchard-3b-instruct-canary"
RUN_ID = "golden-001"

DOC_REQUEST = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "Summarize the weekly status."}],
    "max_tokens": 64,
}

FORBIDDEN = (b'"pid"', b"observed_")


def capture():
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / ".orchard-runtime"
        pull(state)
        pull(state, CANARY)
        with Serve(state, RUN_ID, load_delay_ms=0, ttft_ms=0,
                   tokens_per_second=0) as serve:
            serve.wait_for_status("ready")
            base = f"http://127.0.0.1:{serve.port}"
            models = urllib.request.urlopen(base + "/v1/models",
                                            timeout=10).read()

            def post(stream):
                request = urllib.request.Request(
                    base + "/v1/chat/completions",
                    method="POST",
                    data=json.dumps(dict(DOC_REQUEST, stream=stream)).encode(),
                    headers={"Content-Type": "application/json"})
                return urllib.request.urlopen(request, timeout=30).read()

            return {
                "models-list.json": models,
                "chat-completion.json": post(False),
                "chat-completion.sse": post(True),
            }


def main():
    goldens = capture()
    GOLDEN.mkdir(parents=True, exist_ok=True)
    for name, data in goldens.items():
        for marker in FORBIDDEN:
            if marker in data:
                print(f"REFUSED {name}: golden bytes contain "
                      f"{marker.decode()}; goldens hold configured values "
                      "only, never process or timing observations")
                return 1
        (GOLDEN / name).write_bytes(data)
        print(f"wrote fixtures/golden/{name} bytes={len(data)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
