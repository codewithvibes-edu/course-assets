"""Tests for the reference chunkers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cleaning.chunking import (  # noqa: E402
    chunk_by_sentences,
    chunk_by_speaker_turns,
    chunk_recursive,
    split_sentences,
)


def test_split_sentences_basic():
    text = "First sentence. Second one! Third?"
    assert split_sentences(text) == ["First sentence.", "Second one!", "Third?"]


def test_sentence_chunks_respect_budget_and_carry_provenance():
    text = " ".join(f"Sentence number {i} is here." for i in range(200))
    chunks = list(chunk_by_sentences(text, doc_id="doc-1", max_tokens=100))
    assert len(chunks) > 1
    budget = 100 * 4
    for i, c in enumerate(chunks):
        assert c["doc_id"] == "doc-1"
        assert c["chunk_index"] == i
        assert c["char_count"] <= budget + 40  # overlap sentence slack


def test_sentence_overlap_repeats_tail():
    text = " ".join(f"Sentence number {i} is here." for i in range(50))
    chunks = list(chunk_by_sentences(text, max_tokens=40, overlap_sentences=1))
    for prev, nxt in zip(chunks, chunks[1:]):
        last_sentence = split_sentences(prev["text"])[-1]
        assert nxt["text"].startswith(last_sentence)


def test_recursive_carries_section_headings():
    text = "# Intro\n\nHello there.\n\n# Details\n\nMore words here.\n\nAnother paragraph."
    chunks = list(chunk_recursive(text, doc_id="d", max_tokens=500))
    sections = {c["section"] for c in chunks}
    assert sections == {"Intro", "Details"}


def test_recursive_splits_oversized_paragraph():
    text = "# Big\n\n" + " ".join(f"Word{i} padded sentence goes on." for i in range(400))
    chunks = list(chunk_recursive(text, max_tokens=80))
    assert len(chunks) > 1
    assert all(c["char_count"] <= 80 * 4 + 40 for c in chunks)


def test_speaker_turns_grouped_with_provenance():
    text = "\n".join(
        f"{'alice' if i % 2 == 0 else 'bob'}: message number {i} with some length to it"
        for i in range(60)
    )
    chunks = list(chunk_by_speaker_turns(text, doc_id="ticket-9", max_tokens=100))
    assert len(chunks) > 1
    for i, c in enumerate(chunks):
        assert c["doc_id"] == "ticket-9"
        assert c["chunk_index"] == i
        assert c["turns"]


def test_speaker_turn_oversized_monologue_is_split_not_truncated():
    monologue = " ".join(f"Sentence {i} of the rant continues onward." for i in range(100))
    text = f"alice: {monologue}\nbob: ok"
    chunks = list(chunk_by_speaker_turns(text, max_tokens=80))
    total_text = " ".join(t["text"] for c in chunks for t in c["turns"])
    assert "Sentence 99" in total_text  # nothing silently dropped
    assert len(chunks) > 1
