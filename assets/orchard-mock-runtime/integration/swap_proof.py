"""The m24-3 swap proof, reproducible end to end.

    python3 integration/swap_proof.py

The 06c doc's literal command is:

    CWV_CONNECTION=local_mock python3 app_swap_demo.py

That command presumes your own Module 21 project, where you have already
merged profile.local-mock.json into your profiles.json and registered the
local adapter in your registry. This script performs exactly that merge
in-process against the SHIPPED m21 kit, then runs the kit's UNCHANGED
app_swap_demo.main(). Nothing in the m21 kit is edited; the application
file's checksum is printed before and after so the evidence can say,
with bytes, that the application-code diff is empty.

Evidence lands in evidence/ (gitignored learner output, never published
fixture data).
"""

import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(HERE))

from support import Serve, pull                        # noqa: E402
from adapter_local import LocalProviderAdapter         # noqa: E402

M21 = ROOT.parent / "m21-adapter-kit" / "reference"
sys.path.insert(0, str(M21))

import registry                                        # noqa: E402

PROFILE_PATH = HERE / "profile.local-mock.json"
LOGICAL_ID = "local_mock"


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def register_local(base_url):
    """The learner's m24-2 registry edit, performed in-process. The
    original connect() still handles every other logical id, so the merge
    adds a route without forking the registry."""
    profile = dict(json.loads(PROFILE_PATH.read_text())[LOGICAL_ID],
                   base_url=base_url)
    original_connect = registry.connect

    def connect(logical_id, profiles=None, opener=None):
        if logical_id == LOGICAL_ID:
            return (LocalProviderAdapter(profile["base_url"],
                                         profile["model"]),
                    profile)
        return original_connect(logical_id, profiles=profiles, opener=opener)

    registry.connect = connect
    return profile


def main():
    app_path = M21 / "app_swap_demo.py"
    suite_path = M21 / "tests" / "test_adapter_contract.py"
    checksum_before = sha256_file(app_path)

    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / ".orchard-runtime"
        pull(state)
        with Serve(state, "swap-proof-001", load_delay_ms=0, ttft_ms=0,
                   tokens_per_second=0) as run:
            run.wait_for_status("ready")
            profile = register_local(f"http://127.0.0.1:{run.port}")
            os.environ["CWV_CONNECTION"] = LOGICAL_ID

            import app_swap_demo    # after the merge, so it binds it
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = app_swap_demo.main()
            app_output = captured.getvalue()

    checksum_after = sha256_file(app_path)
    diff_empty = checksum_before == checksum_after

    lines = [
        "--- app_swap_demo.py output " + "-" * 32,
        app_output.rstrip("\n"),
        "-" * 60,
        f"logical_connection={LOGICAL_ID}",
        f"adapter={profile['adapter']} "
        f"privacy_class={profile['privacy_class']} "
        f"secret_env={profile['secret_env']}",
        f"contract_suite=test_adapter_contract.py "
        f"sha256={sha256_file(suite_path)}",
        f"app_file=app_swap_demo.py sha256={checksum_before}",
        "application_code_diff=" + ("empty" if diff_empty else "NOT EMPTY"),
        "route_class=exercise-only mock route",
        "note=this proof demonstrates swap mechanics; it says nothing "
        "about any model",
    ]
    report = "\n".join(lines) + "\n"
    print(report, end="")

    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    evidence_path = evidence_dir / "swap-local-mock.txt"
    evidence_path.write_text(report)
    print(f"saved {evidence_path.relative_to(ROOT)}")

    return exit_code if diff_empty else 1


if __name__ == "__main__":
    sys.exit(main())
