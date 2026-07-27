"""Lesson 5: cluster speech into anonymous speaker labels, then flag what needs review.

The approach is deliberately transparent: cut the VAD speech regions into short
windows, embed each window with a public speaker-embedding model (ECAPA, trained for
telling voices apart), cluster the embeddings into the number of speakers you tell it,
and merge adjacent same-label windows into turns. Purpose-built diarization systems
add overlap detection and speaker-count estimation on top; this one keeps every moving
part visible, and its mistakes are the review queue the lesson is about.

Labels are speaker_00 and speaker_01. They are anonymous on purpose. Nothing in this
tool, or this course, turns a voice into a person's identity.

Usage, from assets/m22-media-lab/ with the recipe venv active:
    python pipeline/diarize.py [--speakers 2]
"""

from __future__ import annotations

import argparse

import numpy as np
import torch
from sklearn.cluster import AgglomerativeClustering
from speechbrain.inference.speaker import EncoderClassifier

from common import WORK_DIR, WORKING_COPY, load_wav_mono16k, read_record, require, work_dir, write_record

WINDOW_S = 1.5
HOP_S = 0.75
MIN_WINDOW_S = 0.5
SHORT_TURN_S = 0.6
AMBIGUOUS_MARGIN = 0.08


def cut_windows(vad_segments: list[dict]) -> list[tuple[float, float]]:
    windows = []
    for seg in vad_segments:
        t = seg["start"]
        while seg["end"] - t >= MIN_WINDOW_S:
            windows.append((round(t, 2), round(min(t + WINDOW_S, seg["end"]), 2)))
            t += HOP_S
    return windows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--speakers", type=int, default=2,
                        help="how many speakers to cluster into; this tool does not guess")
    args = parser.parse_args()

    require(WORKING_COPY, "run the normalize step from the recipe first")
    seg_record = read_record(
        require(WORK_DIR / "segmentation-comparison.json",
                "run pipeline/vad_compare.py first")
    )
    vad_segments = seg_record["vad_segments"]

    samples, sr = load_wav_mono16k(WORKING_COPY)
    wav = torch.tensor(samples, dtype=torch.float32).unsqueeze(0)

    encoder = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir=str(work_dir() / "ecapa-model"),
    )

    windows = cut_windows(vad_segments)
    embeddings = []
    for a, b in windows:
        chunk = wav[:, int(a * sr): int(b * sr)]
        with torch.no_grad():
            emb = encoder.encode_batch(chunk).squeeze().numpy()
        embeddings.append(emb / np.linalg.norm(emb))
    matrix = np.stack(embeddings)

    labels = AgglomerativeClustering(
        n_clusters=args.speakers, metric="cosine", linkage="average"
    ).fit_predict(matrix)

    centroids = [matrix[labels == k].mean(axis=0) for k in range(args.speakers)]
    centroids = [c / np.linalg.norm(c) for c in centroids]

    ambiguous = []
    for i, (a, b) in enumerate(windows):
        sims = sorted((float(matrix[i] @ c) for c in centroids), reverse=True)
        if len(sims) > 1 and sims[0] - sims[1] < AMBIGUOUS_MARGIN:
            ambiguous.append({"start": a, "end": b, "margin": round(sims[0] - sims[1], 3)})

    turns = []
    for (a, b), lab in zip(windows, labels):
        speaker = f"speaker_{lab:02d}"
        if turns and turns[-1]["speaker"] == speaker and a <= turns[-1]["end"] + HOP_S:
            turns[-1]["end"] = max(turns[-1]["end"], b)
            turns[-1]["windows"] += 1
        else:
            turns.append({"speaker": speaker, "start": a, "end": b, "windows": 1})

    short_turns = [t for t in turns if t["end"] - t["start"] < SHORT_TURN_S or t["windows"] == 1]

    record = {
        "tool": "ECAPA embeddings plus agglomerative clustering, pipeline/diarize.py",
        "speakers_requested": args.speakers,
        "window_seconds": WINDOW_S,
        "turns": turns,
        "review_queue": {
            "short_turns": short_turns,
            "ambiguous_windows": ambiguous,
            "note": (
                "Review each flagged span against the audio, and for this fixture "
                "against fixture/call-script.md. Corrections keep the tool's label "
                "and add yours next to it; see lesson 5 in the module."
            ),
        },
        "reading": (
            "Overlapping speech lands in one VAD region and gets whichever label wins "
            "the window, single-word turns can vanish into a neighbor, and one voice "
            "can split across labels. The review queue is where those show up."
        ),
    }
    write_record(work_dir() / "speaker-turns.json", record)

    print(f"\n{len(windows)} windows, {len(turns)} turns, "
          f"{len(short_turns)} short-turn flags, {len(ambiguous)} ambiguous windows")
    for t in turns:
        print(f"  {t['speaker']}  {t['start']:6.2f} - {t['end']:6.2f}  ({t['windows']} windows)")


if __name__ == "__main__":
    main()
