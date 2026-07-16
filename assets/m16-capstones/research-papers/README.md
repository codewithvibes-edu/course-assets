# Capstone Track 7 — Research: paper-library research assistant

## Scenario

A researcher has a personal library of papers. They want a tool that
answers "what does the literature say about X" by surfacing relevant
papers and synthesizing the consensus, disagreements, and open
questions. Works only against the indexed library; cites specific
paper IDs for every claim.

## Architecture

```
paper library (pre-extracted texts)
            │
            ▼
       data_layer.py
   (section-aware chunking M6,
    hybrid-lite retrieval M7,
    SQLite store)
            │
            ▼
         agent.py
   ┌─────────────────────────────┐
   │  agentic retrieval (M8)      │
   │  search_library / get_paper  │
   │       │                       │
   │       ▼                       │
   │  cite-first synthesis (M9)    │
   │       │                       │
   │       ▼                       │
   │  validate_citations (M14)     │
   │  (catches hallucinated IDs)   │
   └─────────────────────────────┘
            │
            ▼
        cited synthesis
        + validation report
```

## What's in here

```
research-papers/
├── README.md
├── requirements.txt
├── data_layer.py          # library ingest + chunking + retrieval
├── agent.py               # tool-use agent + citation validator
├── eval_set.yaml          # 10 cases: retrieval + citation + e2e
├── example.py             # runnable end-to-end
├── fixtures/
│   └── library.json       # 6-paper sample library
└── src/                   # reference module pattern (heuristic baseline)
```

## How to run

```bash
cd assets/m15-capstones/research-papers
pip install -r requirements.txt

# Optional: real Anthropic calls. Without this, fallback mode runs
# the deterministic retrieval+synthesis so the example still produces
# output.
export ANTHROPIC_API_KEY=sk-ant-...

# Walkthrough on three sample questions
python example.py

# Run the eval set
python example.py --eval

# Ask a one-off
python example.py --query "what does the literature say about reranking?"

# List indexed papers
python example.py --list
```

## In scope (v1)

- Ingest a folder of pre-extracted paper texts (real implementation
  uses LlamaParse / pdfplumber on actual PDFs - see Module 5)
- Toy hybrid retrieval (token overlap + title boost + keyword boost)
- Cite-first synthesis: every claim points at a paper ID
- Citation validator: hallucinated IDs caught before output ships
- Eval set with retrieval, citation-validation, and end-to-end cases

## Out of scope (v1)

- PDF parsing (assume pre-extracted; Module 5 covers ingestion)
- Pulling new papers from arXiv / PubMed directly (v1.1 add-on)
- Reranker model (toy retrieval today; production uses a cross-encoder)
- Author / venue filtering UI

## Build first

The library + retrieval. Synthesis quality is bounded by retrieval
quality. Get hit-rate above 0.9 on the eval set before tuning the
synthesis prompt.

## Compliance

- Citations are mandatory. Every claim must reference a paper ID.
- Cited IDs must exist in the indexed library; the validator rejects
  outputs that cite anything else.
- The system prompt forbids using general knowledge to pad answers;
  if the library lacks coverage, the agent says so explicitly.

## Migration notes

For a real research workflow:

1. Replace `ingest_library` with a PDF-extraction pipeline (Module 5).
   LlamaParse for layout-preserving extraction; pdfplumber for
   text-native PDFs.
2. Replace the toy retrieval in `data_layer.search_library` with
   pgvector + a science-tuned embedding model (e.g., specter-v2 or
   BGE-large) + a cross-encoder reranker (Module 7).
3. Add an arXiv / PubMed pull job for ongoing ingestion.
4. Wire the agent output through a `human_review` queue so the
   researcher reads before any synthesis is republished.

## Educational only

Reference code for learning. Real research workflows have IP and
licensing constraints on the papers you've downloaded; the citation
validator does not check that you have the right to redistribute
synthesis. Treat any deployed version of this as having compliance
obligations beyond the technical checks here.
