"""
Token-cost reference table for current models (list prices read 2026-09-25).

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


# List prices read 2026-09-25 from each provider's pricing page. Keys are the
# names you log; match them to your provider's exact model IDs, and treat the
# numbers as defaults to override.
PRICING_TABLE: dict[str, ModelPrice] = {
    "claude-opus-5-5": ModelPrice("claude-opus-5-5", "anthropic", 400.0, 2000.0),
    "claude-fable-5-1": ModelPrice("claude-fable-5-1", "anthropic", 1000.0, 5000.0),
    "claude-sonnet-5": ModelPrice("claude-sonnet-5", "anthropic", 200.0, 1000.0),
    "claude-haiku-4-5": ModelPrice("claude-haiku-4-5", "anthropic", 100.0, 500.0),
    "gpt-6-astra": ModelPrice("gpt-6-astra", "openai", 1000.0, 5000.0),
    "gpt-6-sol": ModelPrice("gpt-6-sol", "openai", 200.0, 1000.0),
    "gpt-6-luna": ModelPrice("gpt-6-luna", "openai", 10.0, 50.0),
    # Introductory price through 2026-12-31; 150 / 750 from 2027-01-01.
    "gemini-3.8-flash": ModelPrice("gemini-3.8-flash", "google", 75.0, 375.0),
    "gemini-3.1-pro": ModelPrice("gemini-3.1-pro", "google", 200.0, 1200.0),
    "grok-4.7": ModelPrice("grok-4.7", "spacexai", 200.0, 600.0),
    # Off-peak prices; both double 01:00-04:00 and 06:00-10:00 UTC on weekdays.
    "deepseek-flash": ModelPrice("deepseek-flash", "deepseek", 15.0, 60.0),
    "deepseek-v4-pro": ModelPrice("deepseek-v4-pro", "deepseek", 66.0, 198.0),
    "qwen3.8-27b-local": ModelPrice("qwen3.8-27b-local", "local", 0.0, 0.0),
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
