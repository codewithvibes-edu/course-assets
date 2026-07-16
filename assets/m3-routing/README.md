# Module 3: Routing config + cost-model reference

Reference assets for module 3 (Model selection as a routing problem).
Drop these into a project, swap the model IDs and per-job numbers for
your own, and you have a starting routing table plus a cost projection
sheet to pressure-test it.

These are educational starting points, not production-ready guarantees.
Every dollar number in this folder is a 2026 snapshot and must be
verified against current vendor pricing pages before relying on it for
budget decisions.

## Files

| File                                           | Shape       | Best for                                         |
| ---------------------------------------------- | ----------- | ------------------------------------------------ |
| [`routing-config.json`](./routing-config.json) | JSON config | Wiring jobs to models + fallback chains in code  |
| [`cost-model.csv`](./cost-model.csv)           | CSV         | Per-job monthly cost projection (Excel / Sheets) |
| [`_formulas.md`](./_formulas.md)               | Markdown    | Formulas + assumptions behind the CSV columns    |

## How to use `routing-config.json`

1. Open the file. The top-level keys are `_metadata`, `models`, `fallback_chains`, `jobs`.
2. Replace the model IDs and provider names with the ones you actually use.
3. Refresh every `cost_per_1m_input_usd` and `cost_per_1m_output_usd` against
   the URLs in `_metadata.verify_pricing_urls`.
4. Edit the `jobs` block to match the jobs in your system. Each job entry
   has: primary model, fallback chain reference, temperature, max tokens,
   assumed tokens per call, and an `expected_cost_per_call_usd` computed
   from those assumptions.
5. Load the JSON in your router at startup. Application code refers to
   jobs by their `job_id`, never by model name. When you want to change
   the model behind a job, you edit the config, not the code.

The sample config covers nine jobs: ticket classification, conversation
summarization, structured extraction, customer support drafting, code
review, content drafting, long-doc synthesis, high-stakes structured
output, and embedding generation. Add or remove jobs as needed; the
shape is the contract.

## How to use `cost-model.csv`

1. Open the CSV in Excel, Google Sheets, or any tool that reads CSV.
2. The first ten rows are sample jobs (matching `routing-config.json`).
   The bottom row is the monthly total across all jobs.
3. Replace `calls_per_day` with your real or pessimistic estimate.
4. Replace `input_tokens_per_call` and `output_tokens_per_call` with
   measured averages from 10 real calls per job.
5. Replace per-million rates with current vendor numbers (see `_formulas.md`
   for the pricing URLs).
6. The computed columns (`monthly_input_cost_usd`, `monthly_output_cost_usd`,
   `monthly_total_usd`) need formulas re-applied after a paste. See
   `_formulas.md` for the formula expressions.

## Conventions

- All dollar numbers are 2026-snapshot placeholders. Refresh before relying.
- Self-hosted entries report `$0` per-token cost by convention; capex and
  operating costs are tracked separately.
- Per-job cost estimates assume a single model class for the job. Routing
  to mixed classes within a single job is possible but increases complexity;
  flatten it into separate jobs in the config if you go that route.
- Job IDs in `routing-config.json` and `cost-model.csv` are aligned so
  you can join them in a spreadsheet for sanity checks.

## License

MIT. Use them, adapt them, ship them. No attribution required.
