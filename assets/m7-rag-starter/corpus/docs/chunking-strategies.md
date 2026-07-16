# Chunking strategies

Chunking is splitting documents into pieces small enough to fit in a model's context window. Chunking is more important than people think because it determines what the model can see when answering a question.

## Fixed-size character chunks

The naive default. Splits every N characters with M overlap. Fast and simple. Often wrong because it splits sentences mid-word and loses semantic boundaries.

## Sentence-boundary chunks

Splits at sentence ends. Groups sentences until the chunk hits a token budget. Better than fixed-size because it preserves grammatical boundaries.

## Semantic chunks

Splits at headings or sections first, falls back to paragraphs, then sentences. Tools like LangChain's RecursiveCharacterTextSplitter implement this pattern.

## Document-aware chunks

Uses the document's actual structure. PDF tables stay intact. Code files split at function boundaries. Markdown splits at headings. Highest quality but requires per-format work.

## Contextual chunks

A more recent pattern: prepend a 50-100 word context summary before each chunk before embedding. Embeddings are computed on the contextualized version. Retrieval finds chunks whose context matches the query, not just chunks whose surface words match.
