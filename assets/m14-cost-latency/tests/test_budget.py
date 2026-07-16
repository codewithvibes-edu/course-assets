"""Tests for tracking.budget."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tracking.budget import BudgetCap, BudgetError


def test_input_tokens_pre_check_passes():
    cap = BudgetCap(max_input_tokens=1000)
    cap.check_input_tokens(500)  # no raise


def test_input_tokens_pre_check_fails():
    cap = BudgetCap(max_input_tokens=1000)
    with pytest.raises(BudgetError):
        cap.check_input_tokens(1500)


def test_output_tokens_cumulative():
    cap = BudgetCap(max_output_tokens=1000)
    cap.add_output_tokens(400)
    cap.add_output_tokens(400)
    with pytest.raises(BudgetError):
        cap.add_output_tokens(400)


def test_turns():
    cap = BudgetCap(max_turns=3)
    cap.add_turn()
    cap.add_turn()
    cap.add_turn()
    with pytest.raises(BudgetError):
        cap.add_turn()


def test_cost():
    cap = BudgetCap(max_cost_cents=10.0)
    cap.add_cost(4.0)
    cap.add_cost(5.0)
    with pytest.raises(BudgetError):
        cap.add_cost(2.0)


def test_wall_seconds():
    cap = BudgetCap(max_wall_seconds=0.05)
    time.sleep(0.1)
    with pytest.raises(BudgetError):
        cap.check_wall()


def test_snapshot_shape():
    cap = BudgetCap(max_input_tokens=10_000)
    cap.add_input_tokens(100)
    cap.add_output_tokens(50)
    cap.add_turn()
    cap.add_cost(0.5)
    snap = cap.snapshot()
    assert snap["input_tokens"] == 100
    assert snap["output_tokens"] == 50
    assert snap["turns"] == 1
    assert snap["cost_cents"] == 0.5
    assert snap["elapsed_seconds"] >= 0


def test_no_caps_means_unlimited():
    cap = BudgetCap()
    cap.check_input_tokens(10**9)  # no raise
    cap.add_output_tokens(10**9)
    cap.add_turn()
    cap.add_cost(10**9)
    cap.check_wall()
