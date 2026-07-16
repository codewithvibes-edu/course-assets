"""
Retrieval eval harness. Measures hit rate, MRR, and precision against a
labeled YAML eval set with chunking-invariant labels.

Labels are (source doc, answer substring), NOT chunk ids. Chunk ids change
every time you re-chunk, and the whole point of this harness is comparing
chunking strategies against a fixed ruler. A retrieved chunk counts as
relevant when it comes from the labeled doc AND contains the labeled
answer substring.

Eval set format (eval_set.example.yaml):

    - query: "what is reciprocal rank fusion"
      source_doc_id: "rag-basics.md"
      answer_substring: "summing 1/(k+rank)"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from corpus.load import build_index_from_corpus
from rerank import Reranker


def doc_id_of(chunk_id: str) -> str:
    """Chunk ids look like '{source_id}:{ordinal}:{digest}' (see chunking.py)."""
    return chunk_id.rsplit(":", 2)[0]


def is_relevant(chunk_id: str, chunk_text: str, entry: dict) -> bool:
    return (
        doc_id_of(chunk_id) == entry["source_doc_id"]
        and entry["answer_substring"].lower() in chunk_text.lower()
    )


def evaluate(index, eval_set: list[dict], reranker: Reranker | None = None, top_k: int = 5) -> dict:
    metrics = {"hit_rate": 0.0, "mrr": 0.0, "precision": 0.0, "queries": 0}
    per_query = []
    skipped = 0

    for entry in eval_set:
        query = entry.get("query", "")
        # Skip-unlabeled guard: an entry without both label fields can't score.
        if not entry.get("source_doc_id") or not entry.get("answer_substring"):
            skipped += 1
            continue

        retrieved = index.search_hybrid(query, top_k=50)
        retrieved_chunk_ids = [cid for cid, _ in retrieved]

        chunks = [c.__dict__ for c in index.get_chunks(retrieved_chunk_ids)]
        # Stripped fields the reranker doesn't need
        chunks = [{"id": c["id"], "text": c["text"], "metadata": c["metadata"]} for c in chunks]

        if reranker:
            ranked = reranker.rerank(query, chunks, top_k=top_k)
            final = [(r.id, r.text) for r in ranked]
        else:
            final = [(c["id"], c["text"]) for c in chunks[:top_k]]

        relevant_flags = [is_relevant(cid, text, entry) for cid, text in final]
        hit = 1.0 if any(relevant_flags) else 0.0
        first_rank = relevant_flags.index(True) + 1 if hit else None
        mrr = 1.0 / first_rank if first_rank else 0.0
        precision = sum(relevant_flags) / max(len(relevant_flags), 1)

        metrics["hit_rate"] += hit
        metrics["mrr"] += mrr
        metrics["precision"] += precision
        metrics["queries"] += 1

        per_query.append(
            {
                "query": query[:60] + ("..." if len(query) > 60 else ""),
                "hit": bool(hit),
                "first_relevant_rank": first_rank,
                "precision": round(precision, 3),
                "retrieved": [cid for cid, _ in final],
            }
        )

    n = max(metrics["queries"], 1)
    return {
        "hit_rate": round(metrics["hit_rate"] / n, 3),
        "mrr": round(metrics["mrr"] / n, 3),
        "precision": round(metrics["precision"] / n, 3),
        "queries": metrics["queries"],
        "skipped_unlabeled": skipped,
        "per_query": per_query,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-set", default="eval_set.example.yaml")
    parser.add_argument("--no-rerank", action="store_true")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    print("Building index...")
    index = build_index_from_corpus(Path("corpus/docs"))

    print(f"Loading eval set from {args.eval_set}...")
    with open(args.eval_set) as f:
        eval_set = yaml.safe_load(f) or []

    reranker = None if args.no_rerank else Reranker()

    print(f"Running eval over {len(eval_set)} queries (top_k={args.top_k}, "
          f"rerank={'off' if args.no_rerank else 'on'})...")
    results = evaluate(index, eval_set, reranker=reranker, top_k=args.top_k)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
