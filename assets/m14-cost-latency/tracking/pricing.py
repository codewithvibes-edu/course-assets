"""
Token-cost reference table for common 2026 models.

Prices are in cents per million tokens. Verify against current provider
pricing before using these for billing-impacting math; pricing pages
move. The structure is what matters; the numbers are illustrative.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPrice:
    name: str
    provider: str
    input_cents_per_1m: float
    output_cents_per_1m: float


# Illustrative pricing snapshot. Treat numbers as defaults to override.
PRICING_TABLE: dict[str, ModelPrice] = {
    "claude-opus-4-7": ModelPrice("claude-opus-4-7", "anthropic", 1500.0, 7500.0),
    "claude-sonnet-4-6": ModelPrice("claude-sonnet-4-6", "anthropic", 300.0, 1500.0),
    "claude-haiku-4-5": ModelPrice("claude-haiku-4-5", "anthropic", 80.0, 400.0),
    "gpt-5": ModelPrice("gpt-5", "openai", 1000.0, 5000.0),
    "gpt-5-mini": ModelPrice("gpt-5-mini", "openai", 200.0, 1000.0),
    "gemini-1.5-pro": ModelPrice("gemini-1.5-pro", "google", 350.0, 1050.0),
    "llama-3.3-70b-hosted": ModelPrice("llama-3.3-70b-hosted", "together", 90.0, 90.0),
    "qwen-coder-32b-local": ModelPrice("qwen-coder-32b-local", "local", 0.0, 0.0),
}


def estimate_cost_cents(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Return the estimated cost in cents for a single call. Returns 0
    for unknown models so callers do not crash on a name miss; log the
    miss separately if you want to be loud.
    """
    price = PRICING_TABLE.get(model)
    if price is None:
        return 0.0
    return (
        (input_tokens / 1_000_000) * price.input_cents_per_1m
        + (output_tokens / 1_000_000) * price.output_cents_per_1m
    )
