"""
Agent layer for the research-papers research assistant.

Pattern: agentic retrieval (Module 8) with cite-first synthesis.
The agent decides whether to search, then synthesizes from retrieved
chunks. Every cited paper ID is validated against the indexed library
(Module 14 pattern: catch hallucinated citations before output).

Uses Anthropic Messages API with tool-use. Falls back to a deterministic
search+synthesis path if ANTHROPIC_API_KEY is unset so the example
runs end-to-end.
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

from data_layer import (
    Chunk,
    Paper,
    all_papers,
    get_chunks,
    get_paper,
    known_paper_ids,
    search_library,
)


MODEL = os.environ.get("RESEARCH_AGENT_MODEL", "claude-sonnet-5")
MAX_TOOL_ROUNDS = 6


SYSTEM_PROMPT = """You are a research-papers assistant working over an indexed library of papers.

Your job: answer "what does the literature say about X" using ONLY papers in the library, with citations.

Rules:
1. Use the tools to retrieve papers. Do not invent papers.
2. Every factual claim must end with a citation in the form (paper_id). Example: "Hybrid retrieval beats pure vector (lib-001)."
3. If the library lacks coverage on the question, say so explicitly. Do not pad with general knowledge.
4. Cite the paper_id, not the title.
5. End with a Bibliography section listing the cited papers (id, title, authors, year)."""


# Citations look like (lib-001). Pattern is permissive enough to catch
# malformed / hallucinated IDs like (lib-fake) so the validator can flag them.
CITATION_RE = re.compile(r"\(([a-z]+-[a-z0-9]+)\)", re.IGNORECASE)


# ---------- Tool schemas ----------

TOOLS: list[dict] = [
    {
        "name": "search_library",
        "description": "Retrieve up to top_k papers most relevant to the query via hybrid retrieval over titles, keywords, and section text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_paper",
        "description": "Fetch the full sections of a single paper by id.",
        "input_schema": {
            "type": "object",
            "properties": {"paper_id": {"type": "string"}},
            "required": ["paper_id"],
        },
    },
]


def _tool_search(conn: sqlite3.Connection, args: dict) -> dict:
    papers = search_library(conn, args["query"], top_k=args.get("top_k", 5))
    return {
        "results": [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "venue": p.venue,
                "abstract": p.sections.get("abstract", ""),
                "keywords": p.keywords,
            }
            for p in papers
        ],
        "count": len(papers),
    }


def _tool_get_paper(conn: sqlite3.Connection, args: dict) -> dict:
    p = get_paper(conn, args["paper_id"])
    if not p:
        return {"found": False, "paper_id": args["paper_id"]}
    return {
        "found": True,
        "id": p.id,
        "title": p.title,
        "authors": p.authors,
        "year": p.year,
        "venue": p.venue,
        "sections": p.sections,
    }


_DISPATCH = {
    "search_library": _tool_search,
    "get_paper": _tool_get_paper,
}


# ---------- Validator ----------


def validate_citations(text: str, library_ids: set) -> list:
    """
    Every (paper_id) citation in `text` must exist in `library_ids`.
    Returns a list of unknown citation IDs (empty list = passed).
    """
    cited = set(CITATION_RE.findall(text))
    unknown = sorted(cited - library_ids)
    return [f"unknown citation: ({pid})" for pid in unknown]


# ---------- Schema ----------


@dataclass
class SynthesisResult:
    answer: str
    cited_paper_ids: list = field(default_factory=list)
    tool_calls: list = field(default_factory=list)
    validation_failures: list = field(default_factory=list)
    raw_stop_reason: str = ""


# ---------- Agentic synthesis ----------


def synthesize(question: str, conn: sqlite3.Connection) -> SynthesisResult:
    library_ids = known_paper_ids(conn)
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return _fallback_synthesize(question, conn, library_ids, reason="ANTHROPIC_API_KEY not set")
    try:
        from anthropic import Anthropic
    except ImportError:
        return _fallback_synthesize(question, conn, library_ids, reason="anthropic SDK not installed")

    client = Anthropic(api_key=api_key)
    messages: list = [{"role": "user", "content": question}]
    tool_calls: list = []

    for _ in range(MAX_TOOL_ROUNDS):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=6000,
                # no temperature: Sonnet 5 rejects sampling params
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
        except Exception as exc:
            return _fallback_synthesize(
                question, conn, library_ids, reason=f"API call failed: {exc}"
            )

        if response.stop_reason != "tool_use":
            text = "".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text")
            cited = sorted(set(CITATION_RE.findall(text)))
            failures = validate_citations(text, library_ids)
            return SynthesisResult(
                answer=text,
                cited_paper_ids=cited,
                tool_calls=tool_calls,
                validation_failures=failures,
                raw_stop_reason=response.stop_reason or "",
            )

        messages.append({"role": "assistant", "content": response.content})
        tool_results: list = []
        for block in response.content:
            if getattr(block, "type", "") != "tool_use":
                continue
            tool_name = block.name
            tool_input = block.input or {}
            tool_calls.append({"name": tool_name, "input": tool_input})
            handler = _DISPATCH.get(tool_name)
            result = handler(conn, tool_input) if handler else {"error": f"unknown tool {tool_name}"}
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return SynthesisResult(
        answer="Agent loop hit max rounds without converging.",
        tool_calls=tool_calls,
        raw_stop_reason="max_rounds",
    )


# ---------- Fallback (no API key) ----------


def _fallback_synthesize(
    question: str, conn: sqlite3.Connection, library_ids: set, reason: str
) -> SynthesisResult:
    """Deterministic search-then-synthesize. Mirrors the agent's intent."""
    papers = search_library(conn, question, top_k=5)
    tool_calls = [{"name": "search_library", "input": {"query": question, "top_k": 5}}]
    if not papers:
        return SynthesisResult(
            answer=(
                f"[FALLBACK MODE - {reason}] The library has no papers matching "
                f"this question. Try a different phrasing."
            ),
            tool_calls=tool_calls,
            raw_stop_reason="fallback",
        )

    parts = [f"# Synthesis: {question}", "", f"_[FALLBACK MODE - {reason}]_", ""]
    parts.append("## What the literature says")
    for p in papers:
        result_text = p.sections.get("results") or p.sections.get("abstract") or ""
        first_sentence = re.split(r"(?<=[.!?])\s+", result_text.strip(), maxsplit=1)[0]
        if first_sentence:
            parts.append(f"- {first_sentence} ({p.id})")
    parts.extend(["", "## Caveats"])
    parts.append(
        "Each cited paper is a single observation. Cross-paper agreement on these results "
        "is uneven and worth your follow-up reading."
    )
    parts.extend(["", "## Bibliography"])
    for p in papers:
        authors = ", ".join(p.authors) if p.authors else "unknown authors"
        parts.append(f"- ({p.id}) {p.title} — {authors} ({p.year}, {p.venue})")

    answer = "\n".join(parts)
    cited = sorted(set(CITATION_RE.findall(answer)))
    failures = validate_citations(answer, library_ids)
    return SynthesisResult(
        answer=answer,
        cited_paper_ids=cited,
        tool_calls=tool_calls,
        validation_failures=failures,
        raw_stop_reason="fallback",
    )
