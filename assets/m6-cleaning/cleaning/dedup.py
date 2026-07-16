"""
Three flavors of dedup: exact (hash), fuzzy (Jaccard on shingles),
and embedding-based (cosine similarity on sentence embeddings).
"""

from __future__ import annotations

import hashlib
import re
from typing import Iterable, TypeVar


T = TypeVar("T", bound=dict)

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _content_hash(text: str) -> str:
    """SHA-256 of normalized content. Whitespace + case-insensitive."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def exact_dedup(records: Iterable[T], text_field: str = "text") -> list[T]:
    """
    Drop duplicates whose normalized content hash matches.
    Keeps the first occurrence; preserves input order for the rest.
    """
    seen: set[str] = set()
    out: list[T] = []
    for record in records:
        text = str(record.get(text_field, ""))
        h = _content_hash(text)
        if h in seen:
            continue
        seen.add(h)
        out.append(record)
    return out


def _shingles(text: str, k: int = 3) -> set[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    if len(tokens) < k:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def jaccard_similarity(a: str, b: str, k: int = 3) -> float:
    """Jaccard similarity over k-shingles. 1.0 = identical token sequences."""
    sa = _shingles(a, k)
    sb = _shingles(b, k)
    if not sa or not sb:
        return 0.0
    intersection = len(sa & sb)
    union = len(sa | sb)
    return intersection / union if union else 0.0


def fuzzy_dedup(
    records: list[T],
    text_field: str = "text",
    threshold: float = 0.92,
    shingle_k: int = 3,
) -> list[T]:
    """
    Drop near-duplicates by Jaccard similarity on k-shingles.
    Keeps the longer text when two records are above threshold.
    O(n²); for n > ~10,000 records, swap in MinHash + LSH.
    """
    keep = [True] * len(records)
    shingles = [_shingles(str(r.get(text_field, "")), shingle_k) for r in records]
    lengths = [len(str(r.get(text_field, ""))) for r in records]

    for i in range(len(records)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(records)):
            if not keep[j]:
                continue
            if not shingles[i] or not shingles[j]:
                continue
            sim = len(shingles[i] & shingles[j]) / max(len(shingles[i] | shingles[j]), 1)
            if sim >= threshold:
                # Keep the longer record; drop the shorter.
                if lengths[j] > lengths[i]:
                    keep[i] = False
                    break
                else:
                    keep[j] = False
    return [r for r, k in zip(records, keep) if k]


def embedding_dedup(
    records: list[T],
    text_field: str = "text",
    threshold: float = 0.95,
    embedding_model: str = "BAAI/bge-base-en-v1.5",
) -> list[T]:
    """
    Drop semantic duplicates by embedding cosine similarity. Slower
    than Jaccard but catches paraphrases. Requires sentence-transformers.
    """
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "embedding_dedup requires sentence-transformers + numpy"
        ) from exc

    if not records:
        return []

    model = SentenceTransformer(embedding_model)
    texts = [str(r.get(text_field, "")) for r in records]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    keep = [True] * len(records)
    for i in range(len(records)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(records)):
            if not keep[j]:
                continue
            sim = float(np.dot(embeddings[i], embeddings[j]))
            if sim >= threshold:
                # Keep the longer text
                if len(texts[j]) > len(texts[i]):
                    keep[i] = False
                    break
                else:
                    keep[j] = False
    return [r for r, k in zip(records, keep) if k]
