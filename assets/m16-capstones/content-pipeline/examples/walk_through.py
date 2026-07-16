"""End-to-end walkthrough: rank segments, then caption the top one for X."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents import caption_writer, rank_segments
from src.data import load_segments


def main():
    segments = load_segments()
    print("=== Ranking ===")
    scores = rank_segments(segments)
    for score in scores:
        print(f"  {score.segment_id}  score={score.score}/10  ({score.reason})")

    top = scores[0]
    top_segment = next(s for s in segments if s.id == top.segment_id)

    print()
    print(f"=== Caption for top segment ({top_segment.id}) ===")
    for platform in ("x", "ig", "linkedin"):
        caption = caption_writer(top_segment, platform)
        print(f"\n--- {platform} ---")
        print(caption.text)


if __name__ == "__main__":
    main()
