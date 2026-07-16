"""
Cross-encoder reranking. Takes the top-50 retrieved candidates and
re-orders by joint query-chunk relevance. Often the single biggest
quality lift in a RAG pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class RerankedChunk:
    id: str
    text: str
    metadata: dict
    score: float


class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base", use_fp16: bool = True):
        # Lazy import so this module can be imported in environments without
        # FlagEmbedding installed (e.g., for static type checking).
        from FlagEmbedding import FlagReranker

        self.model = FlagReranker(model_name, use_fp16=use_fp16)

    def rerank(
        self,
        query: str,
        chunks: Iterable[dict],
        top_k: int = 5,
    ) -> list[RerankedChunk]:
        """
        chunks: iterable of {id, text, metadata}.
        Returns top_k reranked chunks with relevance scores.
        """
        chunks_list = list(chunks)
        if not chunks_list:
            return []
        pairs = [[query, c["text"]] for c in chunks_list]
        scores = self.model.compute_score(pairs, normalize=True)

        # compute_score returns a single float when given a single pair
        if not isinstance(scores, list):
            scores = [scores]

        scored = [
            RerankedChunk(
                id=c["id"],
                text=c["text"],
                metadata=c.get("metadata", {}),
                score=float(s),
            )
            for c, s in zip(chunks_list, scores)
        ]
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]
