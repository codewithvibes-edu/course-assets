"""
Eval set for the research-papers assistant. Two flavors:
  - retrieval: question -> the right paper IDs surface in top-k
  - citation validation: hallucinated citations are caught
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from .agents import synthesize, validate_citations
from .data import search_papers


@dataclass
class RetrievalCase:
    question: str
    expected_paper_ids: set[str]


@dataclass
class CitationCase:
    name: str
    text: str
    expect_failures: bool


RETRIEVAL_CASES: list[RetrievalCase] = [
    RetrievalCase(
        question="hybrid retrieval bm25 vector",
        expected_paper_ids={"lib-001"},
    ),
    RetrievalCase(
        question="reranking quality lift",
        expected_paper_ids={"lib-002"},
    ),
    RetrievalCase(
        question="chunking strategies for long docs",
        expected_paper_ids={"lib-003"},
    ),
    RetrievalCase(
        question="eval set curation team practices",
        expected_paper_ids={"lib-004"},
    ),
]


CITATION_CASES: list[CitationCase] = [
    CitationCase(
        name="known_id_passes",
        text="Hybrid retrieval helps. (lib-001)",
        expect_failures=False,
    ),
    CitationCase(
        name="unknown_id_caught",
        text="Hybrid retrieval helps. (lib-999)",
        expect_failures=True,
    ),
    CitationCase(
        name="multiple_with_one_unknown",
        text="See (lib-001) and (lib-002) and (lib-fake).",
        expect_failures=True,
    ),
    CitationCase(
        name="no_citations_passes",
        text="A general statement with no citation markers.",
        expect_failures=False,
    ),
]


def run_eval(verbose: bool = False) -> dict:
    failures: list[str] = []

    for case in RETRIEVAL_CASES:
        papers = search_papers(case.question, top_k=5)
        retrieved_ids = {p.id for p in papers}
        if not (case.expected_paper_ids & retrieved_ids):
            failures.append(
                f"retrieval: '{case.question}' did not surface any of {case.expected_paper_ids}"
            )
        elif verbose:
            print(f"  [PASS] retrieval: '{case.question[:40]}'")

    for case in CITATION_CASES:
        actual = validate_citations(case.text)
        had_failures = bool(actual)
        if had_failures != case.expect_failures:
            failures.append(
                f"citation: {case.name} expected_failures={case.expect_failures}, "
                f"got_failures={had_failures}"
            )
        elif verbose:
            print(f"  [PASS] citation: {case.name}")

    # End-to-end smoke: synthesize on a known query, check valid citations.
    result = synthesize("hybrid retrieval")
    if result.validation_failures:
        failures.append(f"e2e: synthesis emitted invalid citations: {result.validation_failures}")
    elif verbose:
        print(f"  [PASS] e2e synthesis on 'hybrid retrieval'")

    total = len(RETRIEVAL_CASES) + len(CITATION_CASES) + 1
    return {"total": total, "passed": total - len(failures), "failures": failures}


if __name__ == "__main__":
    result = run_eval(verbose=True)
    print()
    print(f"Pass rate: {result['passed']}/{result['total']}")
    if result["failures"]:
        for f in result["failures"]:
            print(f"  - {f}")
        sys.exit(1)
