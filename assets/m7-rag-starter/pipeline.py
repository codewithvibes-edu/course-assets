"""
End-to-end pipeline. Chunks the corpus, builds the hybrid index, runs
queries through retrieve → rerank → return top-k chunks.

CLI:
    python pipeline.py build           # build the index from corpus/docs/
    python pipeline.py query "..."     # run a query
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from corpus.load import build_index_from_corpus
from rerank import Reranker


def run_query(index, reranker, query: str, top_k: int = 5) -> list[dict]:
    retrieved = index.search_hybrid(query, top_k=50)
    chunk_ids = [cid for cid, _ in retrieved]
    chunks = [
        {"id": c.id, "text": c.text, "metadata": c.metadata}
        for c in index.get_chunks(chunk_ids)
    ]
    ranked = reranker.rerank(query, chunks, top_k=top_k)
    return [
        {
            "id": r.id,
            "score": round(r.score, 4),
            "metadata": r.metadata,
            "text_excerpt": r.text[:300],
        }
        for r in ranked
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build", "query"])
    parser.add_argument("query_text", nargs="?", default=None)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    if args.command == "build":
        print("Building index from corpus/docs/...")
        index = build_index_from_corpus(Path("corpus/docs"))
        print(f"Indexed {len(index.chunks)} chunks.")
        return

    if args.command == "query":
        if not args.query_text:
            parser.error("query requires a query string argument")

        index = build_index_from_corpus(Path("corpus/docs"))
        reranker = Reranker()
        results = run_query(index, reranker, args.query_text, top_k=args.top_k)
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
