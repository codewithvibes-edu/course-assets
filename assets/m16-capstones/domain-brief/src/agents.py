"""
Agent layer for the domain intelligence daily brief.

  - analysis_agent: compares today vs prior similar periods
  - synthesis_agent: writes the structured brief
  - validator: claims linter (unsupported superlatives, uncited
    business names, missing data-gap disclosure) before publish

Bodies are heuristic for the demo so the example runs without API
keys. Real implementation: each agent is a Claude Sonnet call with a
tight system prompt + few-shot from your own past briefs, and the
linter also checks every cited permit id against the data store (see
the root-level agent.py for that version).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .data import DailyContext


# Superlatives a permit feed cannot prove. Flag them all; a human can
# override at review if a data row actually backs one up.
_SUPERLATIVE_PATTERNS = [
    r"\brecord[-\s]breaking\b",
    r"\bfirst[-\s]ever\b",
    r"\bunprecedented\b",
    r"\blargest\b",
    r"\bguaranteed\b",
]
_SUPERLATIVE_RE = [re.compile(p, re.IGNORECASE) for p in _SUPERLATIVE_PATTERNS]

PERMIT_ID_RE = re.compile(r"\bP-\d{4}-\d{4,6}\b")

BUSINESS_NAME_RE = re.compile(
    r"\b(?:[A-Z][A-Za-z&'\-]+\s+){1,4}"
    r"(?:LLC|Inc|Corp|Group|Partners|Builders|Development|Construction|Properties|Holdings)\b"
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n(?=\s*[-#])")


@dataclass
class AnalysisFindings:
    headline: str
    confidence: float           # 0.0 - 1.0
    similar_outcomes: list[str]
    activity_summary: str


@dataclass
class Brief:
    title: str
    body: str
    confidence: float
    needs_human_review: bool
    validation_failures: list[str]


def analysis_agent(ctx: DailyContext) -> AnalysisFindings:
    """
    Compare today's snapshot against prior similar periods. Heuristic
    body; real implementation calls an LLM with the context in a
    structured prompt.
    """
    filings = ctx.today.filings
    total_valuation = sum(f.valuation for f in filings)

    # Outcome tendency from history
    outcomes = [h.outcome_label for h in ctx.similar_history]
    advanced = outcomes.count("advanced")
    stalled = outcomes.count("stalled")
    tendency = ""
    if outcomes:
        tendency = (
            f"In {len(outcomes)} prior similar stretches, tracked projects "
            f"advanced {advanced}x and stalled {stalled}x."
        )

    headline = (
        f"Activity pattern: {ctx.today.activity_pattern}. {len(filings)} filings, "
        f"${total_valuation:,.0f} combined valuation. {tendency}"
    ).strip()

    activity_summary = (
        f"{len(filings)} filings across "
        f"{len({f.district for f in filings})} district(s), "
        f"top project type: {filings[0].project_type if filings else 'n/a'}."
    )

    return AnalysisFindings(
        headline=headline,
        confidence=0.7 if tendency else 0.5,
        similar_outcomes=outcomes,
        activity_summary=activity_summary,
    )


def synthesis_agent(ctx: DailyContext, findings: AnalysisFindings) -> str:
    """Compose the brief body from findings + archive excerpts."""
    parts = [
        "## What got filed",
        findings.headline,
        "",
    ]
    for f in ctx.today.filings:
        parts.append(
            f"- {f.permit_id}: {f.applicant} filed {f.project_type} in {f.district}, "
            f"${f.valuation:,.0f} ({f.status}): {f.description}"
        )
    parts.extend(["", "## Projects that moved"])
    for f in ctx.today.filings:
        if f.status in ("issued", "finaled"):
            parts.append(f"- {f.permit_id}: status {f.status}: {f.description}")
    parts.extend(["", "## Projects that stalled"])
    for f in ctx.today.filings:
        if f.status in ("on_hold", "expired"):
            parts.append(f"- {f.permit_id}: status {f.status}: {f.description}")
    parts.extend(["", "## Similar stretches"])
    for h in ctx.similar_history:
        parts.append(f"- {h.target_date} ({h.activity_pattern}): {h.note} ({h.outcome_label})")
    parts.extend(["", "## What to watch this week"])
    for excerpt in ctx.archive_excerpts:
        parts.append(f"- {excerpt}")
    missing = ctx.today.raw_metadata.get("missing_sources", [])
    if missing:
        gap_line = (
            f"Data gaps: the {', '.join(missing)} feed(s) did not load this run. "
            "Coverage of those areas is blind today, not clean."
        )
    else:
        gap_line = "Data gaps: none today; the permit feed loaded in full."
    parts.extend(["", "## Data gaps", gap_line])
    return "\n".join(parts)


def validate_brief(text: str) -> list[str]:
    """Return a list of linter failure messages. Empty list = passed."""
    failures: list[str] = []
    for pattern in _SUPERLATIVE_RE:
        match = pattern.search(text)
        if match:
            failures.append(f"unsupported superlative: {match.group()[:60]!r}")
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    for sentence in sentences:
        match = BUSINESS_NAME_RE.search(sentence)
        if match and not PERMIT_ID_RE.search(sentence):
            failures.append(
                f"names a business without a permit id citation: {match.group()[:60]!r}"
            )
    if "data gap" not in text.lower():
        failures.append("missing the data-gaps disclosure line")
    return failures


def generate_daily_brief(ctx: DailyContext) -> Brief:
    findings = analysis_agent(ctx)
    body = synthesis_agent(ctx, findings)
    failures = validate_brief(body)
    return Brief(
        title=f"Metro permits brief: {ctx.today.target_date}",
        body=body,
        confidence=findings.confidence,
        needs_human_review=True,  # always; this is the rule, not the exception
        validation_failures=failures,
    )
