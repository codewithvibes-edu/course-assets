# Reference outputs: the course's verified run

These are the records the course team produced by running the full pipeline against
the frozen fixture on 2026-07-25 (macOS, Apple silicon, the pinned versions from the
recipe). They exist for two reasons: so you can compare your outputs to a known-good
run at every step, and so the module prose can cite measured numbers instead of
invented ones.

Your numbers will not match these exactly. Model updates, OS versions, and hardware
change timings and can nudge words and probabilities. The shape should match; the
story the numbers tell should match; byte equality is not the goal.

What each file is:

- `segmentation-comparison.json`: Silero VAD versus fixed 5 second windows. The 3.5s
  hold silence shows up as the one large gap; 10 of 14 fixed boundaries land inside
  speech.
- `transcript-tiny-batch.json` and `transcript-small-batch.json`: the model-size
  comparison. tiny put 13 words under probability 0.5 on this audio, small put 5.
- `transcript-small-stream.json`: same decode consumed incrementally; first segment
  at 3.7s against 9.0s total on the course machine.
- `corrections.json`: the reviewed verdict on the one real transcription error, with
  the detail worth remembering: the wrong word ("-seater" for "cedar") carried
  probability 0.743, above the review threshold. Reading caught it, the queue did not.
- `transcript-reviewed.json`: corrections applied, original hypothesis preserved.
- `speaker-turns.json`: 15 anonymous turns. The engineered overlap appears as two
  turns overlapping in time near 38.8s; the 0.4s "Done." fell below the window floor
  and has no turn at all, which lesson 5 has you find.
- `frame-manifest.json` and `frame-ocr.json`: 12 retained frames across the three
  strategies, all four scene cuts caught at the measured 0.02 threshold, OCR read with its usual small errors (a chart bar read as stray letters, a date line ending in a pipe).
- `transcript.json`: the joined, schema-valid data product, consent and retention
  fields filled, every derived artifact named for the deletion drill.
