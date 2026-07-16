# Module 7 — RAG starter repo

A reference Python implementation of the RAG patterns from module 7. Chunking,
hybrid retrieval (BM25 + vector with Reciprocal Rank Fusion), reranking, and
an eval harness that scores precision/recall/hit-rate against a labeled set.

This is educational reference code. It runs end-to-end on a small corpus
without paid services. Real production deployments need adaptations covered
in modules 8 + 12 + 13 + 14.

## What's in here

```
m7-rag-starter/
├── README.md                  # this file
├── requirements.txt           # pinned dependencies
├── pipeline.py                # the full pipeline (chunking → retrieve → rerank)
├── chunking.py                # 4 chunking strategies side-by-side
├── retrieval.py               # BM25 + vector + RRF combine
├── rerank.py                  # cross-encoder rerank
├── eval.py                    # eval harness: precision, recall, hit_rate
├── eval_set.example.yaml      # 5-entry sample eval set
└── corpus/                    # toy corpus for the worked example
    ├── docs/                  # plain-text documents
    └── load.py                # corpus loader
```

## Quick start

```bash
cd m7-rag-starter
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Build the index from the toy corpus
python pipeline.py build

# Run a query
python pipeline.py query "what is reciprocal rank fusion"

# Run the eval suite
python eval.py
```

## Design choices documented in the code

- Embedding model: `BAAI/bge-base-en-v1.5` (open-source, runs locally on CPU
  for small corpora). Module 7 covers when to use commercial embeddings.
- Chunking: section-aware with sentence-boundary fallback. ~400 tokens per
  chunk with 80 tokens of overlap. Tunable in `chunking.py`.
- Retrieval: BM25 + vector cosine, combined via Reciprocal Rank Fusion (RRF)
  with k=60. Top 50 from the combined ranking go to the reranker.
- Reranking: `BAAI/bge-reranker-base` cross-encoder. Top 5 of the reranked
  list is what would go into a downstream LLM prompt.
- Storage: pgvector for production; the starter uses an in-memory
  numpy-backed index for simplicity.
- Eval: deterministic precision/recall/hit_rate against a labeled YAML
  eval set. Module 12 expands this with model-graded and human eval.

## Migration to production

This starter is single-machine, single-process, in-memory. To take it to
production:

1. Replace the in-memory index with pgvector (Postgres + the pgvector
   extension). The retrieval interface stays the same; only `retrieval.py`
   changes.
2. Run ingestion as a separate scheduled job; do not rebuild on every
   query.
3. Wire trace logging per module 12 so retrieval quality can be debugged
   in production.
4. Add caching for embeddings (the embedding step is deterministic per
   input + model, so re-embedding is wasted work).
5. Add reranker batching and concurrency. The starter does one query
   at a time.

## License

MIT. Use, adapt, ship. No attribution required.
