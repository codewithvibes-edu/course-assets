"""
Per-task budget caps. Enforce limits explicitly so a buggy loop or a
malicious input cannot run away with cost or wall time.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


class BudgetError(RuntimeError):
    """Raised when a budget cap is exceeded."""


@dataclass
class BudgetCap:
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    max_turns: int | None = None
    max_cost_cents: float | None = None
    max_wall_seconds: float | None = None

    # Internal accumulators
    _started_at: float = field(default_factory=time.perf_counter, init=False)
    _input_tokens: int = field(default=0, init=False)
    _output_tokens: int = field(default=0, init=False)
    _turns: int = field(default=0, init=False)
    _cost_cents: float = field(default=0.0, init=False)

    def check_input_tokens(self, count: int) -> None:
        """Reject the call before it goes out the door if it would exceed the cap."""
        if self.max_input_tokens is not None and count > self.max_input_tokens:
            raise BudgetError(
                f"input tokens {count} > max {self.max_input_tokens}"
            )

    def add_input_tokens(self, count: int) -> None:
        self._input_tokens += count

    def add_output_tokens(self, count: int) -> None:
        self._output_tokens += count
        if (
            self.max_output_tokens is not None
            and self._output_tokens > self.max_output_tokens
        ):
            raise BudgetError(
                f"cumulative output tokens {self._output_tokens} > max "
                f"{self.max_output_tokens}"
            )

    def add_turn(self) -> None:
        self._turns += 1
        if self.max_turns is not None and self._turns > self.max_turns:
            raise BudgetError(f"turns {self._turns} > max {self.max_turns}")

    def add_cost(self, cents: float) -> None:
        self._cost_cents += cents
        if (
            self.max_cost_cents is not None
            and self._cost_cents > self.max_cost_cents
        ):
            raise BudgetError(
                f"cost {self._cost_cents:.2f}c > max {self.max_cost_cents:.2f}c"
            )

    def check_wall(self) -> None:
        elapsed = time.perf_counter() - self._started_at
        if (
            self.max_wall_seconds is not None
            and elapsed > self.max_wall_seconds
        ):
            raise BudgetError(
                f"wall time {elapsed:.1f}s > max {self.max_wall_seconds:.1f}s"
            )

    def snapshot(self) -> dict:
        return {
            "input_tokens": self._input_tokens,
            "output_tokens": self._output_tokens,
            "turns": self._turns,
            "cost_cents": round(self._cost_cents, 4),
            "elapsed_seconds": round(time.perf_counter() - self._started_at, 3),
        }
