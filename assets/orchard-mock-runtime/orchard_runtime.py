#!/usr/bin/env python3
"""Orchard Mock Runtime: the course's zero-floor local fallback.

    The mock runtime does not think. It proves the operations: pull, serve,
    bind, measure, stop, restart, recover, swap, promote, and roll back.

Read that sentence twice, because it is the whole contract. This process is
a pretend local model server. It exists so a learner whose machine cannot
run a real small model can still perform every OPERATION the local pair
teaches, and save real evidence of having performed it.

What a mock run proves: that you pulled and verified an artifact, bound a
port, read a loopback address, watched a load delay, sent a request, read a
stream, hit a planted failure, recovered from it, swapped a connection by
configuration, and rolled back a promotion.

What a mock run can never prove: model quality, quantization quality, real
context behavior, real memory use, accelerator residency, driver health,
thermal behavior, or throughput on your hardware. Those need the real lane
or a read-along of the course's recorded real-recipe results. Every number
this process prints about memory and timing is a scenario you configured on
the command line, echoed back to you.

Standard library only. Offline. No credential. No trading content. It never
downloads a file, opens a non-loopback client connection, allocates fake
gigabytes, or shells out.

    python3 orchard_runtime.py pull orchard-3b-instruct --state-dir .orchard-runtime
    python3 orchard_runtime.py serve orchard-3b-instruct --state-dir .orchard-runtime --run-id local-001
    python3 orchard_runtime.py ps --state-dir .orchard-runtime
    python3 orchard_runtime.py stop --state-dir .orchard-runtime --run-id local-001

Windows uses `python` in place of `python3`. Everything else is identical.

Accessibility note: output is plain ASCII text, one fact per line, no color,
no cursor movement, and no animation. Progress is printed as discrete lines
rather than a redrawn bar, so a screen reader and a reduced-motion setting
both get the same information. `pull --quiet` drops the intermediate
progress lines entirely.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG_PATH = HERE / "catalog.json"
EVAL_CASES_PATH = HERE / "fixtures" / "eval-cases.json"

ARTIFACT_UNIT = b"ORCHARD MOCK ARTIFACT\n"
ARTIFACT_BYTES = 4096
GIB = 1073741824

EXIT_OK = 0
EXIT_INVALID = 2
EXIT_NO_RUN = 3
EXIT_MOCK_OOM = 4
EXIT_LOCK = 5

STOP_POLL_SECONDS = 0.05


# ---- output ---------------------------------------------------------------

def say(line):
    """Every learner-visible runtime line begins with MOCK. No exceptions,
    so a learner can grep this process out of any transcript."""
    print(f"MOCK {line}", flush=True)


def error(code, explanation, extra=None):
    """Errors carry the word mock in the code AND in the explanation, so a
    pasted error can never be mistaken for a real runtime's error."""
    say(f"ERROR {code}" + (f" {extra}" if extra else ""))
    say(f"ERROR {explanation}")


# ---- catalog and fixtures --------------------------------------------------

def load_catalog(path=None):
    return json.loads(Path(path or CATALOG_PATH).read_text())


def load_eval_cases(path=None):
    return json.loads(Path(path or EVAL_CASES_PATH).read_text())


def normalize_text(text):
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def build_fixture_index(catalog, eval_cases):
    """Map normalized input text to a per-model fixture result. The index is
    data, not inference: every value was typed by a human into a JSON file."""
    index = {}
    for case in eval_cases["cases"]:
        key = normalize_text(case["input"])
        index[key] = {model: payload["fixture_result"]
                      for model, payload in case["outputs"].items()}
    for text, result in catalog.get("generic_fixtures", {}).items():
        index.setdefault(normalize_text(text), {})
        for model in catalog["models"]:
            index[normalize_text(text)].setdefault(model, result)
    return index


def word_count(text):
    """The mock's only counting rule: whitespace-separated words. This is
    NOT a tokenizer result and no token-efficiency conclusion may rest on
    it. It exists because the canonical contract needs a usage number."""
    return len(text.split())


def fixture_result_for(model, messages, index, catalog):
    prompt_key = normalize_text(last_user_text(messages))
    entry = index.get(prompt_key)
    if entry and model in entry:
        return entry[model]
    joined = "\n".join(m.get("content", "") for m in messages)
    digest = hashlib.sha256(
        f"{catalog['fixture_version']}|{model}|{normalize_text(joined)}".encode()
    ).hexdigest()[:8]
    return catalog["generic_pattern"].format(words=word_count(joined), digest=digest)


def last_user_text(messages):
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return messages[-1].get("content", "") if messages else ""


def build_content(model, messages, max_tokens, index, catalog):
    """Content is prefix plus fixture line, always. The prefix is not
    decoration: it is the guardrail that stops fixture prose from being
    quoted anywhere as model output."""
    result = fixture_result_for(model, messages, index, catalog)
    content = f"{catalog['content_prefix']}\nfixture={result}"
    words = content.split()
    if max_tokens is not None and len(words) > max_tokens:
        return " ".join(words[:max_tokens]), "length"
    return content, "stop"


def chunk_content(content):
    """Deterministic word chunks whose concatenation is exactly the content.
    Same content in, same event boundaries and same bytes out, every run."""
    return re.findall(r"\S+\s*", content)


def request_fingerprint(run_id, model, messages, max_tokens, stream, fixture_version):
    normalized = json.dumps({
        "fixture_version": fixture_version,
        "run_id": run_id,
        "model": model,
        "messages": [{"role": m.get("role"), "content": m.get("content")}
                     for m in messages],
        "max_tokens": max_tokens,
        "stream": bool(stream),
    }, sort_keys=True)
    return "mockreq_" + hashlib.sha256(normalized.encode()).hexdigest()[:12]


# ---- state -----------------------------------------------------------------

def artifact_dir(state_dir, model):
    return Path(state_dir) / "artifacts" / model


def runs_dir(state_dir):
    return Path(state_dir) / "runs"


def run_state_path(state_dir, run_id):
    return runs_dir(state_dir) / f"{run_id}.json"


def stop_request_path(state_dir, run_id):
    return runs_dir(state_dir) / f"{run_id}.stop"


def write_atomic(path, text):
    """Write temp, then rename. A reader never sees a half-written file,
    which is the same discipline the daily-driver checkpoint fixture uses."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def write_run_state(state_dir, state):
    write_atomic(run_state_path(state_dir, state["run_id"]),
                 json.dumps(state, indent=2) + "\n")


def read_run_state(state_dir, run_id):
    path = run_state_path(state_dir, run_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except (OSError, ValueError):
        return False
    return True


def pulled_models(state_dir):
    root = Path(state_dir) / "artifacts"
    if not root.is_dir():
        return []
    return sorted(child.name for child in root.iterdir()
                  if (child / "manifest.json").exists())


# ---- pull -------------------------------------------------------------------

def artifact_payload():
    repeats = ARTIFACT_BYTES // len(ARTIFACT_UNIT) + 2
    return (ARTIFACT_UNIT * repeats)[:ARTIFACT_BYTES]


def payload_sha256():
    return hashlib.sha256(artifact_payload()).hexdigest()


def cmd_pull(args):
    catalog = load_catalog()
    model = args.model
    if model not in catalog["models"]:
        error("mock_unknown_model",
              "this mock catalog does not contain that model; run "
              "`python3 orchard_runtime.py pull --help` and use a catalog name",
              f"model={model} known={','.join(sorted(catalog['models']))}")
        return EXIT_INVALID

    spec = catalog["models"][model]
    target = artifact_dir(args.state_dir, model)
    lock = target / ".lock"
    display = f"{args.state_dir}/artifacts/{model}"

    if lock.exists():
        holder = read_lock(lock)
        alive = pid_alive(holder.get("pid"))
        if alive:
            error("mock_artifact_lock_held",
                  "another mock pull holds this artifact lock and is still "
                  "running; wait for it or stop that process first",
                  f"model={model} pid={holder.get('pid')} pid_alive=true")
            return EXIT_LOCK
        if not args.recover_stale_lock:
            error("mock_stale_artifact_lock",
                  "this mock lock names a fixture process that is not "
                  "running, and this mock command refuses to guess whether "
                  "the artifact is complete",
                  f"model={model} pid={holder.get('pid')} pid_alive=false")
            say(f"recover: python3 orchard_runtime.py pull {model} "
                f"--state-dir {args.state_dir} --recover-stale-lock")
            return EXIT_LOCK
        say(f"recover stale lock model={model} pid={holder.get('pid')} pid_alive=false")
        lock.unlink()
        say("recover removed only this model's mock lock; other artifacts untouched")

    payload_file = target / "payload.bin"
    manifest_file = target / "manifest.json"
    if payload_file.exists() and manifest_file.exists():
        actual = hashlib.sha256(payload_file.read_bytes()).hexdigest()
        expected = payload_sha256()
        say("NOTICE no model weights will be downloaded")
        say(f"pull model={model} revision={spec['revision']}")
        say(f"verify sha256={actual} status={'match' if actual == expected else 'mismatch'}")
        if actual != expected:
            error("mock_artifact_corrupt",
                  "the mock payload on disk does not match the fixed fixture "
                  "checksum; delete the artifact directory and pull again",
                  f"model={model}")
            return EXIT_INVALID
        say(f"cached artifact={display} actual_payload_bytes={payload_file.stat().st_size}")
        say("complete no rewrite performed")
        return EXIT_OK

    target.mkdir(parents=True, exist_ok=True)
    write_atomic(lock, json.dumps(
        {"mock": True, "model": model, "pid": os.getpid(),
         "note": "held by a running mock pull"}, indent=2) + "\n")
    try:
        say("NOTICE no model weights will be downloaded")
        say(f"pull model={model} revision={spec['revision']}")
        declared = spec["declared_mock_size_bytes"]
        declared_gib = declared / GIB
        if not args.quiet:
            for percent in (0, 25, 50, 75, 100):
                done = declared_gib * percent / 100
                say(f"progress={percent}% declared={done:.2f}/{declared_gib:.2f} GiB")
        payload = artifact_payload()
        tmp = payload_file.with_name(payload_file.name + ".tmp")
        tmp.write_bytes(payload)
        os.replace(tmp, payload_file)
        digest = hashlib.sha256(payload).hexdigest()
        write_atomic(manifest_file, json.dumps({
            "mock": True,
            "schema_version": 1,
            "model_id": model,
            "revision": spec["revision"],
            "fixture_version": load_catalog()["fixture_version"],
            "actual_payload_bytes": len(payload),
            "declared_mock_size_bytes": declared,
            "sha256": digest,
            "format_or_quant": spec["format_or_quant"],
            "note": "Pretend course fixture. No weights, no vendor, no license claim.",
        }, indent=2) + "\n")
        say(f"artifact={display}")
        say(f"actual_payload_bytes={len(payload)} declared_mock_size_bytes={declared}")
        say(f"sha256={digest}")
        say("complete this artifact proves pull and verification mechanics only")
    finally:
        if lock.exists():
            lock.unlink()
    return EXIT_OK


def read_lock(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return {}


# ---- HTTP surface ------------------------------------------------------------

class OrchardServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False


class OrchardHandler(BaseHTTPRequestHandler):
    """One narrow, compatible-SHAPED subset: three routes, nothing else.

    Compatible-shaped is not compatible. This server answers the three
    routes the course uses and rejects everything else explicitly, which is
    exactly the claim the module asks you to test against a real runtime
    rather than believe from a README.
    """

    protocol_version = "HTTP/1.1"
    server_version = "OrchardMockRuntime/1"
    sys_version = ""

    # ---- plumbing ---------------------------------------------------

    @property
    def config(self):
        return self.server.orchard

    def log_message(self, fmt, *args):
        if self.config["verbose"]:
            print(f"MOCK request {self.address_string()} {fmt % args}", flush=True)

    def send_json(self, status, payload, request_id):
        body = (json.dumps(payload, indent=2) + "\n").encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Request-Id", request_id)
        self.send_header("X-Mock-Runtime", "orchard")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status, error_type, message, request_id="mockreq_none"):
        self.send_json(status, {
            "error": {"type": error_type, "message": message},
            "mock": True,
        }, request_id)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw or b"{}"), None
        except json.JSONDecodeError as err:
            return None, str(err)

    # ---- routes ------------------------------------------------------

    def do_GET(self):
        if self.path.rstrip("/") == "/v1/models":
            return self.handle_models()
        self.send_error_json(
            404, "not_found",
            f"This mock runtime does not serve {self.path}. It serves "
            "GET /v1/models and POST /v1/chat/completions and nothing else.")

    def do_POST(self):
        if self.path.rstrip("/") == "/v1/chat/completions":
            return self.handle_completions()
        self.send_error_json(
            404, "not_found",
            f"This mock runtime does not serve {self.path}. It serves "
            "GET /v1/models and POST /v1/chat/completions and nothing else.")

    def handle_models(self):
        models = pulled_models(self.config["state_dir"])
        self.send_json(200, {
            "object": "list",
            "data": [{"id": name, "object": "model", "owned_by": "course-mock"}
                     for name in models],
            "mock": True,
        }, "mockreq_models000")

    def handle_completions(self):
        config = self.config
        body, parse_error = self.read_json_body()
        if parse_error is not None:
            return self.send_error_json(
                400, "invalid_request",
                f"This mock request body is not valid JSON: {parse_error}")
        if not isinstance(body, dict):
            return self.send_error_json(
                400, "invalid_request",
                "This mock runtime expects a JSON object body.")

        for field in ("tools", "tool_choice", "functions", "response_format"):
            if body.get(field) is not None:
                return self.send_error_json(
                    400, "unsupported_feature",
                    f"This mock runtime declares '{field}' unsupported. Its "
                    "capabilities are text and streaming only. An absent "
                    "feature is a stated fact here, not a surprise at call "
                    "time.")

        model = body.get("model")
        if model != config["model"]:
            return self.send_error_json(
                404, "not_found",
                f"This mock run serves '{config['model']}'. No model "
                f"'{model}' is loaded here. Check GET /v1/models.")

        messages = body.get("messages")
        if not isinstance(messages, list) or not messages:
            return self.send_error_json(
                400, "invalid_request",
                "This mock request needs a non-empty 'messages' array.")
        for message in messages:
            if not isinstance(message, dict) or "content" not in message:
                return self.send_error_json(
                    400, "invalid_request",
                    "Every message in this mock request needs a role and a "
                    "content field.")
            if not isinstance(message.get("content"), str):
                return self.send_error_json(
                    400, "unsupported_feature",
                    "This mock runtime accepts text content only. Non-text "
                    "and image content are declared unsupported.")

        prompt_words = sum(word_count(m["content"]) for m in messages)
        limit = config["context_word_limit"]
        if prompt_words > limit:
            return self.send_error_json(
                400, "fixture_context_limit",
                f"This mock request is {prompt_words} whitespace words and "
                f"the fixture word limit is {limit}. This is a configurable "
                "fixture limit, not a validated model context window.")

        max_tokens = body.get("max_tokens")
        if max_tokens is not None and (not isinstance(max_tokens, int) or max_tokens < 1):
            return self.send_error_json(
                400, "invalid_request",
                "This mock request needs 'max_tokens' to be a positive integer.")

        content, finish_reason = build_content(
            model, messages, max_tokens, config["index"], config["catalog"])
        request_id = request_fingerprint(
            config["run_id"], model, messages, max_tokens,
            body.get("stream"), config["catalog"]["fixture_version"])
        usage = {
            "prompt_tokens": prompt_words,
            "completion_tokens": word_count(content),
            "total_tokens": prompt_words + word_count(content),
        }
        if body.get("stream"):
            return self.stream_completion(request_id, model, content,
                                          finish_reason, usage)
        time.sleep(config["ttft_ms"] / 1000.0)
        self.send_json(200, {
            "id": request_id,
            "object": "chat.completion",
            "created": 0,
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": finish_reason,
            }],
            "usage": usage,
            "mock": {
                "thinking": False,
                "usage_unit": "whitespace_words",
                "timing_source": "configured scenario",
            },
        }, request_id)

    def stream_completion(self, request_id, model, content, finish_reason, usage):
        config = self.config
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Request-Id", request_id)
        self.send_header("X-Mock-Runtime", "orchard")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

        def emit(text):
            data = text.encode()
            self.wfile.write(f"{len(data):X}\r\n".encode() + data + b"\r\n")
            self.wfile.flush()

        def event(payload):
            emit("data: " + json.dumps(payload, separators=(",", ":")) + "\n\n")

        rate = config["tokens_per_second"]
        gap = 1.0 / rate if rate > 0 else 0.0
        try:
            time.sleep(config["ttft_ms"] / 1000.0)
            for position, piece in enumerate(chunk_content(content)):
                if position:
                    time.sleep(gap)
                event({
                    "id": request_id,
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": model,
                    "choices": [{"index": 0, "delta": {"content": piece},
                                 "finish_reason": None}],
                    "mock": True,
                })
            event({
                "id": request_id,
                "object": "chat.completion.chunk",
                "created": 0,
                "model": model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": finish_reason}],
                "usage": usage,
                "mock": {
                    "thinking": False,
                    "usage_unit": "whitespace_words",
                    "timing_source": "configured scenario",
                },
            })
            emit("data: [DONE]\n\n")
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            # The client walked away mid-stream. Canceling a stream is one of
            # the exercises, so this is a clean close, not a failure.
            if config["verbose"]:
                print("MOCK request client canceled the stream", flush=True)


# ---- serve --------------------------------------------------------------------

def cmd_serve(args):
    catalog = load_catalog()
    model = args.model
    if model not in catalog["models"]:
        error("mock_unknown_model",
              "this mock catalog does not contain that model",
              f"model={model} known={','.join(sorted(catalog['models']))}")
        return EXIT_INVALID

    spec = catalog["models"][model]
    if not (artifact_dir(args.state_dir, model) / "manifest.json").exists():
        error("mock_model_not_pulled",
              "pull the mock artifact before serving it; the pull step is "
              "where verification mechanics live",
              f"model={model}")
        say(f"next: python3 orchard_runtime.py pull {model} --state-dir {args.state_dir}")
        return EXIT_INVALID

    existing = read_run_state(args.state_dir, args.run_id)
    if existing and existing.get("status") != "stopped" and pid_alive(existing.get("pid")):
        error("mock_run_id_in_use",
              "another mock run already uses this run id; choose a different "
              "--run-id or stop that run first",
              f"run_id={args.run_id} pid={existing.get('pid')}")
        return EXIT_INVALID

    if args.memory_limit_mib is not None and args.reported_memory_mib > args.memory_limit_mib:
        error("mock_oom",
              "this mock run refused to start because the scenario memory "
              "you configured exceeds the limit you set; drop a size, lower "
              "the scenario, or raise the limit",
              f"required_scenario_mib={args.reported_memory_mib} "
              f"limit_mib={args.memory_limit_mib} no large allocation attempted")
        return EXIT_MOCK_OOM

    loopback = args.bind in ("127.0.0.1", "::1", "localhost")
    if not loopback:
        say(f"WARNING exposure drill: bind={args.bind} listens on every "
            "available interface")
        say("WARNING use fake fixture data only, inspect the bind, then stop "
            "this run")

    say(f"runtime={catalog['runtime']} fixture_version={catalog['fixture_version']}")
    say(f"run_id={args.run_id} model={model}")
    say(f"bind={args.bind}:{args.port} scope={'loopback' if loopback else 'all-interfaces'}")

    context_limit = (args.context_word_limit
                     if args.context_word_limit is not None
                     else spec["context_word_limit"])
    config = {
        "state_dir": args.state_dir,
        "run_id": args.run_id,
        "model": model,
        "catalog": catalog,
        "index": build_fixture_index(catalog, load_eval_cases()),
        "ttft_ms": args.ttft_ms,
        "tokens_per_second": args.tokens_per_second,
        "context_word_limit": context_limit,
        "verbose": args.verbose,
    }

    try:
        server = OrchardServer((args.bind, args.port), OrchardHandler)
    except OSError as err:
        if err.errno in (48, 98, 10048):        # EADDRINUSE across platforms
            error("mock_port_in_use",
                  "another process already listens on that address, so this "
                  "mock run did not start; pick a free port or stop the other "
                  "listener",
                  f"bind={args.bind}:{args.port}")
            return EXIT_INVALID
        error("mock_bind_failed",
              f"this mock run could not bind the address: {err}",
              f"bind={args.bind}:{args.port}")
        return EXIT_INVALID
    server.orchard = config

    def base_state(status):
        return {
            "mock": True,
            "run_id": args.run_id,
            "model": model,
            "status": status,
            "bind": args.bind,
            "port": args.port,
            "pid": os.getpid(),
            "reported_memory_mib": args.reported_memory_mib,
            "reported_memory_source": "scenario-not-measurement",
            "ttft_ms": args.ttft_ms,
            "tokens_per_second": args.tokens_per_second,
            "timing_source": "scenario-not-benchmark",
            "load_delay_ms": args.load_delay_ms,
            "context_word_limit": context_limit,
            "fixture_version": catalog["fixture_version"],
        }

    stop_path = stop_request_path(args.state_dir, args.run_id)
    if stop_path.exists():
        stop_path.unlink()

    def shutdown_during_load(reason):
        server.server_close()
        write_run_state(args.state_dir, base_state("stopped"))
        stop_path.unlink(missing_ok=True)
        say(f"shutdown reason={reason} run_id={args.run_id}")
        return EXIT_OK

    write_run_state(args.state_dir, base_state("loading"))
    try:
        stopped_during_load = wait_for_load(args.load_delay_ms, stop_path)
    except KeyboardInterrupt:
        # Ctrl+C during the load phase gets the same clean transition a stop
        # command gets. Interrupting a slow load is the common case, so it
        # cannot be the one path that leaves state behind.
        return shutdown_during_load("keyboard-interrupt")
    if stopped_during_load:
        return shutdown_during_load("stop-command-during-load")

    write_run_state(args.state_dir, base_state("ready"))
    say(f"reported_memory_mib={args.reported_memory_mib} source=scenario-not-measurement")
    say(f"ttft_ms={args.ttft_ms} tokens_per_second={args.tokens_per_second} "
        "source=scenario-not-benchmark")
    client_host = "127.0.0.1" if not loopback else args.bind
    say(f"ready base_url=http://{client_host}:{args.port}/v1")
    if not loopback:
        say("NOTICE 0.0.0.0 is a listen address, not a destination; clients "
            "still use 127.0.0.1, and firewall policy decides who else can "
            "reach this port")
    say("does not think; it proves the operations")
    say(f"stop with Ctrl+C or: python3 orchard_runtime.py stop "
        f"--state-dir {args.state_dir} --run-id {args.run_id}")

    reason = {"value": "stop-command"}

    def watch_stop():
        while True:
            if stop_path.exists():
                server.shutdown()
                return
            time.sleep(STOP_POLL_SECONDS)

    watcher = threading.Thread(target=watch_stop, daemon=True)
    watcher.start()

    try:
        server.serve_forever(poll_interval=STOP_POLL_SECONDS)
    except KeyboardInterrupt:
        reason["value"] = "keyboard-interrupt"
    finally:
        server.server_close()
        write_run_state(args.state_dir, base_state("stopped"))
        stop_path.unlink(missing_ok=True)
    say(f"shutdown reason={reason['value']} run_id={args.run_id}")
    return EXIT_OK


def wait_for_load(delay_ms, stop_path):
    """Print the load milestones and stay interruptible the whole time. A
    stop request during load must work, which is why this is a poll loop
    instead of one long sleep."""
    milestones = []
    for value in (0, delay_ms // 2, delay_ms):
        if value not in milestones:
            milestones.append(value)
    previous = 0
    for milestone in milestones:
        remaining = (milestone - previous) / 1000.0
        while remaining > 0:
            if stop_path.exists():
                return True
            step = min(STOP_POLL_SECONDS, remaining)
            time.sleep(step)
            remaining -= step
        say(f"loading={milestone}/{delay_ms} ms")
        previous = milestone
    return stop_path.exists()


# ---- ps ------------------------------------------------------------------------

def cmd_ps(args):
    rows = []
    directory = runs_dir(args.state_dir)
    if directory.is_dir():
        for path in sorted(directory.glob("*.json")):
            try:
                state = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            status = state.get("status", "unknown")
            if status in ("loading", "ready") and not pid_alive(state.get("pid")):
                status = "stale"
            rows.append((
                state.get("run_id", path.stem),
                state.get("model", "unknown"),
                status,
                f"{state.get('bind', '?')}:{state.get('port', '?')}",
                str(state.get("reported_memory_mib", "")),
            ))

    # Column widths grow to fit the longest value, never shrink below the
    # documented minimums. A table that shifts a column because one status
    # is a character longer is a table nobody can scan, on screen or through
    # a screen reader.
    minimums = (9, 21, 6, 14)
    widths = [max(floor, *(len(row[column]) for row in rows)) if rows else floor
              for column, floor in enumerate(minimums)]
    line = "  ".join(f"{{:<{width}}}" for width in widths) + "  {}"
    print(line.format("RUN_ID", "MODEL", "STATUS", "BIND", "REPORTED_MIB"))
    for row in rows:
        print(line.format(*row))
    say(f"rows={len(rows)} memory is scenario metadata, not measured process memory")
    return EXIT_OK


# ---- stop ------------------------------------------------------------------------

def cmd_stop(args):
    state = read_run_state(args.state_dir, args.run_id)
    if state is None:
        error("mock_run_not_found",
              "this mock state directory has no run with that id; check "
              "`ps` for the run ids it does have",
              f"run_id={args.run_id} state_dir={args.state_dir}")
        return EXIT_NO_RUN

    say(f"stop requested run_id={args.run_id}")

    if state.get("status") == "stopped":
        say(f"stopped run_id={args.run_id} status=already-stopped")
        return EXIT_OK

    if not pid_alive(state.get("pid")):
        # Never kill an unresolved PID. Clean up only this run's files.
        stop_request_path(args.state_dir, args.run_id).unlink(missing_ok=True)
        state["status"] = "stopped"
        state["recovered"] = True
        write_run_state(args.state_dir, state)
        say(f"stopped run_id={args.run_id} status=stale-state-recovered")
        return EXIT_OK

    write_atomic(stop_request_path(args.state_dir, args.run_id),
                 json.dumps({"mock": True, "run_id": args.run_id,
                             "requested_by_pid": os.getpid()}, indent=2) + "\n")

    deadline = time.monotonic() + args.timeout_s
    while time.monotonic() < deadline:
        current = read_run_state(args.state_dir, args.run_id)
        if current and current.get("status") == "stopped":
            say(f"stopped run_id={args.run_id} status=clean")
            return EXIT_OK
        if not pid_alive(state.get("pid")):
            say(f"stopped run_id={args.run_id} status=stale-state-recovered")
            return EXIT_OK
        time.sleep(STOP_POLL_SECONDS)

    error("mock_stop_timeout",
          "this mock run did not report a clean stop inside the timeout; the "
          "stop request file is still in place and the run will honor it",
          f"run_id={args.run_id} timeout_s={args.timeout_s}")
    return EXIT_INVALID


# ---- argument surface -----------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="orchard_runtime.py",
        description="Orchard Mock Runtime: a pretend local model server that "
                    "proves operations, never model behavior.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pull = subparsers.add_parser("pull", help="create the mock artifact and verify it")
    pull.add_argument("model")
    pull.add_argument("--state-dir", default=".orchard-runtime")
    pull.add_argument("--recover-stale-lock", action="store_true")
    pull.add_argument("--quiet", action="store_true",
                      help="drop the intermediate progress lines")
    pull.set_defaults(func=cmd_pull)

    serve = subparsers.add_parser("serve", help="run the mock HTTP surface")
    serve.add_argument("model")
    serve.add_argument("--state-dir", default=".orchard-runtime")
    serve.add_argument("--run-id", required=True)
    serve.add_argument("--bind", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8133)
    serve.add_argument("--load-delay-ms", type=int, default=1500)
    serve.add_argument("--reported-memory-mib", type=int, default=3584)
    serve.add_argument("--ttft-ms", type=int, default=250)
    serve.add_argument("--tokens-per-second", type=int, default=20)
    serve.add_argument("--memory-limit-mib", type=int, default=None)
    serve.add_argument("--context-word-limit", type=int, default=None)
    serve.add_argument("--verbose", action="store_true",
                       help="print one line per HTTP request")
    serve.set_defaults(func=cmd_serve)

    ps = subparsers.add_parser("ps", help="list mock runs in a state directory")
    ps.add_argument("--state-dir", default=".orchard-runtime")
    ps.set_defaults(func=cmd_ps)

    stop = subparsers.add_parser("stop", help="ask a mock run to stop cleanly")
    stop.add_argument("--state-dir", default=".orchard-runtime")
    stop.add_argument("--run-id", required=True)
    stop.add_argument("--timeout-s", type=float, default=10.0)
    stop.set_defaults(func=cmd_stop)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        say("interrupted")
        return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
