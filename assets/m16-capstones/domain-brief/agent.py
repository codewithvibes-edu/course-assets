"""
# Publishing responsibility
#
# This is educational reference code only. A recurring brief published
# under your own name carries real obligations: data-feed licensing
# limits on republishing raw rows, accuracy about named businesses,
# and a corrections policy when you get one wrong. The claims linter
# below enforces the mechanical part (no named project without a data
# row, no unsupported superlatives, mandatory data-gap disclosure).
# The editorial part is on you. Any deployed version must:
#   - keep an audit log of every published brief
#   - keep the human-review step for anything naming a real company
#   - publish corrections in the next brief, not quietly edit history

Agent layer for the domain intelligence daily brief generator.

Sequential pipeline (module 10, Pattern 2):
    analysis_agent  ->  synthesis_agent  ->  claims linter

Falls back to deterministic logic if ANTHROPIC_API_KEY is unset so the
example runs end-to-end. Real usage exercises the Anthropic Messages
API for analysis + synthesis.

The linter runs whether or not the LLM ran. No autopublish; every
brief lands in a human review queue.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_layer import PERMIT_ID_RE, DailyContext


MODEL = os.environ.get("DOMAIN_BRIEF_MODEL", "claude-sonnet-4-7")


# ---------- Schema ----------


@dataclass
class AnalysisFindings:
    headline: str
    confidence: float  # 0.0 - 1.0, driven by feed coverage + history depth
    similar_outcomes: list = field(default_factory=list)
    activity_summary: str = ""


@dataclass
class Brief:
    title: str
    body: str
    confidence: float
    needs_human_review: bool = True
    validation_failures: list = field(default_factory=list)


# ---------- Claims linter ----------

# Superlatives a permit feed cannot prove. The synthesis prompt forbids
# them; the linter catches them anyway (defense in depth, Module 14).
_SUPERLATIVE_PATTERNS = [
    r"\brecord[-\s]breaking\b",
    r"\bfirst[-\s]ever\b",
    r"\bunprecedented\b",
    r"\blargest\b",
    r"\bguaranteed\b",
]
_SUPERLATIVE_RE = [re.compile(p, re.IGNORECASE) for p in _SUPERLATIVE_PATTERNS]

# Business-style names: capitalized words ending in a corporate suffix.
# Crude on purpose; a deployed linter would check against the applicant
# column instead of pattern-matching prose.
BUSINESS_NAME_RE = re.compile(
    r"\b(?:[A-Z][A-Za-z&'\-]+\s+){1,4}"
    r"(?:LLC|Inc|Corp|Group|Partners|Builders|Development|Construction|Properties|Holdings)\b"
)

# Every brief must disclose data gaps, even when the disclosure is
# "none". Readers calibrate trust on this line.
GAP_DISCLOSURE_PATTERN = re.compile(r"data\s+gaps?", re.IGNORECASE)

# Split on sentence punctuation, plus newlines that start a bullet or
# heading. Wrapped prose lines stay in one sentence so a business name
# and its permit id citation are judged together.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n(?=\s*[-#])")


def _sentences(text: str) -> list:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]


def validate_brief(text: str, known_ids: set = frozenset()) -> list:
    """Return a list of linter failures. Empty list = passed.

    Three rules, all deterministic:
      1. no unsupported superlatives
      2. every cited permit id resolves to a data row, and every named
         business carries a permit id citation in the same sentence
      3. the brief discloses data gaps (or states there were none)
    """
    failures: list = []
    for pattern in _SUPERLATIVE_RE:
        match = pattern.search(text)
        if match:
            failures.append(f"unsupported superlative: {match.group()!r}")
    for pid in sorted(set(PERMIT_ID_RE.findall(text))):
        if known_ids and pid not in known_ids:
            failures.append(f"cites a permit id with no data row: {pid}")
    for sentence in _sentences(text):
        match = BUSINESS_NAME_RE.search(sentence)
        if match and not PERMIT_ID_RE.search(sentence):
            failures.append(
                f"names a business without a permit id citation: {match.group()!r}"
            )
    if not GAP_DISCLOSURE_PATTERN.search(text):
        failures.append("missing the data-gaps disclosure line")
    return failures


# ---------- Stage 1: analysis_agent ----------


ANALYSIS_SYSTEM = """You are an analyst covering commercial construction permits in one metro area, preparing findings for a daily brief.

Given a CONTEXT (today's filings, inspection results, zoning calendar, and prior similar periods with their outcomes), produce a concise headline + activity summary + confidence score (0.0 - 1.0).

Rules:
- Describe what the data shows. Do NOT speculate beyond the rows.
- Cite the permit id for every project you name.
- Do NOT use superlatives ("largest", "first-ever", "record-breaking", "unprecedented"); the feed cannot prove them.
- Stick to structural language: "activity pattern", "filings", "valuation", "in prior similar periods, tracked projects advanced/stalled".
- Confidence reflects feed coverage and history depth, not prediction certainty.

Respond with a JSON object only:
{"headline": "...", "activity_summary": "...", "confidence": <float 0-1>}"""


def _fallback_analysis(ctx: DailyContext) -> AnalysisFindings:
    today = ctx.today
    new_filings = [f for f in today.filings if f.filed_date == today.target_date]
    total_valuation = sum(f.valuation for f in new_filings)
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
        f"Activity pattern: {today.activity_pattern}. {len(new_filings)} new filings, "
        f"${total_valuation:,.0f} combined valuation. {tendency}"
    ).strip()

    passed = sum(1 for i in today.inspections if i.result == "passed")
    failed = sum(1 for i in today.inspections if i.result == "failed")
    activity_summary = (
        f"{len(new_filings)} new filings totaling ${total_valuation:,.0f}; "
        f"{passed} inspections passed, {failed} failed; "
        f"{len(today.zoning_items)} zoning items on this week's calendar."
    )

    complete_feeds = not today.raw_metadata.get("missing_sources")
    return AnalysisFindings(
        headline=headline,
        confidence=0.7 if (complete_feeds and outcomes) else 0.5,
        similar_outcomes=outcomes,
        activity_summary=activity_summary,
    )


def _context_json(ctx: DailyContext) -> str:
    return json.dumps(
        {
            "today": {
                "target_date": ctx.today.target_date,
                "activity_pattern": ctx.today.activity_pattern,
                "filings": [asdict(f) for f in ctx.today.filings],
                "inspections": [asdict(i) for i in ctx.today.inspections],
                "zoning_items": [asdict(z) for z in ctx.today.zoning_items],
                "missing_sources": ctx.today.raw_metadata.get("missing_sources", []),
            },
            "similar_history": [
                {
                    "date": h.target_date,
                    "activity_pattern": h.activity_pattern,
                    "note": h.note,
                    "outcome": h.outcome_label,
                }
                for h in ctx.similar_history
            ],
        },
        indent=2,
    )


def analysis_agent(ctx: DailyContext) -> AnalysisFindings:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_analysis(ctx)
    try:
        from anthropic import Anthropic
    except ImportError:
        return _fallback_analysis(ctx)

    client = Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=400,
            temperature=0.2,
            system=ANALYSIS_SYSTEM,
            messages=[{"role": "user", "content": f"CONTEXT:\n{_context_json(ctx)}"}],
        )
    except Exception:
        return _fallback_analysis(ctx)

    text = "".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text")
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        try:
            obj = json.loads(match.group())
            return AnalysisFindings(
                headline=str(obj.get("headline", "")).strip(),
                confidence=float(obj.get("confidence", 0.5)),
                similar_outcomes=[h.outcome_label for h in ctx.similar_history],
                activity_summary=str(obj.get("activity_summary", "")).strip(),
            )
        except (ValueError, json.JSONDecodeError):
            pass
    return _fallback_analysis(ctx)


# ---------- Stage 2: synthesis_agent ----------


SYNTHESIS_SYSTEM = """You write the daily brief from FINDINGS + DATA + EXAMPLES (prior briefs in the analyst's voice).

Required sections (in this order, as Markdown H2):
1. What got filed          (today's filings, each with permit id, applicant, valuation)
2. Projects that moved     (permits issued, inspections passed)
3. Projects that stalled   (holds, failed inspections, expirations)
4. Similar stretches       (bulleted; prior periods from DATA with their outcomes)
5. What to watch this week (zoning/variance calendar, voice-matched)
6. Data gaps               (must start with "Data gaps:"; disclose any missing or stale feed, or state that all feeds were current)

Rules:
- Every named business or project must carry its permit id in the same sentence. No id, no mention.
- Make no claim about a project without a corresponding data row.
- No superlatives ("largest", "first-ever", "record-breaking", "unprecedented").
- Match the prose voice from EXAMPLES (declarative, no watery qualifiers).
- The final section MUST contain the phrase "Data gaps".

Respond with the Markdown body only. No preamble."""


def _gap_disclosure(ctx: DailyContext) -> str:
    missing = ctx.today.raw_metadata.get("missing_sources", [])
    if missing:
        return (
            f"Data gaps: the {', '.join(missing)} feed(s) did not load this run. "
            "Coverage of those areas is blind today, not clean."
        )
    return "Data gaps: none today; permits, inspections, and zoning feeds all current."


def _fallback_synthesis(ctx: DailyContext, findings: AnalysisFindings) -> str:
    today = ctx.today
    new_filings = [f for f in today.filings if f.filed_date == today.target_date]
    moved = [f for f in today.filings if f.status in ("issued", "finaled")]
    stalled = [f for f in today.filings if f.status in ("on_hold", "expired")]

    parts = ["## What got filed", findings.headline, ""]
    for f in new_filings:
        parts.append(
            f"- {f.permit_id}: {f.applicant} filed {f.project_type} in {f.district}, "
            f"${f.valuation:,.0f} ({f.status}): {f.description}"
        )

    parts.extend(["", "## Projects that moved"])
    for f in moved:
        parts.append(f"- {f.permit_id}: {f.applicant}, {f.district}: status {f.status}: {f.description}")
    for i in today.inspections:
        if i.result == "passed":
            parts.append(f"- {i.permit_id}: {i.inspection_type} inspection passed on {i.inspection_date}: {i.notes}")

    parts.extend(["", "## Projects that stalled"])
    for f in stalled:
        parts.append(f"- {f.permit_id}: {f.applicant}, {f.district}: status {f.status}: {f.description}")
    for i in today.inspections:
        if i.result == "failed":
            parts.append(f"- {i.permit_id}: {i.inspection_type} inspection failed on {i.inspection_date}: {i.notes}")

    parts.extend(["", "## Similar stretches"])
    for h in ctx.similar_history:
        parts.append(f"- {h.target_date} ({h.activity_pattern}): {h.note} ({h.outcome_label})")

    parts.extend(["", "## What to watch this week"])
    for z in today.zoning_items:
        ref = f" [{z.related_permit_id}]" if z.related_permit_id else ""
        parts.append(f"- {z.case_id} hearing {z.hearing_date} ({z.district}, {z.request_type}): {z.summary}{ref}")
    for excerpt in ctx.archive_excerpts:
        parts.append(f"- Voice reference ({excerpt.target_date}): {excerpt.text}")

    parts.extend(["", "## Data gaps", _gap_disclosure(ctx)])
    return "\n".join(parts)


def synthesis_agent(ctx: DailyContext, findings: AnalysisFindings) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_synthesis(ctx, findings)
    try:
        from anthropic import Anthropic
    except ImportError:
        return _fallback_synthesis(ctx, findings)

    client = Anthropic(api_key=api_key)
    examples_text = "\n\n".join(
        f"Example brief (accuracy {e.accuracy:.2f}):\n{e.text}" for e in ctx.archive_excerpts
    )
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1200,
            temperature=0.3,
            system=SYNTHESIS_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"FINDINGS:\n{json.dumps(asdict(findings), indent=2)}\n\n"
                        f"DATA:\n{_context_json(ctx)}\n\n"
                        f"PRIOR BRIEFS (voice examples, accuracy-weighted):\n{examples_text}"
                    ),
                }
            ],
        )
    except Exception:
        return _fallback_synthesis(ctx, findings)
    text = "".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text").strip()
    return text or _fallback_synthesis(ctx, findings)


# ---------- End-to-end ----------


def generate_daily_brief(ctx: DailyContext) -> Brief:
    findings = analysis_agent(ctx)
    body = synthesis_agent(ctx, findings)

    # Defensive: if the LLM omitted the gap disclosure, append it from
    # the pipeline's own feed-load record. The disclosure comes from
    # code, not the model, so it cannot be hallucinated as "all clear".
    if not GAP_DISCLOSURE_PATTERN.search(body):
        body = body.rstrip() + f"\n\n## Data gaps\n{_gap_disclosure(ctx)}"

    failures = validate_brief(body, ctx.known_permit_ids)
    return Brief(
        title=f"Metro permits brief: {ctx.today.target_date}",
        body=body,
        confidence=findings.confidence,
        needs_human_review=True,  # always; this is the rule, not the exception
        validation_failures=failures,
    )
