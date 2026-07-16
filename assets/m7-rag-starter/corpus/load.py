"""Load a corpus of plain-text files into a HybridIndex."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from the m7-rag-starter directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chunking import section_aware
from retrieval import HybridIndex


def build_index_from_corpus(corpus_dir: Path, embedding_model: str = "BAAI/bge-base-en-v1.5") -> HybridIndex:
    index = HybridIndex(embedding_model=embedding_model)
    items = []
    for file_path in sorted(corpus_dir.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix not in (".md", ".txt"):
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        source_id = str(file_path.relative_to(corpus_dir))
        for chunk in section_aware(text, source_id):
            items.append(chunk.to_dict())

    if items:
        index.add(items)
    return index
