"""
Agent layer for the content pipeline. Two agents:
  - clip_scorer: rates each segment 1-10 with a one-line reason
  - caption_writer: produces platform-specific copy from a chosen segment

Both bodies are heuristic for the demo so the example runs without
API keys. Replace with LLM calls (Claude Sonnet works well here at
temperature 0 for scoring, 0.3-0.5 for caption tone).
"""

from __future__ import annotations

from dataclasses import dataclass

from .data import Segment


@dataclass
class ClipScore:
    segment_id: str
    score: int  # 1-10
    reason: str


@dataclass
class Caption:
    platform: str  # 'x' | 'ig' | 'linkedin'
    text: str


_FILLER_PATTERNS = ("um", "uh", "anyway", "that is the whole")


def _filler_density(text: str) -> float:
    lower = text.lower()
    return sum(1 for f in _FILLER_PATTERNS if f in lower) / max(len(_FILLER_PATTERNS), 1)


def _conviction_density(text: str) -> float:
    """
    Tiny heuristic: short declarative sentences with concrete nouns score
    higher than meandering prose. Real implementation uses an LLM with
    a rubric.
    """
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    if not sentences:
        return 0.0
    short_strong = sum(1 for s in sentences if 4 <= len(s.split()) <= 14)
    return short_strong / len(sentences)


def clip_scorer(segment: Segment) -> ClipScore:
    """Score a segment for clip-worthiness. 1 = skip, 10 = ship."""
    duration_ok = 4.0 <= segment.duration_seconds <= 60.0
    filler = _filler_density(segment.text)
    conviction = _conviction_density(segment.text)

    score = 5
    if duration_ok:
        score += 1
    if filler == 0:
        score += 1
    if conviction >= 0.5:
        score += 2
    if filler > 0.2:
        score -= 3

    score = max(1, min(10, score))

    if score >= 8:
        reason = "tight, declarative, on-thesis"
    elif score >= 5:
        reason = "usable but not standout"
    else:
        reason = "too much filler or weak structure"

    return ClipScore(segment_id=segment.id, score=score, reason=reason)


def caption_writer(segment: Segment, platform: str) -> Caption:
    """Generate platform-specific copy from a segment."""
    if platform == "x":
        # Short, punchy, no hashtags. Trim to ~240 chars.
        text = segment.text.split(".")[0].strip() + "."
        return Caption(platform=platform, text=text[:240])

    if platform == "ig":
        # First line is the hook; hashtags live at the bottom.
        first_sentence = segment.text.split(".")[0].strip()
        hashtags = "#building #ai #thedataistheproduct"
        return Caption(platform=platform, text=f"{first_sentence}.\n\n{hashtags}")

    if platform == "linkedin":
        first_sentence = segment.text.split(".")[0].strip()
        return Caption(
            platform=platform,
            text=(
                f"{first_sentence}.\n\n"
                "I keep coming back to this when I see AI projects stall: it is "
                "almost never the model. Worth thinking about for anyone shipping "
                "LLM features."
            ),
        )

    return Caption(platform=platform, text=segment.text[:280])


def rank_segments(segments: list[Segment]) -> list[ClipScore]:
    """Score every segment and sort by descending score."""
    scores = [clip_scorer(s) for s in segments]
    scores.sort(key=lambda s: s.score, reverse=True)
    return scores
