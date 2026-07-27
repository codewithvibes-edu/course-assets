"""Gate 3: the Orchard adapter passes the Module 21 shared contract suite.

The suite is imported from the m21 kit, never copied. Its adapter
factories and its opener-seam helper are repointed at LocalProviderAdapter,
so every one of its thirteen tests exercises the Orchard adapter: the
happy paths against a live out-of-process serve run, the failure paths
through the same opener seam the lab adapter uses. If the shared suite
grows a test, this file inherits it for free; if this adapter forked the
canonical types, OneCanonicalBoundary would fail before anything else ran.

    python3 -m unittest discover -s tests -v
"""

import dataclasses
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support
from support import Serve, pull

sys.path.insert(0, str(support.ROOT / "integration"))

import adapter_local
from adapter_local import CAPABILITIES, LocalProviderAdapter

M21_TESTS = (support.ROOT.parent / "m21-adapter-kit" / "reference" / "tests"
             / "test_adapter_contract.py")

_spec = importlib.util.spec_from_file_location("m21_contract_suite",
                                               str(M21_TESTS))
m21 = importlib.util.module_from_spec(_spec)
sys.modules["m21_contract_suite"] = m21
_spec.loader.exec_module(m21)

MODEL = "orchard-3b-instruct"

_tmp = None
_serve = None


def _live_adapter():
    return LocalProviderAdapter(f"http://127.0.0.1:{_serve.port}", MODEL)


def _local_with(response_or_exc):
    """The suite's opener-seam helper, rebuilt around the local adapter.
    The local adapter holds no credential, so one is planted into its
    redaction list here; the secrecy test then proves the redaction
    machinery runs even on an adapter that normally has nothing to hide."""
    def opener(request_obj, timeout=None):
        if isinstance(response_or_exc, Exception):
            raise response_or_exc
        return response_or_exc
    adapter = LocalProviderAdapter("http://double.invalid", MODEL,
                                   opener=opener)
    adapter._secrets = [m21.SECRET]
    return adapter


def setUpModule():
    global _tmp, _serve
    _tmp = tempfile.TemporaryDirectory()
    state = Path(_tmp.name) / ".orchard-runtime"
    pull(state)
    _serve = Serve(state, "m21-contract", load_delay_ms=100).start()
    _serve.wait_for_status("ready")

    m21.adapters_for_generate = lambda: [("local", _live_adapter)]
    m21.adapters_for_stream = lambda: [("local", _live_adapter)]
    m21.lab_with = _local_with


def tearDownModule():
    if _serve:
        _serve.stop()
    if _tmp:
        _tmp.cleanup()


class CanonicalShape(m21.CanonicalShape):
    pass


class NormalizedFailures(m21.NormalizedFailures):
    pass


class SecretsAndCapabilities(m21.SecretsAndCapabilities):
    pass


class OneCanonicalBoundary(unittest.TestCase):
    def test_adapter_and_suite_share_one_canonical_module(self):
        """Identity, not equality: a faithful copy would still be a fork."""
        self.assertIs(adapter_local.AdapterError, m21.AdapterError)
        self.assertIs(adapter_local.CanonicalResponse, m21.CanonicalResponse)
        self.assertIs(adapter_local.StreamEvent, m21.StreamEvent)
        self.assertIs(adapter_local.Usage,
                      sys.modules["canonical"].Usage)


class CapabilitiesMatchCatalog(unittest.TestCase):
    def test_declaration_matches_catalog_field_for_field(self):
        catalog = json.loads((support.ROOT / "catalog.json").read_text())
        declared = catalog["capabilities"]
        for name, value in declared.items():
            self.assertEqual(getattr(CAPABILITIES, name), value, name)
        self.assertEqual(
            set(declared),
            {field.name for field in dataclasses.fields(CAPABILITIES)},
            "capabilities fields differ between catalog.json and the adapter")


if __name__ == "__main__":
    unittest.main()
