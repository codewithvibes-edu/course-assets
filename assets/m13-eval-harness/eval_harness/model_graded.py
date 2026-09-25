"""
Model-graded evaluation. A stronger model scores the output of a weaker
one against a rubric. Useful for subjective quality (writing tone, code
style, edge case coverage) where deterministic checks fall short.

Sycophancy bias: models are biased toward saying their own output is
good. Use a different model than the one being evaluated where practical,
and sample human review periodically to calibrate.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from .types import Score, ScoreSource


GRADER_PROMPT = """You are an evaluation grader. Read the OUTPUT against the RUBRIC and produce a single JSON object with two fields:

- "score": a float between 0.0 and 1.0 representing how well the output meets the rubric (0 = does not meet at all, 1 = fully meets)
- "reasoning": a one-sentence explanation of the score

Be strict. A passing output earns 0.8+; a borderline output earns 0.5-0.7; an output that misses the rubric earns < 0.5.

OUTPUT TO EVALUATE:
{output}

RUBRIC:
{rubric}

INPUT THAT PRODUCED THE OUTPUT (for context):
{input}

Respond with the JSON object only, no surrounding prose."""


@dataclass
class ModelGrader:
    """Grades outputs by calling a stronger model with a rubric prompt."""

    model: str = "claude-opus-5-5"
    api_key_env: str = "ANTHROPIC_API_KEY"
    timeout_seconds: int = 30

    def grade(self, output: str, rubric: str, input_text: str = "", passing_threshold: float = 0.8) -> Score:
        try:
            from anthropic import Anthropic
        except ImportError:
            return Score(
                source=ScoreSource.MODEL_GRADED,
                rule=f"rubric:{rubric[:40]}",
                passed=False,
                detail="anthropic SDK not installed",
            )

        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            return Score(
                source=ScoreSource.MODEL_GRADED,
                rule=f"rubric:{rubric[:40]}",
                passed=False,
                detail=f"missing {self.api_key_env}",
            )

        client = Anthropic(api_key=api_key, timeout=self.timeout_seconds)
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=4000,  # Opus 5.5 always thinks; thinking counts here
                # no temperature: Opus 5.5 rejects sampling params
                messages=[
                    {
                        "role": "user",
                        "content": GRADER_PROMPT.format(
                            output=output[:4000],
                            rubric=rubric,
                            input=input_text[:1000],
                        ),
                    }
                ],
            )
        except Exception as exc:
            return Score(
                source=ScoreSource.MODEL_GRADED,
                rule=f"rubric:{rubric[:40]}",
                passed=False,
                detail=f"grader call failed: {exc}",
            )

        text = "".join(b.text for b in response.content if hasattr(b, "text"))
        score, reasoning = _parse_grader_output(text)
        if score is None:
            return Score(
                source=ScoreSource.MODEL_GRADED,
                rule=f"rubric:{rubric[:40]}",
                passed=False,
                detail=f"could not parse grader response: {text[:120]}",
            )

        return Score(
            source=ScoreSource.MODEL_GRADED,
            rule=f"rubric:{rubric[:40]}",
            passed=score >= passing_threshold,
            value=score,
            detail=reasoning,
        )


def _parse_grader_output(text: str) -> tuple[float | None, str]:
    """Extract score + reasoning from the grader response."""
    # Try direct JSON parse first
    try:
        parsed = json.loads(text)
        return float(parsed.get("score", 0.0)), str(parsed.get("reasoning", ""))
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    # Fall back to extracting JSON from a fenced block
    match = re.search(r"\{[^{}]*\}", text, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            return float(parsed.get("score", 0.0)), str(parsed.get("reasoning", ""))
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    return None, ""
