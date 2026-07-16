"""
Hybrid retrieval: BM25 + vector cosine, combined via Reciprocal Rank Fusion.

Module 7 walks through why each piece matters. This file is the reference
implementation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


@dataclass
class IndexedChunk:
    id: str
    text: str
    metadata: dict
    embedding: np.ndarray
    tokens: list[str]


class HybridIndex:
    def __init__(self, embedding_model: str = "BAAI/bge-base-en-v1.5"):
        self.model = SentenceTransformer(embedding_model)
        self.chunks: list[IndexedChunk] = []
        self._bm25: BM25Okapi | None = None
        self._embedding_matrix: np.ndarray | None = None

    def add(self, items: Iterable[dict]) -> None:
        """Add items with shape {id, text, metadata}."""
        new_texts: list[str] = []
        new_meta: list[tuple[str, dict]] = []
        for item in items:
            new_texts.append(item["text"])
            new_meta.append((item["id"], item.get("metadata", {})))

        if not new_texts:
            return

        embeddings = self.model.encode(
            new_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        for (chunk_id, metadata), text, embedding in zip(new_meta, new_texts, embeddings):
            self.chunks.append(
                IndexedChunk(
                    id=chunk_id,
                    text=text,
                    metadata=metadata,
                    embedding=embedding.astype(np.float32),
                    tokens=tokenize(text),
                )
            )
        self._refresh_indexes()

    def _refresh_indexes(self) -> None:
        if not self.chunks:
            self._bm25 = None
            self._embedding_matrix = None
            return
        self._bm25 = BM25Okapi([c.tokens for c in self.chunks])
        self._embedding_matrix = np.vstack([c.embedding for c in self.chunks])

    def search_bm25(self, query: str, top_k: int = 50) -> list[tuple[str, float]]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        order = np.argsort(scores)[::-1][:top_k]
        return [(self.chunks[i].id, float(scores[i])) for i in order if scores[i] > 0]

    def search_vector(self, query: str, top_k: int = 50) -> list[tuple[str, float]]:
        if self._embedding_matrix is None:
            return []
        q = self.model.encode(query, normalize_embeddings=True)
        sims = self._embedding_matrix @ q.astype(np.float32)
        order = np.argsort(sims)[::-1][:top_k]
        return [(self.chunks[i].id, float(sims[i])) for i in order]

    def search_hybrid(self, query: str, top_k: int = 50, rrf_k: int = 60) -> list[tuple[str, float]]:
        """
        Reciprocal Rank Fusion of BM25 and vector results.
        rrf_k=60 is the default from the original RRF paper.
        """
        bm25 = self.search_bm25(query, top_k=top_k)
        vector = self.search_vector(query, top_k=top_k)

        scores: dict[str, float] = {}
        for ranking in (bm25, vector):
            for rank, (chunk_id, _) in enumerate(ranking):
                scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank + 1)

        ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ordered[:top_k]

    def get_chunks(self, chunk_ids: list[str]) -> list[IndexedChunk]:
        index = {c.id: c for c in self.chunks}
        return [index[cid] for cid in chunk_ids if cid in index]
