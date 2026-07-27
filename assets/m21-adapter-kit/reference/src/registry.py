"""Connection profiles and the logical-ID registry.

Two rules do all the work here:

1. The application selects a LOGICAL connection ("primary", "fallback"),
   never a provider name. Providers change; the words in your code should
   not have to.
2. Profiles store metadata and a POINTER to a secret (the name of an
   environment variable), never the secret itself. profiles.json is
   committable; the values it points to are not.
"""

import json
import os
from pathlib import Path

from adapter_lab import LabAdapter
from adapter_mock import MockAdapter
from canonical import AdapterError

PROFILES_PATH = Path(__file__).parent / "profiles.json"

ADAPTERS = {
    "lab": LabAdapter,
    "mock": MockAdapter,
}


def load_profiles(path=None):
    return json.loads(Path(path or PROFILES_PATH).read_text())


def connect(logical_id, profiles=None, opener=None):
    """Build the adapter behind a logical ID. Fails closed and loudly."""
    profiles = profiles or load_profiles()
    if logical_id not in profiles:
        raise AdapterError("not_found",
                           f"No connection profile named '{logical_id}'. "
                           f"Profiles: {', '.join(sorted(profiles))}.")
    profile = profiles[logical_id]
    adapter_id = profile["adapter"]
    if adapter_id not in ADAPTERS:
        raise AdapterError("not_found", f"No adapter '{adapter_id}' registered.")

    if adapter_id == "mock":
        return MockAdapter(model=profile.get("model", "mock-deterministic-1")), profile

    secret_env = profile["secret_env"]          # the NAME, never the value
    api_key = os.environ.get(secret_env)
    if not api_key:
        raise AdapterError(
            "auth",
            f"Profile '{logical_id}' expects the secret in ${secret_env}, "
            "which is not set. The profile stores the pointer; you hold "
            "the value.")
    return LabAdapter(
        base_url=profile["base_url"], api_key=api_key,
        model=profile["model"], opener=opener,
    ), profile


def require_capability(adapter, name):
    """Capability gate: check before enabling a feature; fail closed with
    a sentence a human can act on, not a KeyError three layers deep."""
    caps = adapter.capabilities()
    if not getattr(caps, name, False):
        raise AdapterError(
            "unsupported",
            f"This connection does not declare '{name}' "
            f"(capabilities last tested {caps.last_tested}). "
            "Choose a connection that declares it, or degrade visibly.")
