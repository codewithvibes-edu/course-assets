"""
Agent layer for the research-papers assistant.

  - synthesizer: composes a structured answer with citations
  - citation_validator: rejects outputs that cite paper IDs not in the
    library (catches hallucinated citations before they reach the user)

Heuristic body so the demo runs without API keys. Real implementation:
the synthesizer is an agentic-retrieval LLM call (M8 pattern) with
cite-first prompting; the validator runs against every output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .data import Paper, known_paper_ids, search_papers


@dataclass
class SynthesisResult:
    answer: str
    cited_paper_ids: list[str]
    validation_failures: list[str]


_CITATION_RE = re.compile(r"\(([a-z]+-\d{3,})\)")


def synthesize(question: str, top_k: int = 5) -> SynthesisResult:
    """
    Heuristic synthesis: retrieve top-k papers; produce an outline that
    cites at least one paper per claim. Real impl uses an LLM with
    cite-first prompting + agentic multi-step retrieval.
    """
    papers = search_papers(question, top_k=top_k)
    if not papers:
        return SynthesisResult(
            answer="No matching papers in the library.",
            cited_paper_ids=[],
            validation_failures=[],
        )

    parts = [f"# Synthesis: {question}", ""]
    parts.append("## What the literature says")
    for p in papers:
        result_summary = p.sections.get("results", "").split(".")[0]
        if result_summary:
            parts.append(f"- {result_summary}. ({p.id})")

    parts.extend(["", "## Open questions"])
    parts.append(
        "Each cited paper is a single observation; cross-paper agreement on these "
        "results is uneven and worth your follow-up reading."
    )
    parts.extend(["", "## Bibliography"])
    for p in papers:
        parts.append(f"- ({p.id}) {p.title} — {', '.join(p.authors)} ({p.year}, {p.venue})")

    answer = "\n".join(parts)
    cited_ids = sorted(set(_CITATION_RE.findall(answer)))
    failures = validate_citations(answer)
    return SynthesisResult(answer=answer, cited_paper_ids=cited_ids, validation_failures=failures)


def validate_citations(text: str) -> list[str]:
    """
    Every citation in `text` must match a paper ID known to the library.
    Returns the list of unknown citations (empty list = passed).
    """
    cited = set(_CITATION_RE.findall(text))
    known = known_paper_ids()
    unknown = sorted(cited - known)
    return [f"unknown citation: ({pid})" for pid in unknown]
