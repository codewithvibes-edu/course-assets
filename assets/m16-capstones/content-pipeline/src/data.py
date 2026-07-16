"""
Data layer for the content pipeline. Transcript + segmentation.
Sample data here is illustrative; real implementations would ingest
a Whisper transcript with word-level timestamps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Segment:
    """A speaker-bounded slice of a transcript."""

    id: str
    speaker: str
    text: str
    start_seconds: float
    end_seconds: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end_seconds - self.start_seconds)


# Sample transcript segments for the worked example. Replace with
# real Whisper output (with word-level timestamps) at production time.
SAMPLE_SEGMENTS: list[Segment] = [
    Segment(
        id="seg-001",
        speaker="host",
        text=(
            "Most AI courses spend their first three weeks on transformer math. "
            "You do not need transformer math to ship an LLM system."
        ),
        start_seconds=0.0,
        end_seconds=11.4,
    ),
    Segment(
        id="seg-002",
        speaker="host",
        text=(
            "The bottleneck on building useful LLM systems is not the model. "
            "It is the data layer. Pretty much every production LLM system that "
            "fails in 2026 fails at the data layer, not the model."
        ),
        start_seconds=11.4,
        end_seconds=28.7,
    ),
    Segment(
        id="seg-003",
        speaker="host",
        text=(
            "Here is the test. If your AI feature is failing, ask: where is the data "
            "coming from, when was it last refreshed, who signed off that it was "
            "the right shape. If you cannot answer those, you have a data problem, "
            "not a model problem."
        ),
        start_seconds=28.7,
        end_seconds=49.2,
    ),
    Segment(
        id="seg-004",
        speaker="host",
        text="Yeah uh, anyway, that is the whole module on data sources.",
        start_seconds=49.2,
        end_seconds=55.0,
    ),
]


def load_segments() -> list[Segment]:
    return list(SAMPLE_SEGMENTS)
