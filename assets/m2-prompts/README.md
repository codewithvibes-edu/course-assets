# Module 2 — Prompt template library

Reference prompt templates for the patterns covered in module 2. Each
template is a Markdown file with a metadata header (model, intended
use, eval set reference) and a working prompt body.

These are educational starting points, not production-ready guarantees.
Run them through your own eval set before using them in production.

## Templates

| File                                                                   | Pattern                                             | Best for                                  |
| ---------------------------------------------------------------------- | --------------------------------------------------- | ----------------------------------------- |
| [`structured-output-classifier.md`](./structured-output-classifier.md) | Structured JSON output with schema enforcement      | Classification, triage, routing           |
| [`code-with-validation.md`](./code-with-validation.md)                 | Code generation with output validation gates        | Utility code, refactor candidates         |
| [`self-critique-loop.md`](./self-critique-loop.md)                     | Two-pass self-critique pattern                      | Subjective quality (writing, code review) |
| [`structured-extractor.md`](./structured-extractor.md)                 | Extracting structured fields from unstructured text | Receipts, emails, transcripts             |
| [`few-shot-runner.md`](./few-shot-runner.md)                           | Few-shot pattern with rotating examples             | Tone-matching, style transfer             |

## Conventions used in these templates

- Frontmatter declares the model class, default temperature, expected token cost,
  and the eval set reference for the prompt.
- Variables are marked `{{like_this}}`. Replace at template-render time with your
  data; do not concatenate with string interpolation in production code (use a
  proper templating engine).
- Few-shot examples live inline. The model performs better on most tasks with
  3-5 high-quality examples than with abstract instructions.
- Self-critique blocks are marked with comments so you can strip them when not
  needed.

## License

MIT. Use them, adapt them, ship them. No attribution required (anon-brand
courtesy; if your taste says credit the source, your call).
