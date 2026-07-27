"""Canonical types: the ONLY shapes the application is allowed to see.

Every field exists because the application uses it, not because some
provider offers it. That restraint is the design: a canonical type that
mirrors one provider's API is that provider's API wearing a fake mustache.

Provider request/response types must never cross the adapter boundary.
The contract suite checks the visible surface of that rule; the rest is
discipline.
"""

from dataclasses import dataclass, field


# ---- requests -------------------------------------------------------------

@dataclass
class Message:
    role: str          # "user" | "assistant" | "system"
    content: str


@dataclass
class MediaRef:
    """A reference to learner-owned media for input understanding.
    Adapters that declare image_input=False must refuse this explicitly."""
    media_type: str    # e.g. "image/png"
    data_b64: str


@dataclass
class CanonicalRequest:
    messages: list                      # list[Message]
    media: list = field(default_factory=list)   # list[MediaRef]
    max_output_tokens: int = 512
    timeout_s: float = 15.0


# ---- responses ------------------------------------------------------------

@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class CanonicalResponse:
    content: str
    finish_reason: str                  # "complete" | "length" | "canceled"
    usage: Usage
    latency_s: float
    request_id: str                     # provider's ID, or "local-<n>" for offline adapters
    raw_debug: str = ""                 # REDACTED diagnostic context; never secrets


@dataclass
class StreamEvent:
    kind: str                           # "delta" | "usage" | "done" | "canceled" | "error"
    text: str = ""                      # for delta
    usage: Usage = None                 # for usage/done
    request_id: str = ""                # populated on done/error


# ---- capabilities ----------------------------------------------------------

@dataclass
class Capabilities:
    """Declared, dated, and truthful. An absent feature is a stated fact
    here, never a nullable surprise at call time."""
    text: bool
    streaming: bool
    structured_output: bool
    tools: bool
    image_input: bool
    last_tested: str                    # ISO date the declaration was verified


# ---- errors -----------------------------------------------------------------

ERROR_CATEGORIES = (
    "auth", "rate_limit", "bad_input", "not_found", "server",
    "timeout", "network", "malformed", "unsupported",
)


class AdapterError(Exception):
    """One error type for the whole application. The category carries the
    decision; raw_debug carries redacted evidence for a human."""

    def __init__(self, category, message, retry_after=None,
                 request_id=None, raw_debug=""):
        assert category in ERROR_CATEGORIES, category
        super().__init__(message)
        self.category = category
        self.retry_after = retry_after
        self.request_id = request_id
        self.raw_debug = raw_debug


def redact(text, secrets):
    """Strip every known secret value out of diagnostic text before it is
    stored anywhere. Evidence survives; credentials do not."""
    out = text or ""
    for secret in secrets:
        if secret:
            out = out.replace(secret, "[REDACTED]")
    return out
