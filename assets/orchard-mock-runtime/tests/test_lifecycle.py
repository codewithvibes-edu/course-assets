"""Lifecycle: the transitions that decide whether an operator trusts a
service. Load, ready, stop during load, Ctrl+C, stale state, port conflict,
planted memory refusal, and stale artifact lock recovery.

Every test here runs a REAL out-of-process server on loopback with a
temporary state directory. Nothing is faked at this layer, because the
whole point of an operational fixture is that the operations really happen.

    python3 -m unittest discover -s tests -v
"""

import json
import signal
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from support import Serve, cli, plant, pull


class LifecycleCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / ".orchard-runtime"
        pull(self.state)
        self.addCleanup(self.tmp.cleanup)

    def serve(self, run_id, **flags):
        run = Serve(self.state, run_id, **flags)
        self.addCleanup(run.stop)
        return run.start()


class ReadyAndStop(LifecycleCase):
    def test_run_reaches_ready_then_stops_clean(self):
        run = self.serve("local-001", load_delay_ms=100)
        run.wait_for_status("ready")

        result = cli("stop", "--state-dir", str(self.state), "--run-id", "local-001")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("MOCK stop requested run_id=local-001", result.stdout)
        self.assertIn("MOCK stopped run_id=local-001 status=clean", result.stdout)

        self.assertEqual(run.wait_for_exit(), 0)
        self.assertIn("MOCK shutdown reason=stop-command run_id=local-001", run.log())
        self.assertEqual(run.state()["status"], "stopped")

    def test_state_is_written_before_each_transition(self):
        run = self.serve("local-002", load_delay_ms=3000)
        deadline = time.monotonic() + 10
        seen = None
        while time.monotonic() < deadline and seen is None:
            current = run.state()
            if current and current.get("status") == "loading":
                seen = current
            time.sleep(0.02)
        self.assertIsNotNone(seen, "loading state was never observable on disk")
        self.assertEqual(run.wait_for_status("ready")["status"], "ready")


class StopDuringLoad(LifecycleCase):
    def test_stop_request_during_load_is_honored(self):
        run = self.serve("load-001", load_delay_ms=8000)
        run.wait_for_status("loading")

        result = cli("stop", "--state-dir", str(self.state), "--run-id", "load-001")
        self.assertEqual(result.returncode, 0, result.stdout)

        self.assertEqual(run.wait_for_exit(), 0)
        self.assertIn("reason=stop-command-during-load", run.log())
        self.assertEqual(run.state()["status"], "stopped")
        self.assertNotIn("MOCK ready", run.log(),
                         "a stopped load must never announce ready")


class KeyboardInterruptPath(LifecycleCase):
    def test_ctrl_c_after_ready_transitions_like_stop(self):
        run = self.serve("sig-001", load_delay_ms=100)
        run.wait_for_status("ready")

        run.process.send_signal(signal.SIGINT)
        self.assertEqual(run.wait_for_exit(), 0)
        self.assertIn("reason=keyboard-interrupt", run.log())
        self.assertEqual(run.state()["status"], "stopped")

    def test_ctrl_c_during_load_transitions_cleanly(self):
        run = self.serve("sig-002", load_delay_ms=8000)
        run.wait_for_status("loading")

        run.process.send_signal(signal.SIGINT)
        self.assertEqual(run.wait_for_exit(), 0)
        self.assertIn("reason=keyboard-interrupt", run.log())
        self.assertEqual(run.state()["status"], "stopped")


class StaleState(LifecycleCase):
    def test_ps_reports_stale_for_a_dead_pid(self):
        run = self.serve("stale-001", load_delay_ms=100)
        run.wait_for_status("ready")
        run.process.kill()
        run.process.wait(timeout=10)

        listing = cli("ps", "--state-dir", str(self.state))
        self.assertEqual(listing.returncode, 0)
        row = [line for line in listing.stdout.splitlines()
               if line.startswith("stale-001")]
        self.assertTrue(row, listing.stdout)
        self.assertIn("stale", row[0])
        self.assertNotIn("ready", row[0],
                         "a dead pid must never be reported as healthy")

    def test_stop_recovers_stale_state_without_killing_anything(self):
        run = self.serve("stale-002", load_delay_ms=100)
        run.wait_for_status("ready")
        run.process.kill()
        run.process.wait(timeout=10)

        result = cli("stop", "--state-dir", str(self.state), "--run-id", "stale-002")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("status=stale-state-recovered", result.stdout)

    def test_stop_on_unknown_run_exits_three(self):
        result = cli("stop", "--state-dir", str(self.state), "--run-id", "ghost")
        self.assertEqual(result.returncode, 3)
        self.assertIn("mock_run_not_found", result.stdout)


class PortConflict(LifecycleCase):
    def test_second_bind_on_the_same_address_exits_two(self):
        run = self.serve("port-001", load_delay_ms=100)
        run.wait_for_status("ready")

        result = cli("serve", "orchard-3b-instruct",
                     "--state-dir", str(self.state), "--run-id", "port-002",
                     "--port", str(run.port), "--load-delay-ms", "0")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn(f"MOCK ERROR mock_port_in_use bind=127.0.0.1:{run.port}",
                      result.stdout)

    def test_run_id_already_in_use_is_refused(self):
        run = self.serve("dup-001", load_delay_ms=100)
        run.wait_for_status("ready")

        result = cli("serve", "orchard-3b-instruct",
                     "--state-dir", str(self.state), "--run-id", "dup-001",
                     "--port", "0", "--load-delay-ms", "0")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("mock_run_id_in_use", result.stdout)


class PlantedMemoryRefusal(LifecycleCase):
    def test_scenario_over_limit_exits_four_without_allocating(self):
        result = cli("serve", "orchard-3b-instruct",
                     "--state-dir", str(self.state), "--run-id", "oom-001",
                     "--reported-memory-mib", "3584", "--memory-limit-mib", "2048")
        self.assertEqual(result.returncode, 4, result.stdout)
        self.assertIn("MOCK ERROR mock_oom required_scenario_mib=3584 "
                      "limit_mib=2048 no large allocation attempted",
                      result.stdout)
        self.assertFalse((self.state / "runs" / "oom-001.json").exists(),
                         "a refused start must not leave run state behind")

    def test_refusal_names_no_real_allocation(self):
        result = cli("serve", "orchard-3b-instruct",
                     "--state-dir", str(self.state), "--run-id", "oom-002",
                     "--reported-memory-mib", "9000", "--memory-limit-mib", "512")
        self.assertIn("no large allocation attempted", result.stdout)


class StaleArtifactLock(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / ".orchard-runtime"
        self.addCleanup(self.tmp.cleanup)

    def test_planted_lock_refuses_then_recovers(self):
        pull(self.state)
        planted = plant("stale-artifact-lock", "--state-dir", str(self.state),
                        "--model", "orchard-3b-instruct")
        self.assertEqual(planted.returncode, 0, planted.stdout + planted.stderr)
        self.assertIn("pid_alive=false", planted.stdout)

        refused = cli("pull", "orchard-3b-instruct", "--state-dir", str(self.state))
        self.assertEqual(refused.returncode, 5, refused.stdout)
        self.assertIn("mock_stale_artifact_lock", refused.stdout)
        self.assertIn("--recover-stale-lock", refused.stdout)

        recovered = cli("pull", "orchard-3b-instruct",
                        "--state-dir", str(self.state), "--recover-stale-lock")
        self.assertEqual(recovered.returncode, 0, recovered.stdout)
        self.assertIn("status=match", recovered.stdout)
        self.assertFalse(
            (self.state / "artifacts" / "orchard-3b-instruct" / ".lock").exists())

    def test_recovery_touches_only_the_named_model(self):
        pull(self.state)
        pull(self.state, "orchard-3b-instruct-canary")
        plant("stale-artifact-lock", "--state-dir", str(self.state),
              "--model", "orchard-3b-instruct")
        plant("stale-artifact-lock", "--state-dir", str(self.state),
              "--model", "orchard-3b-instruct-canary")

        cli("pull", "orchard-3b-instruct", "--state-dir", str(self.state),
            "--recover-stale-lock")

        canary_lock = (self.state / "artifacts" / "orchard-3b-instruct-canary"
                       / ".lock")
        self.assertTrue(canary_lock.exists(),
                        "recovery removed a lock it was not asked to touch")

    def test_a_live_lock_is_not_treated_as_stale(self):
        pull(self.state)
        lock = self.state / "artifacts" / "orchard-3b-instruct" / ".lock"
        lock.write_text(json.dumps({"mock": True, "pid": __import__("os").getpid()}))

        held = cli("pull", "orchard-3b-instruct", "--state-dir", str(self.state))
        self.assertEqual(held.returncode, 5, held.stdout)
        self.assertIn("mock_artifact_lock_held", held.stdout)
        self.assertIn("pid_alive=true", held.stdout)


if __name__ == "__main__":
    unittest.main()
