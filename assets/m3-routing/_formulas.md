# cost-model.csv: formulas, assumptions, and how to use it

The CSV is a flat projection. No formulas live in the file because formulas
do not survive CSV round-trips between Excel, Google Sheets, and version
control. This file documents what each column means, the math behind the
computed columns, and the assumptions you should override before relying
on the numbers.

## Columns

| Column                        | Meaning                                                  | Source                          |
| ----------------------------- | -------------------------------------------------------- | ------------------------------- |
| `job_id`                      | Stable identifier matching `routing-config.json` jobs    | Hand-set per job                |
| `job_name`                    | Human-readable name for the job + model class            | Hand-set per job                |
| `model_class`                 | small / mid / frontier / mid-code / embedding-local      | From `routing-config.json`      |
| `calls_per_day`               | Estimated production volume per day for this job         | Your traffic estimate           |
| `input_tokens_per_call`       | Average input tokens per call (system + user + RAG)      | Measure 10 real calls; round up |
| `output_tokens_per_call`      | Average output tokens per call                           | Measure 10 real calls; round up |
| `input_rate_per_million_usd`  | Provider input price per 1M tokens, USD (2026 snapshot)  | Vendor pricing page; verify     |
| `output_rate_per_million_usd` | Provider output price per 1M tokens, USD (2026 snapshot) | Vendor pricing page; verify     |
| `monthly_input_cost_usd`      | Computed: see formula below                              | Computed                        |
| `monthly_output_cost_usd`     | Computed: see formula below                              | Computed                        |
| `monthly_total_usd`           | Computed: input + output monthly cost                    | Computed                        |

## Formulas

```
monthly_input_cost_usd  = calls_per_day * input_tokens_per_call  * 30 / 1_000_000 * input_rate_per_million_usd
monthly_output_cost_usd = calls_per_day * output_tokens_per_call * 30 / 1_000_000 * output_rate_per_million_usd
monthly_total_usd       = monthly_input_cost_usd + monthly_output_cost_usd
```

If you paste this CSV into Google Sheets or Excel, replace the computed
columns with the formulas above so the projection recomputes when you
change traffic or rates.

### Google Sheets formula (replace D-row 2, copy down)

```
=ROUND(D2 * E2 * 30 / 1000000 * G2, 2)
=ROUND(D2 * F2 * 30 / 1000000 * H2, 2)
=I2 + J2
```

(Column letters assume `job_id, job_name, model_class, calls_per_day,
input_tokens_per_call, output_tokens_per_call, input_rate_per_million_usd,
output_rate_per_million_usd, monthly_input_cost_usd, monthly_output_cost_usd,
monthly_total_usd` = A through K.)

## Assumptions baked into the sample rows

1. **30 days per month.** Round number for projection. Replace with 30.44
   (365.25 / 12) if you want the calendar-accurate version.
2. **Calls-per-day is deterministic.** Real traffic has spikes; bursty
   workloads can hit 3-5x the daily average over an hour. Module 13 covers
   per-task budget caps that bound spike cost.
3. **Tokens-per-call is the average, not the worst case.** Long-context
   outliers (a 50k-token PDF instead of a 2k-token one) wreck cost
   projections. Track p95 input tokens in your traces and revisit.
4. **Per-million rates are 2026 snapshots.** Refresh against:
   - Anthropic: https://www.anthropic.com/pricing
   - OpenAI: https://openai.com/api/pricing
   - Google Gemini: https://ai.google.dev/pricing
   - Together: https://www.together.ai/pricing
   - Fireworks: https://fireworks.ai/pricing
   - Groq: https://groq.com/pricing
5. **Self-hosted entries report $0 per-token cost.** Capex (GPU hardware)
   plus operating costs (power, cooling, ops time) are real but live
   outside the per-call projection. Track them in a separate sheet.
6. **No prompt caching credit applied.** If your provider supports prompt
   caching and your prompts are repeated, real cost can be 30-70% lower
   than this projection shows. The discount is provider-specific; verify.

## How to use this in practice

1. Copy the CSV.
2. Replace `calls_per_day` with your real or pessimistic estimate.
3. Replace `input_tokens_per_call` and `output_tokens_per_call` with
   measured averages from 10 real calls per job.
4. Replace per-million rates with the current vendor numbers.
5. Look at `monthly_total_usd`. If a row is more than 10% of total spend,
   re-examine the routing choice for that job. Frontier model for a job
   that could ship with a mid-size model is the most common cost mistake.
6. Re-run quarterly. Pricing moves; volume moves; model choices age.
