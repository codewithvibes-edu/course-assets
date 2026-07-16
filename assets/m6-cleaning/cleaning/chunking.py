"""Reference chunkers for Module 6.

These are reference ANSWERS, not the assignment. Checklist item m6-2 asks you
to implement a chunking strategy yourself first; come back and diff against
these when yours works (or does not).

Three strategies, matching the module's table:
- sentence-boundary: group sentences up to a token budget
- recursive (semantic): split at headings, fall back to paragraphs, then sentences
- speaker-turn: the customer-support transcript chunker from the worked example

Every chunk carries doc_id + chunk_index so retrieval can cite its source
(Module 7 consumes this). Tokens are approximated at 1 token per 4 characters
for English; for exact Claude counts use Anthropic's count_tokens endpoint.

Stdlib only. No dependencies.
"""

from __future__ import annotations

import re
from typing import Iterator

CHARS_PER_TOKEN = 4  # rough English average; measure on your own corpus

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def split_sentences(text: str) -> list[str]:
    """Naive sentence splitter. Good enough for reference use; it will
    misfire on abbreviations ("Dr. Smith") and decimal numbers. A production
    pipeline uses a real sentence tokenizer."""
    parts = _SENTENCE_END.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def _emit(doc_id: str, chunk_index: int, text: str, extra: dict | None = None) -> dict:
    record = {
        "doc_id": doc_id,
        "chunk_index": chunk_index,
        "text": text,
        "char_count": len(text),
        "approx_tokens": len(text) // CHARS_PER_TOKEN,
    }
    if extra:
        record.update(extra)
    return record


def _split_oversized(unit: str, char_budget: int) -> list[str]:
    """The fallback rule from the module: when one atomic unit exceeds the
    budget, split one level down the hierarchy instead of truncating.
    Here: sentences, then hard character windows as the last resort."""
    if len(unit) <= char_budget:
        return [unit]
    pieces: list[str] = []
    current = ""
    for sentence in split_sentences(unit) or [unit]:
        if len(sentence) > char_budget:
            # Last resort: hard windows. Never silently truncate.
            pieces.extend(
                sentence[i : i + char_budget] for i in range(0, len(sentence), char_budget)
            )
            continue
        if current and len(current) + len(sentence) + 1 > char_budget:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


# ---------------------------------------------------------------------------
# 1. Sentence-boundary chunking
# ---------------------------------------------------------------------------

def chunk_by_sentences(
    text: str,
    doc_id: str = "",
    max_tokens: int = 500,
    overlap_sentences: int = 1,
) -> Iterator[dict]:
    """Group sentences until the chunk approaches the token budget. Each chunk
    repeats the last `overlap_sentences` sentences of the previous chunk."""
    char_budget = max_tokens * CHARS_PER_TOKEN
    sentences: list[str] = []
    for s in split_sentences(text):
        sentences.extend(_split_oversized(s, char_budget))

    chunk: list[str] = []
    chunk_chars = 0
    chunk_index = 0
    for sentence in sentences:
        if chunk and chunk_chars + len(sentence) + 1 > char_budget:
            yield _emit(doc_id, chunk_index, " ".join(chunk))
            chunk_index += 1
            chunk = chunk[-overlap_sentences:] if overlap_sentences else []
            chunk_chars = sum(len(s) + 1 for s in chunk)
        chunk.append(sentence)
        chunk_chars += len(sentence) + 1
    if chunk:
        yield _emit(doc_id, chunk_index, " ".join(chunk))


# ---------------------------------------------------------------------------
# 2. Recursive (semantic) chunking
# ---------------------------------------------------------------------------

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def chunk_recursive(
    text: str,
    doc_id: str = "",
    max_tokens: int = 500,
) -> Iterator[dict]:
    """Split at markdown headings first, fall back to paragraphs, then
    sentences. Each chunk carries the section heading it fell under, which is
    exactly the chunk-level metadata Module 7's citation patterns consume."""
    char_budget = max_tokens * CHARS_PER_TOKEN
    chunk_index = 0

    # Level 1: sections by heading. If no headings, one anonymous section.
    sections: list[tuple[str, str]] = []
    matches = list(_HEADING.finditer(text))
    if not matches:
        sections.append(("", text))
    else:
        if matches[0].start() > 0:
            sections.append(("", text[: matches[0].start()]))
        for i, m in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections.append((m.group(2).strip(), text[m.end() : end]))

    for heading, body in sections:
        body = body.strip()
        if not body:
            continue
        # Level 2: paragraphs within the section.
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        chunk: list[str] = []
        chunk_chars = 0
        for para in paragraphs:
            # Level 3: sentence-split any paragraph that alone busts the budget.
            for piece in _split_oversized(para, char_budget):
                if chunk and chunk_chars + len(piece) + 2 > char_budget:
                    yield _emit(doc_id, chunk_index, "\n\n".join(chunk), {"section": heading})
                    chunk_index += 1
                    chunk = []
                    chunk_chars = 0
                chunk.append(piece)
                chunk_chars += len(piece) + 2
        if chunk:
            yield _emit(doc_id, chunk_index, "\n\n".join(chunk), {"section": heading})
            chunk_index += 1


# ---------------------------------------------------------------------------
# 3. Speaker-turn chunking (the module's worked example, asset edition)
# ---------------------------------------------------------------------------

_TURN = re.compile(r"^(\w+):\s*(.*)")


def chunk_by_speaker_turns(
    text: str,
    doc_id: str = "",
    max_tokens: int = 500,
    overlap: int = 1,
) -> Iterator[dict]:
    """Group consecutive speaker turns until the chunk approaches the token
    budget. Oversized single turns are sentence-split (the fallback rule)
    instead of being emitted oversized like the lesson's teaching version."""
    char_budget = max_tokens * CHARS_PER_TOKEN

    turns: list[dict] = []
    current_speaker = None
    current_text: list[str] = []
    for line in text.split("\n"):
        match = _TURN.match(line)
        if match:
            if current_speaker:
                turns.append({"speaker": current_speaker, "text": " ".join(current_text)})
            current_speaker, message = match.groups()
            current_text = [message]
        else:
            current_text.append(line)
    if current_speaker:
        turns.append({"speaker": current_speaker, "text": " ".join(current_text)})

    # Apply the fallback rule to oversized turns before grouping.
    sized_turns: list[dict] = []
    for turn in turns:
        for piece in _split_oversized(turn["text"], char_budget):
            sized_turns.append({"speaker": turn["speaker"], "text": piece})

    chunk: list[dict] = []
    chunk_chars = 0
    chunk_index = 0
    for turn in sized_turns:
        turn_chars = len(turn["text"]) + len(turn["speaker"]) + 4
        if chunk and chunk_chars + turn_chars > char_budget:
            yield {
                "doc_id": doc_id,
                "chunk_index": chunk_index,
                "turns": chunk,
                "char_count": chunk_chars,
                "approx_tokens": chunk_chars // CHARS_PER_TOKEN,
            }
            chunk_index += 1
            chunk = chunk[-overlap:] if overlap else []
            chunk_chars = sum(len(t["text"]) + len(t["speaker"]) + 4 for t in chunk)
        chunk.append(turn)
        chunk_chars += turn_chars
    if chunk:
        yield {
            "doc_id": doc_id,
            "chunk_index": chunk_index,
            "turns": chunk,
            "char_count": chunk_chars,
            "approx_tokens": chunk_chars // CHARS_PER_TOKEN,
        }
