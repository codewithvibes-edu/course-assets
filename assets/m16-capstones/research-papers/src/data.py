"""
Library data layer. The sample papers below are FICTIONAL placeholders
for the demo. Replace with your real library (extract text from PDFs
per Module 5 + index per Module 7) before treating this as anything
other than a teaching demo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class Paper:
    id: str
    title: str
    authors: list[str]
    year: int
    venue: str
    sections: dict[str, str]  # 'abstract' / 'methods' / 'results' / 'discussion'
    keywords: list[str] = field(default_factory=list)


# Fictional placeholder library. Each paper is invented for the demo.
# Replace with real ingested papers in production.
SAMPLE_LIBRARY: list[Paper] = [
    Paper(
        id="lib-001",
        title="Hybrid Retrieval Beats Pure Vector on Domain-Specific Corpora",
        authors=["A. Researcher", "B. Researcher"],
        year=2025,
        venue="Workshop on Retrieval Systems",
        sections={
            "abstract": "We compare BM25, vector, and hybrid retrieval on three corpora.",
            "methods": "Three corpora; four embedding models; reciprocal rank fusion.",
            "results": (
                "Hybrid retrieval (BM25+vector via RRF) outperformed pure vector by "
                "8-14 hit-rate points on the technical corpora and was within 1 point "
                "on the general-knowledge corpus."
            ),
            "discussion": (
                "Hybrid wins where exact-string matches matter (codes, names, identifiers). "
                "On general-knowledge corpora the gap closes."
            ),
        },
        keywords=["retrieval", "rag", "bm25", "vector"],
    ),
    Paper(
        id="lib-002",
        title="Reranking as the Single Largest Quality Lift in Production RAG",
        authors=["C. Researcher"],
        year=2026,
        venue="Industrial AI Symposium",
        sections={
            "abstract": "We study the effect of cross-encoder reranking on real workloads.",
            "methods": "Five production RAG pipelines; A/B testing with and without reranking.",
            "results": (
                "Adding a cross-encoder reranker improved final-answer quality by "
                "20-35% across the five pipelines, measured by human-graded rubrics."
            ),
            "discussion": (
                "Reranking helps because retrieval scores are coarse. Joint query-chunk "
                "scoring catches relevance signal that vector or BM25 alone misses."
            ),
        },
        keywords=["rag", "reranking", "production"],
    ),
    Paper(
        id="lib-003",
        title="Chunking Strategies for Long Technical Documents",
        authors=["D. Researcher"],
        year=2024,
        venue="Practical NLP Notes",
        sections={
            "abstract": "We evaluate four chunking strategies on a technical-docs corpus.",
            "methods": "Section-aware, sentence-boundary, fixed-size, contextual.",
            "results": (
                "Section-aware chunks outperformed fixed-size by ~12 points on hit rate. "
                "Contextual prefixes added another 4-6 points on top of section-aware."
            ),
            "discussion": (
                "Document structure carries information that vector embeddings alone "
                "do not capture; chunkers that respect structure perform better."
            ),
        },
        keywords=["chunking", "rag", "technical-docs"],
    ),
    Paper(
        id="lib-004",
        title="Eval Set Curation: A Practitioner Survey",
        authors=["E. Researcher", "F. Researcher"],
        year=2026,
        venue="ML in Practice",
        sections={
            "abstract": "Survey of how teams build and maintain LLM eval sets.",
            "methods": "Interviews with 28 teams across industries.",
            "results": (
                "Teams that maintained eval sets > 30 entries, updated weekly, and gated "
                "releases on regression checks shipped fewer high-severity incidents."
            ),
            "discussion": (
                "Eval discipline correlates with shipping confidence. Teams that skipped "
                "eval sets reported repeated regressions and faith-based deploys."
            ),
        },
        keywords=["evals", "production", "process"],
    ),
]


def load_library() -> list[Paper]:
    return list(SAMPLE_LIBRARY)


def known_paper_ids() -> set[str]:
    return {p.id for p in SAMPLE_LIBRARY}


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text)}


def search_papers(query: str, papers: Iterable[Paper] | None = None, top_k: int = 5) -> list[Paper]:
    """
    Toy retrieval: token-overlap with title + abstract + keywords.
    Real implementation: hybrid retrieval per Module 7.
    """
    pool = list(papers) if papers is not None else load_library()
    query_tokens = _tokens(query)

    scored = []
    for p in pool:
        text = f"{p.title} {p.sections.get('abstract', '')} {' '.join(p.keywords)}"
        overlap = len(query_tokens & _tokens(text))
        if overlap:
            scored.append((overlap, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_k]]
