"""
CLI for the content pipeline.

Usage:
    python -m src.main rank
    python -m src.main caption --segment-id seg-002 --platform x
"""

from __future__ import annotations

import argparse
import sys

from .agents import caption_writer, rank_segments
from .data import load_segments


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-platform content pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("rank", help="Score all loaded segments")

    cap = sub.add_parser("caption", help="Generate a platform-specific caption")
    cap.add_argument("--segment-id", required=True)
    cap.add_argument("--platform", required=True, choices=["x", "ig", "linkedin"])

    args = parser.parse_args()
    segments = load_segments()

    if args.cmd == "rank":
        scores = rank_segments(segments)
        for score in scores:
            print(f"  {score.segment_id}  score={score.score}/10  ({score.reason})")
        return 0

    if args.cmd == "caption":
        match = next((s for s in segments if s.id == args.segment_id), None)
        if not match:
            print(f"No segment {args.segment_id}", file=sys.stderr)
            return 2
        caption = caption_writer(match, args.platform)
        print(caption.text)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
