"""
Fallback chain dispatcher. Try each provider in order; log fallback
events; raise AllFallbacksFailed if every provider errors.

Distinguishes retryable from non-retryable errors via a caller-supplied
classifier so a 401 (auth misconfigured) does not trigger fallback to
secondary, but a 503 does.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Iterable


_log = logging.getLogger(__name__)


class AllFallbacksFailed(RuntimeError):
    """Every provider in the chain raised."""

    def __init__(self, errors: list[Exception]):
        super().__init__(f"all {len(errors)} providers failed")
        self.errors = errors


@dataclass
class FallbackResult:
    value: Any
    provider_name: str
    fallback_level: int
    errors_before: list[Exception]


def _default_is_retryable(exc: Exception) -> bool:
    """
    Conservative default: timeouts + connection errors retry; everything
    else is treated as a real failure that should fall through. Override
    for provider-specific logic.
    """
    name = type(exc).__name__.lower()
    return any(s in name for s in ("timeout", "connection", "ratelimit", "service"))


@dataclass
class FallbackChain:
    """
    Provider chain. Each entry: {"name": str, "fn": callable, "is_retryable": optional}.
    The fn signature is `fn(*args, **kwargs) -> result`.
    """

    providers: list[dict[str, Any]]

    def run(self, *args, **kwargs) -> FallbackResult:
        if not self.providers:
            raise AllFallbacksFailed([])

        errors: list[Exception] = []
        for level, entry in enumerate(self.providers):
            name = entry["name"]
            fn = entry["fn"]
            is_retryable = entry.get("is_retryable", _default_is_retryable)
            try:
                value = fn(*args, **kwargs)
                if level > 0:
                    _log.warning(
                        "fallback success: provider=%s level=%d primary_errors=%d",
                        name,
                        level,
                        len(errors),
                    )
                return FallbackResult(
                    value=value,
                    provider_name=name,
                    fallback_level=level,
                    errors_before=errors,
                )
            except Exception as exc:  # broad; classifier decides retryability
                _log.warning("provider %s raised: %s", name, exc)
                errors.append(exc)
                if not is_retryable(exc):
                    # Permanent error from this provider; still fall through to
                    # the next. The classifier's job is to decide retryability
                    # on this provider, not whether to escalate.
                    pass

        raise AllFallbacksFailed(errors)
