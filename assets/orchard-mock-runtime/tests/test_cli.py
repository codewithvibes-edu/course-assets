"""CLI transcripts: the exact bytes the learner's terminal shows.

The 06c contract publishes exact output blocks for pull, serve startup,
ps, and stop. These tests hold the runtime to them byte for byte, because
a lesson that says "your terminal will show exactly this" is a promise.
Commands run with a RELATIVE --state-dir from a temporary directory, the
way the lessons run them, so path-bearing lines match the doc verbatim.

The serve/ps/stop flow needs the doc's literal port 8133 to reproduce the
doc bytes; it skips, loudly, if something else already owns that port.

    python3 -m unittest discover -s tests -v
"""

import json
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from support import READY_TIMEOUT_S, RUNTIME, clean_env, cli

MODEL = "orchard-3b-instruct"
DIGEST = "f5277bd414643c90b16022e3a388513bf54b6f7377c49461789f7be108c9cc45"

PULL_TRANSCRIPT = f"""\
MOCK NOTICE no model weights will be downloaded
MOCK pull model={MODEL} revision=fixture-v1
MOCK progress=0% declared=0.00/2.75 GiB
MOCK progress=25% declared=0.69/2.75 GiB
MOCK progress=50% declared=1.38/2.75 GiB
MOCK progress=75% declared=2.06/2.75 GiB
MOCK progress=100% declared=2.75/2.75 GiB
MOCK artifact=.orchard-runtime/artifacts/{MODEL}
MOCK actual_payload_bytes=4096 declared_mock_size_bytes=2952790016
MOCK sha256={DIGEST}
MOCK complete this artifact proves pull and verification mechanics only
"""

QUIET_PULL_TRANSCRIPT = f"""\
MOCK NOTICE no model weights will be downloaded
MOCK pull model={MODEL} revision=fixture-v1
MOCK artifact=.orchard-runtime/artifacts/{MODEL}
MOCK actual_payload_bytes=4096 declared_mock_size_bytes=2952790016
MOCK sha256={DIGEST}
MOCK complete this artifact proves pull and verification mechanics only
"""

CACHED_PULL_TRANSCRIPT = f"""\
MOCK NOTICE no model weights will be downloaded
MOCK pull model={MODEL} revision=fixture-v1
MOCK verify sha256={DIGEST} status=match
MOCK cached artifact=.orchard-runtime/artifacts/{MODEL} actual_payload_bytes=4096
MOCK complete no rewrite performed
"""

SERVE_TRANSCRIPT = f"""\
MOCK runtime=orchard-runtime fixture_version=1
MOCK run_id=local-001 model={MODEL}
MOCK bind=127.0.0.1:8133 scope=loopback
MOCK loading=0/1500 ms
MOCK loading=750/1500 ms
MOCK loading=1500/1500 ms
MOCK reported_memory_mib=3584 source=scenario-not-measurement
MOCK ttft_ms=250 tokens_per_second=20 source=scenario-not-benchmark
MOCK ready base_url=http://127.0.0.1:8133/v1
MOCK does not think; it proves the operations
MOCK stop with Ctrl+C or: python3 orchard_runtime.py stop --state-dir .orchard-runtime --run-id local-001
"""

PS_TRANSCRIPT = f"""\
RUN_ID     MODEL                  STATUS  BIND            REPORTED_MIB
local-001  {MODEL}    ready   127.0.0.1:8133  3584
MOCK rows=1 memory is scenario metadata, not measured process memory
"""

STOP_TRANSCRIPT = """\
MOCK stop requested run_id=local-001
MOCK stopped run_id=local-001 status=clean
"""


class CliCase(unittest.TestCase):
    """Every command in this file runs from a temp cwd with the relative
    state dir the lessons use."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def run_cli(self, *args):
        return cli(*args, "--state-dir", ".orchard-runtime", cwd=self.cwd)


class PullTranscripts(CliCase):
    def test_first_pull_matches_the_doc_byte_for_byte(self):
        result = self.run_cli("pull", MODEL)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, PULL_TRANSCRIPT)

    def test_second_pull_verifies_and_reports_cached(self):
        self.run_cli("pull", MODEL)
        payload = (self.cwd / ".orchard-runtime" / "artifacts" / MODEL
                   / "payload.bin")
        before = payload.stat().st_mtime_ns
        result = self.run_cli("pull", MODEL)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout, CACHED_PULL_TRANSCRIPT)
        self.assertEqual(payload.stat().st_mtime_ns, before,
                         "a cached pull must not rewrite the artifact")

    def test_quiet_pull_drops_only_the_progress_lines(self):
        result = self.run_cli("pull", MODEL, "--quiet")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout, QUIET_PULL_TRANSCRIPT)

    def test_unknown_model_exits_two_and_names_the_catalog(self):
        result = self.run_cli("pull", "orchard-9000-imaginary")
        self.assertEqual(result.returncode, 2)
        self.assertIn("MOCK ERROR mock_unknown_model", result.stdout)
        self.assertIn(MODEL, result.stdout,
                      "the error must list the names that DO exist")


class InvalidInvocation(CliCase):
    def test_unknown_command_exits_two(self):
        result = cli("shovel", cwd=self.cwd)
        self.assertEqual(result.returncode, 2)

    def test_serving_an_unpulled_model_exits_two_and_names_the_next_step(self):
        result = self.run_cli("serve", MODEL, "--run-id", "early-001")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("MOCK ERROR mock_model_not_pulled", result.stdout)
        self.assertIn(f"next: python3 orchard_runtime.py pull {MODEL}",
                      result.stdout)


class ExposureWarningOrder(CliCase):
    def test_exposure_warning_prints_before_anything_else(self):
        """Gate 1's second half: the exposure bind is explicit and warned.
        The port is pre-occupied on loopback so the wildcard bind fails
        right after the warning prints. That proves warning-first ordering
        without this suite ever holding an all-interfaces listener open;
        the full exposure drill is the learner's own m23-6 exercise."""
        self.run_cli("pull", MODEL, "--quiet")
        with socket.socket() as holder:
            holder.bind(("127.0.0.1", 0))
            holder.listen(1)
            port = holder.getsockname()[1]
            result = self.run_cli("serve", MODEL, "--run-id", "exposure-001",
                                  "--bind", "0.0.0.0", "--port", str(port))
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "MOCK WARNING exposure drill: bind=0.0.0.0 "
                                   "listens on every available interface")
        self.assertEqual(lines[1], "MOCK WARNING use fake fixture data only, "
                                   "inspect the bind, then stop this run")
        self.assertEqual(result.returncode, 2)
        self.assertIn("mock_port_in_use", result.stdout)


class DocExactServeFlow(CliCase):
    """The doc's serve, ps, and stop blocks on the doc's literal port."""

    def wait_for_ready(self, process):
        state_file = (self.cwd / ".orchard-runtime" / "runs"
                      / "local-001.json")
        deadline = time.monotonic() + READY_TIMEOUT_S
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise AssertionError(
                    f"serve exited early ({process.returncode})")
            try:
                if json.loads(state_file.read_text()).get("status") == "ready":
                    return
            except (OSError, json.JSONDecodeError):
                pass
            time.sleep(0.05)
        raise AssertionError("serve never reached ready")

    def test_serve_ps_stop_match_the_doc(self):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", 8133))
            except OSError:
                self.skipTest("port 8133 is busy; the doc-exact serve "
                              "transcript needs the doc's literal port")

        self.run_cli("pull", MODEL, "--quiet")
        log_path = self.cwd / "serve.log"
        with open(log_path, "w") as log:
            process = subprocess.Popen(
                [sys.executable, str(RUNTIME), "serve", MODEL,
                 "--state-dir", ".orchard-runtime", "--run-id", "local-001",
                 "--bind", "127.0.0.1", "--port", "8133",
                 "--load-delay-ms", "1500", "--reported-memory-mib", "3584",
                 "--ttft-ms", "250", "--tokens-per-second", "20"],
                stdout=log, stderr=subprocess.STDOUT,
                env=clean_env(), cwd=str(self.cwd))
        try:
            self.wait_for_ready(process)
            self.assertEqual(log_path.read_text(), SERVE_TRANSCRIPT)

            listing = self.run_cli("ps")
            self.assertEqual(listing.returncode, 0)
            self.assertEqual(listing.stdout, PS_TRANSCRIPT)

            stop = self.run_cli("stop", "--run-id", "local-001")
            self.assertEqual(stop.returncode, 0, stop.stdout)
            self.assertEqual(stop.stdout, STOP_TRANSCRIPT)

            self.assertEqual(process.wait(timeout=READY_TIMEOUT_S), 0)
            self.assertEqual(
                log_path.read_text(),
                SERVE_TRANSCRIPT
                + "MOCK shutdown reason=stop-command run_id=local-001\n")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
