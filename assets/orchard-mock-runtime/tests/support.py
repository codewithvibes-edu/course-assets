"""Shared test plumbing: start a mock run, wait for it, tear it down.

Not a test file. Every test module imports this so that starting and
stopping a real out-of-process server is one line instead of twenty, and so
that a hung test kills its own child instead of leaking it into your
session.
"""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "orchard_runtime.py"
PLANT = ROOT / "scripts" / "plant_failure.py"

READY_TIMEOUT_S = 20.0


def clean_env():
    """Provider and model environment variables unset, per the build
    contract. A test that passes only because your shell had a key in it is
    not a test."""
    env = dict(os.environ)
    for name in list(env):
        if any(token in name.upper() for token in
               ("API_KEY", "OPENAI", "ANTHROPIC", "OLLAMA", "MODEL", "CWV_")):
            env.pop(name, None)
    env["PYTHONUNBUFFERED"] = "1"
    return env


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(RUNTIME), *args],
        capture_output=True, text=True, env=clean_env(),
        cwd=str(cwd or ROOT), timeout=60)


def plant(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(PLANT), *args],
        capture_output=True, text=True, env=clean_env(),
        cwd=str(cwd or ROOT), timeout=60)


class Serve:
    """A serve run with its stdout on disk, so a test can assert on the
    transcript the learner would see."""

    def __init__(self, state_dir, run_id, model="orchard-3b-instruct",
                 port=None, log_name=None, **flags):
        self.state_dir = Path(state_dir)
        self.run_id = run_id
        self.model = model
        self.port = port or free_port()
        self.log_path = self.state_dir.parent / (log_name or f"{run_id}.log")
        self.flags = flags
        self.process = None

    def start(self):
        args = [sys.executable, str(RUNTIME), "serve", self.model,
                "--state-dir", str(self.state_dir), "--run-id", self.run_id,
                "--port", str(self.port)]
        for name, value in self.flags.items():
            flag = "--" + name.replace("_", "-")
            if value is True:
                args.append(flag)
            elif value is not None:
                args += [flag, str(value)]
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = open(self.log_path, "w")
        self.process = subprocess.Popen(
            args, stdout=self.handle, stderr=subprocess.STDOUT,
            env=clean_env(), cwd=str(ROOT))
        return self

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.port}/v1"

    def state(self):
        path = self.state_dir / "runs" / f"{self.run_id}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return None

    def wait_for_status(self, status, timeout=READY_TIMEOUT_S):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            current = self.state()
            if current and current.get("status") == status:
                return current
            if self.process.poll() is not None and status != "stopped":
                raise AssertionError(
                    f"serve exited early ({self.process.returncode}):\n{self.log()}")
            time.sleep(0.05)
        raise AssertionError(
            f"run {self.run_id} never reached {status}:\n{self.log()}")

    def wait_for_exit(self, timeout=READY_TIMEOUT_S):
        try:
            return self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            raise AssertionError(f"serve did not exit:\n{self.log()}")

    def log(self):
        try:
            self.handle.flush()
        except (AttributeError, ValueError):
            pass
        return self.log_path.read_text() if self.log_path.exists() else ""

    def lines(self):
        return [line for line in self.log().splitlines() if line.strip()]

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        if getattr(self, "handle", None):
            self.handle.close()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        return False


def pull(state_dir, model="orchard-3b-instruct", cwd=None):
    result = cli("pull", model, "--state-dir", str(state_dir), "--quiet", cwd=cwd)
    assert result.returncode == 0, result.stdout + result.stderr
    return result
