"""Failures on purpose: planted eval cases and live error normalization.

Three layers. The eval fixture's planted failures must be exactly what
the fixture declares, byte for byte, or the m24-5 comparison drill counts
the wrong things. The adapter must normalize LIVE runtime errors into
canonical categories, not just the doubles the m21 suite feeds it. And
stopping the service mid-conversation must surface as a canonical
network failure, because that is the m24-4 fallback drill.

    python3 -m unittest discover -s tests -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support
from support import Serve, cli, pull

sys.path.insert(0, str(support.ROOT / "integration"))

from adapter_local import LocalProviderAdapter
from canonical import AdapterError, CanonicalRequest, Message

MODEL = "orchard-3b-instruct"
CANARY = "orchard-3b-instruct-canary"
PREFIX = "[COURSE MOCK, NOT MODEL OUTPUT]"

EVAL = json.loads((support.ROOT / "fixtures" / "eval-cases.json").read_text())
CASES = {case["case_id"]: case for case in EVAL["cases"]}

_tmp = None
_serve = None


def setUpModule():
    global _tmp, _serve
    _tmp = tempfile.TemporaryDirectory()
    state = Path(_tmp.name) / ".orchard-runtime"
    pull(state)
    _serve = Serve(state, "failures-001", load_delay_ms=0, ttft_ms=0,
                   tokens_per_second=0).start()
    _serve.wait_for_status("ready")


def tearDownModule():
    if _serve:
        _serve.stop()
    if _tmp:
        _tmp.cleanup()


def adapter(model=MODEL):
    return LocalProviderAdapter(f"http://127.0.0.1:{_serve.port}", model)


def request(content):
    return CanonicalRequest(messages=[Message("user", content)])


class PlantedFixtureData(unittest.TestCase):
    """The fixture file's claims about itself, verified. These tests carry
    the honesty block: a declared subset that quietly drifts from the
    actual data would poison every comparison built on it."""

    def test_ten_cases_with_unique_ids(self):
        self.assertEqual(len(EVAL["cases"]), 10)
        self.assertEqual(len(CASES), 10)

    def test_differing_cases_declaration_is_exactly_true(self):
        actual = {case_id for case_id, case in CASES.items()
                  if case["outputs"][MODEL]["fixture_result"]
                  != case["outputs"][CANARY]["fixture_result"]}
        self.assertEqual(actual, set(EVAL["differing_cases"]))

    def test_non_differing_cases_are_byte_identical(self):
        for case_id, case in CASES.items():
            if case_id in EVAL["differing_cases"]:
                continue
            self.assertEqual(case["outputs"][MODEL],
                             case["outputs"][CANARY], case_id)

    def test_planted_failure_counts_drive_the_promotion_drill(self):
        """Baseline plants 2, canary plants 3: the arithmetic behind the
        m24-6 promote-or-reject decision."""
        planted = {model: [case_id for case_id, case in sorted(CASES.items())
                           if case["outputs"][model]["planted_failure"]]
                   for model in (MODEL, CANARY)}
        self.assertEqual(planted[MODEL], ["oc-05", "oc-08"])
        self.assertEqual(planted[CANARY], ["oc-03", "oc-07", "oc-10"])

    def test_every_planted_category_is_declared(self):
        declared = set(EVAL["planted_failure_categories"])
        for case_id, case in CASES.items():
            for model in (MODEL, CANARY):
                category = case["outputs"][model]["planted_failure"]
                if category is not None:
                    self.assertIn(category, declared, case_id)

    def test_format_break_and_refusal_really_fail_to_parse(self):
        with self.assertRaises(json.JSONDecodeError):
            json.loads(CASES["oc-08"]["outputs"][MODEL]["fixture_result"])
        with self.assertRaises(json.JSONDecodeError):
            json.loads(CASES["oc-07"]["outputs"][CANARY]["fixture_result"])

    def test_every_other_result_parses_against_the_schema(self):
        fields = EVAL["response_schema"]["fields"]
        enums = {name: set(values) for name, values in fields.items()
                 if isinstance(values, list)}
        for case_id, case in CASES.items():
            for model in (MODEL, CANARY):
                output = case["outputs"][model]
                if output["planted_failure"] in ("format-break", "refusal"):
                    continue
                parsed = json.loads(output["fixture_result"])
                self.assertEqual(set(parsed), set(fields),
                                 f"{case_id}/{model}")
                for name, allowed in enums.items():
                    self.assertIn(parsed[name], allowed, f"{case_id}/{model}")
                self.assertTrue(0.0 <= parsed["confidence"] <= 1.0,
                                f"{case_id}/{model}")


class LiveNormalization(unittest.TestCase):
    """The m21 suite proves normalization against doubles. These prove it
    against the real server's real error bodies."""

    def test_model_this_run_does_not_serve_is_not_found(self):
        with self.assertRaises(AdapterError) as ctx:
            adapter(CANARY).generate(request("hello"))
        self.assertEqual(ctx.exception.category, "not_found")

    def test_unsupported_feature_wins_over_the_generic_400_mapping(self):
        broken = CanonicalRequest(
            messages=[Message("user", [{"type": "image_url"}])])
        with self.assertRaises(AdapterError) as ctx:
            adapter().generate(broken)
        self.assertEqual(ctx.exception.category, "unsupported")

    def test_other_400s_normalize_to_bad_input(self):
        with self.assertRaises(AdapterError) as ctx:
            adapter().generate(request("word " * 513))
        self.assertEqual(ctx.exception.category, "bad_input")
        self.assertIn("fixture word limit", str(ctx.exception))

    def test_planted_wrong_answer_is_served_verbatim(self):
        case = CASES["oc-05"]
        response = adapter().generate(request(case["input"]))
        expected = (PREFIX + "\nfixture="
                    + case["outputs"][MODEL]["fixture_result"])
        self.assertEqual(response.content, expected)

    def test_planted_format_break_survives_transport_intact(self):
        case = CASES["oc-08"]
        response = adapter().generate(request(case["input"]))
        fixture = response.content.split("fixture=", 1)[1]
        self.assertEqual(fixture, case["outputs"][MODEL]["fixture_result"])
        with self.assertRaises(json.JSONDecodeError):
            json.loads(fixture)


class StoppedServiceDrill(unittest.TestCase):
    """m24-4: the service stops, the adapter says 'network', the
    application decides. Nothing here inspects Orchard internals; the
    adapter sees exactly what it would see with a real dead runtime."""

    def test_stop_produces_a_canonical_network_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / ".orchard-runtime"
            pull(state)
            run = Serve(state, "drill-001", load_delay_ms=0, ttft_ms=0,
                        tokens_per_second=0)
            with run:
                run.wait_for_status("ready")
                live = LocalProviderAdapter(
                    f"http://127.0.0.1:{run.port}", MODEL)
                self.assertTrue(live.test())

                result = cli("stop", "--state-dir", str(state),
                             "--run-id", "drill-001")
                self.assertEqual(result.returncode, 0, result.stdout)
                run.wait_for_exit()

                with self.assertRaises(AdapterError) as ctx:
                    live.generate(request("Summarize the weekly status."))
                self.assertEqual(ctx.exception.category, "network")
                with self.assertRaises(AdapterError) as test_ctx:
                    live.test()
                self.assertEqual(test_ctx.exception.category, "network")


if __name__ == "__main__":
    unittest.main()
