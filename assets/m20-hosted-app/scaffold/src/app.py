"""The application. Two commands:

    python3 src/app.py summarize fixtures/sample-input.txt
    python3 src/app.py chat

`summarize` streams output to the terminal as it arrives, survives Ctrl+C
as a clean cancel, times out on its own budget, and logs usage without
logging content. `chat` keeps a bounded history and prints exactly what
state gets sent each turn, because the API remembers nothing and the app
should never pretend otherwise.

Configuration comes from the environment (.env, loaded by hand below to
stay standard-library only). Defaults point at the Module 19 lab service.
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import client
import state
import usage_log


def load_env():
    """Tiny .env loader: KEY=VALUE lines, no quoting games. Real projects
    use python-dotenv; the lesson here is only WHERE values live."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def settings():
    return {
        "base_url": os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8124"),
        "api_key": os.environ.get("MODEL_API_KEY", "mock-key-local-only"),
        "model": os.environ.get("MODEL_NAME", "mock-1"),
        "timeout_s": float(os.environ.get("APP_TIMEOUT_S", "15")),
        "max_turns": int(os.environ.get("APP_MAX_TURNS", "6")),
        "max_input_chars": int(os.environ.get("APP_MAX_INPUT_CHARS", "20000")),
    }


def summarize(path):
    cfg = settings()
    text = Path(path).read_text(encoding="utf-8")
    if len(text) > cfg["max_input_chars"]:
        print(f"refused: input is {len(text)} chars; the contract caps it at "
              f"{cfg['max_input_chars']}. Split the file or raise the limit "
              "in the contract first, on purpose.")
        return 1

    started = time.monotonic()
    request_id = None
    usage = {}
    outcome = "ok"
    printed_anything = False
    try:
        for event in client.stream_generate(
            cfg["base_url"], cfg["api_key"], cfg["model"], text, cfg["timeout_s"]
        ):
            if event[0] == "delta":
                # Partial text is safe to DISPLAY. It is not safe to save,
                # parse, or act on; only the done event makes it an answer.
                print(event[1], end="", flush=True)
                printed_anything = True
            else:
                usage, request_id = event[1], event[2]
        print()
    except KeyboardInterrupt:
        outcome = "canceled"
        print("\n[canceled by you; partial text above is partial]")
    except client.ClientError as err:
        outcome = err.kind
        request_id = err.request_id
        if printed_anything:
            print()
        detail = f" (request {err.request_id})" if err.request_id else ""
        wait = f" Retry after {err.retry_after}s." if err.retry_after else ""
        print(f"failed: {err.kind}: {err}{detail}{wait}")

    usage_log.record(
        route="summarize", model=cfg["model"],
        latency_s=time.monotonic() - started,
        usage=usage, request_id=request_id, outcome=outcome,
    )
    print(f"[logged: outcome={outcome}, latency="
          f"{time.monotonic() - started:.2f}s, content=absent]")
    return 0 if outcome == "ok" else 1


def chat():
    cfg = settings()
    history = state.BoundedHistory(cfg["max_turns"])
    print(f"bounded chat against {cfg['base_url']} "
          f"(history cap: {cfg['max_turns']} turns; Ctrl+C or 'quit' to leave)")
    while True:
        try:
            line = input("you> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not line or line.lower() == "quit":
            break
        history.add("user", line)
        payload = {"model": cfg["model"], "messages": history.to_payload()}
        print(f"[sending {len(history)} turns; dropped so far: {history.dropped}]")
        started = time.monotonic()
        try:
            body, request_id = client.echo_request(
                cfg["base_url"], cfg["api_key"], payload, cfg["timeout_s"]
            )
        except client.ClientError as err:
            print(f"failed: {err.kind}: {err}")
            usage_log.record(route="chat", model=cfg["model"],
                             latency_s=time.monotonic() - started, usage={},
                             request_id=err.request_id, outcome=err.kind)
            continue
        # The lab service echoes what it received: the proof, every turn,
        # that the provider sees only what you sent and nothing older.
        echoed = body.get("received", {}).get("body", {}).get("messages", [])
        reply = f"(service saw exactly {len(echoed)} turns)"
        print(f"app> {reply}")
        history.add("assistant", reply)
        usage_log.record(route="chat", model=cfg["model"],
                         latency_s=time.monotonic() - started,
                         usage=body.get("usage", {}),
                         request_id=request_id, outcome="ok")
    return 0


def main(argv):
    load_env()
    if len(argv) >= 2 and argv[1] == "summarize" and len(argv) == 3:
        return summarize(argv[2])
    if len(argv) == 2 and argv[1] == "chat":
        return chat()
    print("usage: python3 src/app.py summarize <file> | chat")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
