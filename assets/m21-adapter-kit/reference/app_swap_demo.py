"""The swap proof. One application, zero provider knowledge, and the
connection chosen by an environment variable:

    CWV_CONNECTION=fallback python3 app_swap_demo.py
    LAB_API_KEY=mock-key-local-only CWV_CONNECTION=primary python3 app_swap_demo.py

Run it both ways (start the Module 19 lab service for `primary`), save
both outputs side by side, and notice what changed between the runs:
one environment variable. Application code untouched. That record is the
module's acceptance evidence, and the whole reason the adapter exists.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from canonical import AdapterError, CanonicalRequest, Message
from registry import connect, require_capability

FIXED_INPUT = "In one sentence, what does an adapter buy an application?"


def main():
    logical_id = os.environ.get("CWV_CONNECTION", "fallback")
    print(f"connection: {logical_id} (a logical name; no provider in sight)")
    try:
        adapter, profile = connect(logical_id)
        print(f"profile: adapter={profile['adapter']}, "
              f"privacy_class={profile['privacy_class']}")
        require_capability(adapter, "text")
        response = adapter.generate(
            CanonicalRequest(messages=[Message("user", FIXED_INPUT)]))
    except AdapterError as err:
        print(f"failed: {err.category}: {err}")
        return 1

    print(f"content:       {response.content}")
    print(f"finish_reason: {response.finish_reason}")
    print(f"usage:         in={response.usage.input_tokens} "
          f"out={response.usage.output_tokens}")
    print(f"latency_s:     {response.latency_s:.3f}")
    print(f"request_id:    {response.request_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
