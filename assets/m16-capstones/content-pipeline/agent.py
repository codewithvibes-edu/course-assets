"""
Agent layer for the multi-platform content pipeline.

Sequential pipeline pattern (module 10, Pattern 2):
    clip_scorer  ->  caption_writer  ->  human_review_queue

Each stage uses the Anthropic Messages API with a tight system prompt
and few-shot examples drawn from the voice_history corpus (module 7
RAG pattern). All bodies fall back to deterministic logic if
ANTHROPIC_API_KEY is unset, so `python example.py` runs end-to-end.

Nothing publishes automatically. The final stage emits a review_queue
entry; a human approves before posting (module 14 pattern).
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_layer import Segment, get_segment, voice_examples


MODEL = os.environ.get("CONTENT_AGENT_MODEL", "claude-sonnet-4-7")


# ---------- Schema ----------


@dataclass
class ClipScore:
    segment_id: str
    score: int  # 1-10
    reason: str


@dataclass
class Caption:
    platform: str  # 'x' | 'ig' | 'linkedin'
    text: str
    source_segment_id: str = ""


@dataclass
class ReviewItem:
    """A scheduled-but-not-published post. Human approves before send."""

    segment_id: str
    platform: str
    caption_text: str
    score: int
    status: str = "pending_human_review"


# ---------- Stage 1: clip_scorer ----------


SCORER_SYSTEM = """You are a clip identifier for a content pipeline.

Given a transcript SEGMENT, rate it 1-10 for clip-worthiness on social media. Criteria:
- Tight delivery (no rambling)
- One concrete claim or insight (not a hedge or a transition)
- Stands alone (a reader who never saw the source can follow it)
- Conviction (declarative, specific)

Filler-heavy ("um", "uh", "anyway") or transition-only segments score 1-3.
Solid but-not-standout segments score 5-6.
Strong, standalone, on-thesis segments score 8-10.

Respond with a JSON object only: {"score": <int>, "reason": "<one sentence>"}"""


_FILLER_TOKENS = ("um", "uh", "anyway", "you know", "i mean", "sort of", "kind of", "like,")


def _filler_count(text: str) -> int:
    lower = text.lower()
    return sum(lower.count(t) for t in _FILLER_TOKENS)


def _conviction_score(text: str) -> float:
    """Short declarative sentences with concrete nouns score higher."""
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if not sentences:
        return 0.0
    strong = sum(1 for s in sentences if 4 <= len(s.split()) <= 18)
    return strong / len(sentences)


def _fallback_score(segment: Segment) -> ClipScore:
    duration_ok = 4.0 <= segment.duration_seconds <= 90.0
    fillers = _filler_count(segment.text)
    conviction = _conviction_score(segment.text)
    score = 5
    if duration_ok:
        score += 1
    if fillers == 0:
        score += 1
    if conviction >= 0.6 and fillers == 0:
        score += 2
    if fillers >= 2:
        score -= 5
    if fillers >= 1 and len(segment.text.split()) < 18:
        # short + any filler = transition / throwaway
        score -= 2
    score = max(1, min(10, score))
    if score >= 8:
        reason = "tight, declarative, on-thesis"
    elif score >= 5:
        reason = "usable but not standout"
    else:
        reason = "filler-heavy or weak structure"
    return ClipScore(segment_id=segment.id, score=score, reason=reason)


def clip_scorer(segment: Segment) -> ClipScore:
    """Score a single segment. Uses Anthropic Messages API if key available."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_score(segment)
    try:
        from anthropic import Anthropic
    except ImportError:
        return _fallback_score(segment)

    client = Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=200,
            temperature=0,
            system=SCORER_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": f"SEGMENT (duration {segment.duration_seconds:.1f}s):\n{segment.text}",
                }
            ],
        )
    except Exception:
        return _fallback_score(segment)

    text = "".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text")
    try:
        # Permissive JSON extraction
        match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
        if match:
            obj = json.loads(match.group())
            return ClipScore(
                segment_id=segment.id,
                score=max(1, min(10, int(obj.get("score", 5)))),
                reason=str(obj.get("reason", "")).strip()[:200],
            )
    except (ValueError, json.JSONDecodeError):
        pass
    return _fallback_score(segment)


# ---------- Stage 2: caption_writer ----------


CAPTION_SYSTEM = """You write platform-specific captions from a transcript SEGMENT, matching the creator's voice using EXAMPLES.

Platform rules:
- x: <=240 chars. Punchy. No hashtags. No links. One strong sentence, occasionally two.
- ig: 1-3 sentences. Hook first line. Hashtags only at the very bottom (3-5).
- linkedin: 2-4 short paragraphs. Concrete claim, then context. No hashtags.

Voice rules from EXAMPLES:
- Declarative. No watery qualifiers ("perhaps", "it seems").
- No em dashes. No "it's not about X, it's about Y."
- Tight. Direct. Treat the reader as a peer.

Respond with the caption text only. No preamble, no commentary."""


def _fallback_caption(segment: Segment, platform: str, examples: list) -> Caption:
    """Heuristic caption that mimics the platform shape without an LLM."""
    sentences = [s.strip() for s in re.split(r"[.!?]+", segment.text) if s.strip()]
    first_sentence = sentences[0] if sentences else segment.text[:120]
    long_body = (
        ". ".join(sentences[:3]) + "." if sentences else segment.text[:300]
    )
    if platform == "x":
        text = (first_sentence + ".")[:240]
    elif platform == "ig":
        body = first_sentence + "."
        hashtags = "#building #ai #datafirst"
        text = f"{body}\n\n{hashtags}"
    elif platform == "linkedin":
        text = (
            f"{long_body}\n\n"
            "Worth thinking about for anyone shipping LLM features in 2026."
        )
    else:
        text = first_sentence[:280]
    return Caption(platform=platform, text=text, source_segment_id=segment.id)


def caption_writer(segment: Segment, platform: str, examples: list) -> Caption:
    """Generate a platform-specific caption. Few-shot from voice examples."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_caption(segment, platform, examples)
    try:
        from anthropic import Anthropic
    except ImportError:
        return _fallback_caption(segment, platform, examples)

    client = Anthropic(api_key=api_key)
    examples_text = "\n\n".join(f"Example: {e.text}" for e in examples) or "(no examples available)"
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=400,
            temperature=0.4,
            system=CAPTION_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"PLATFORM: {platform}\n\n"
                        f"EXAMPLES (top engagement on this platform):\n{examples_text}\n\n"
                        f"SEGMENT:\n{segment.text}\n\n"
                        "Write the caption."
                    ),
                }
            ],
        )
    except Exception:
        return _fallback_caption(segment, platform, examples)

    text = "".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text").strip()
    if not text:
        return _fallback_caption(segment, platform, examples)
    return Caption(platform=platform, text=text, source_segment_id=segment.id)


# ---------- Stage 3: pipeline orchestration ----------


@dataclass
class PipelineRun:
    scored: list = field(default_factory=list)
    top_segment_id: str = ""
    captions: list = field(default_factory=list)
    review_queue: list = field(default_factory=list)


def run_pipeline(conn: sqlite3.Connection, segments: list, platforms: list = None) -> PipelineRun:
    """
    Score every segment, pick the top, draft captions per platform,
    and emit pending review items. No autopublish.
    """
    if platforms is None:
        platforms = ["x", "ig", "linkedin"]

    scored = [clip_scorer(s) for s in segments]
    scored.sort(key=lambda x: x.score, reverse=True)
    if not scored:
        return PipelineRun()

    top = scored[0]
    top_segment = get_segment(conn, top.segment_id)
    if top_segment is None:
        return PipelineRun(scored=scored)

    captions: list = []
    review: list = []
    for platform in platforms:
        examples = voice_examples(conn, platform, limit=3)
        cap = caption_writer(top_segment, platform, examples)
        captions.append(cap)
        review.append(
            ReviewItem(
                segment_id=top_segment.id,
                platform=platform,
                caption_text=cap.text,
                score=top.score,
            )
        )
    return PipelineRun(
        scored=scored,
        top_segment_id=top.segment_id,
        captions=captions,
        review_queue=review,
    )
