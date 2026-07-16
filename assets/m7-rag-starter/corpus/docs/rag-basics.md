# RAG basics

Retrieval-augmented generation is just: fetch relevant text, paste it into the prompt, ask the model to answer using it.

## Why naive RAG fails

The naive version embeds every chunk, runs cosine search, returns top 5, dumps them into the prompt. This works for demos and fails for serious corpora because each step has a tunable that defaults to wrong.

## Reciprocal Rank Fusion

Reciprocal Rank Fusion (RRF) combines multiple ranked lists by summing 1/(k+rank) across each ranking. The k=60 default comes from the original RRF paper. RRF is parameter-free and handles BM25 + vector retrieval combinations well.

## Reranking

A cross-encoder reranker takes the top 50 retrieved chunks and re-orders them by joint relevance to the query. Cross-encoders are slower than embedding models but more accurate because they consider query and chunk together. The reranker reorders 50 candidates down to 5 that go into the LLM prompt.

## Eval

Without retrieval evaluation you cannot tell if your last change improved anything. Build a 20-30 entry eval set early. Measure precision, recall, and hit rate. Run before any prompt or retrieval change ships.
