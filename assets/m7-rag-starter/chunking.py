"""
Chunking strategies side by side.

Each function takes raw text and produces a list of {"id", "text", "metadata"}
records. Metadata carries source pointers and chunking parameters so retrieval
can trace results back to the source.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"id": self.id, "text": self.text, "metadata": self.metadata}


def _chunk_id(source_id: str, ordinal: int) -> str:
    digest = hashlib.sha1(f"{source_id}:{ordinal}".encode()).hexdigest()[:12]
    return f"{source_id}:{ordinal}:{digest}"


def fixed_size(text: str, source_id: str, *, chunk_chars: int = 1600, overlap_chars: int = 200) -> list[Chunk]:
    """
    Naive default. Split every chunk_chars characters with overlap_chars
    overlap. Fast, simple, often wrong (splits sentences mid-word).
    """
    chunks: list[Chunk] = []
    start = 0
    n = len(text)
    ordinal = 0
    while start < n:
        end = min(start + chunk_chars, n)
        body = text[start:end].strip()
        if body:
            chunks.append(
                Chunk(
                    id=_chunk_id(source_id, ordinal),
                    text=body,
                    metadata={
                        "source_id": source_id,
                        "strategy": "fixed_size",
                        "char_start": start,
                        "char_end": end,
                    },
                )
            )
            ordinal += 1
        if end == n:
            break
        start = end - overlap_chars
    return chunks


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def sentence_boundary(text: str, source_id: str, *, target_chars: int = 1400, overlap_sentences: int = 1) -> list[Chunk]:
    """
    Split at sentence ends (heuristic). Group sentences until target_chars,
    then start a new chunk with overlap_sentences from the previous chunk.
    Better than fixed-size; preserves grammatical boundaries.
    """
    sentences = [s.strip() for s in _SENTENCE_END.split(text) if s.strip()]
    chunks: list[Chunk] = []
    current: list[str] = []
    current_chars = 0
    ordinal = 0

    for sentence in sentences:
        s_chars = len(sentence) + 1
        if current and current_chars + s_chars > target_chars:
            chunks.append(
                Chunk(
                    id=_chunk_id(source_id, ordinal),
                    text=" ".join(current),
                    metadata={
                        "source_id": source_id,
                        "strategy": "sentence_boundary",
                        "sentence_count": len(current),
                    },
                )
            )
            ordinal += 1
            current = current[-overlap_sentences:] if overlap_sentences else []
            current_chars = sum(len(s) + 1 for s in current)
        current.append(sentence)
        current_chars += s_chars

    if current:
        chunks.append(
            Chunk(
                id=_chunk_id(source_id, ordinal),
                text=" ".join(current),
                metadata={
                    "source_id": source_id,
                    "strategy": "sentence_boundary",
                    "sentence_count": len(current),
                },
            )
        )
    return chunks


_HEADING = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)


def section_aware(text: str, source_id: str, *, target_chars: int = 1400) -> list[Chunk]:
    """
    Split at Markdown heading boundaries first; fall back to sentence splits
    for sections that exceed target_chars. Adds the heading hierarchy to
    each chunk's metadata so retrieval can match on document structure.
    """
    # Find heading positions
    heading_matches = list(_HEADING.finditer(text))
    if not heading_matches:
        return sentence_boundary(text, source_id, target_chars=target_chars)

    chunks: list[Chunk] = []
    ordinal = 0

    boundaries = [(m.start(), m.group(1).strip()) for m in heading_matches]
    boundaries.append((len(text), ""))

    for i, (start, heading) in enumerate(boundaries[:-1]):
        end = boundaries[i + 1][0]
        section_text = text[start:end].strip()
        if not section_text:
            continue

        if len(section_text) <= target_chars:
            chunks.append(
                Chunk(
                    id=_chunk_id(source_id, ordinal),
                    text=section_text,
                    metadata={
                        "source_id": source_id,
                        "strategy": "section_aware",
                        "heading": heading,
                    },
                )
            )
            ordinal += 1
        else:
            sub_chunks = sentence_boundary(
                section_text,
                f"{source_id}:section_{i}",
                target_chars=target_chars,
            )
            for sub in sub_chunks:
                sub.metadata["heading"] = heading
                sub.metadata["strategy"] = "section_aware_then_sentence"
                chunks.append(sub)
                ordinal += 1
    return chunks


def contextual(text: str, source_id: str, document_summary: str | None = None, **kwargs) -> list[Chunk]:
    """
    Section-aware chunks with a contextual prefix prepended before embedding.
    This pattern (from Anthropic's contextual retrieval write-up) embeds
    chunks with a 50-100 word context summary so retrieval can match on
    higher-level meaning, not just surface words.

    document_summary: a 1-2 sentence summary of the entire document. If not
    provided, uses the first 200 chars as a heuristic placeholder.
    """
    base_chunks = section_aware(text, source_id, **kwargs)
    summary = document_summary or text[:200].strip()

    for chunk in base_chunks:
        heading = chunk.metadata.get("heading", "")
        prefix = f"[Document context: {summary}] [Section: {heading}]\n\n" if heading else f"[Document context: {summary}]\n\n"
        chunk.text = prefix + chunk.text
        chunk.metadata["strategy"] = "contextual"
        chunk.metadata["has_context_prefix"] = True
    return base_chunks


STRATEGIES = {
    "fixed_size": fixed_size,
    "sentence_boundary": sentence_boundary,
    "section_aware": section_aware,
    "contextual": contextual,
}
