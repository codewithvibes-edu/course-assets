# Data source inventory worksheet

The four-quadrant exercise from Module 4 formatted as a fillable
worksheet. One project per sheet. For each data source, capture format,
cadence, volume, license, and access cost in the quadrant it belongs to.

The point of the exercise is to surface the data layer before you write a
line of LLM code. The quadrant with the most entries is where most of
your work will go. The quadrant with the fewest is where most of your
underestimates live.

---

## How the quadrants work

Two axes, four cells.

|                          | Free                                         | Paid                                              |
| ------------------------ | -------------------------------------------- | ------------------------------------------------- |
| **You created it**       | **Q1.** Your own data (records, transcripts) | **Q4.** Synthetic data you commissioned           |
| **Someone else made it** | **Q2.** Public data (web, gov, open APIs)    | **Q3.** Paid / licensed data (vendor APIs, feeds) |

Per-source fields to capture (same for every quadrant):

- **name:** specific identifier (`customers_v2 table in production Postgres`, not "customer data")
- **format:** JSON / CSV / SQL query / API / scraping / PDF / etc.
- **cadence:** real-time / hourly / daily / weekly / static
- **volume:** rows, megabytes, files, or whatever unit matches the source
- **license:** owned / public-domain / CC-BY / CC-BY-NC / paid (named) / synthetic
- **access cost:** free / $X per month / $X per call / engineering time only

---

## Worked example (anonymized)

A small team wants to ship an internal research assistant for their
engineering org. The inventory looks like this:

### Q1: Your own data

| name                                    | format       | cadence    | volume         | license | access cost                |
| --------------------------------------- | ------------ | ---------- | -------------- | ------- | -------------------------- |
| `monorepo` (private GitHub Enterprise)  | git + files  | real-time  | 12 GB checkout | owned   | included in GH plan        |
| Internal Notion workspace               | API + export | daily sync | 4,200 pages    | owned   | included in Notion plan    |
| Confluence wiki                         | API          | daily sync | 1,800 pages    | owned   | included in Atlassian plan |
| Slack archive (last 12 months)          | export       | weekly     | 2.1 GB         | owned   | engineering time           |
| Runbooks (Markdown in `ops/` directory) | files        | static     | 80 documents   | owned   | engineering time           |

### Q2: Public data

| name                                        | format         | cadence   | volume       | license                    | access cost       |
| ------------------------------------------- | -------------- | --------- | ------------ | -------------------------- | ----------------- |
| GitHub open-source repos of dependencies    | git + REST API | weekly    | 200 repos    | varied (MIT/Apache mostly) | rate-limited free |
| Stack Overflow (search relevant tags)       | REST API       | on demand | unbounded    | CC-BY-SA                   | rate-limited free |
| Framework official docs (Next.js, Postgres) | HTML scraping  | weekly    | ~3,500 pages | varied                     | engineering time  |

### Q3: Paid / licensed data

| name                                | format | cadence   | volume    | license           | access cost       |
| ----------------------------------- | ------ | --------- | --------- | ----------------- | ----------------- |
| GitHub Advanced Security (CVE feed) | API    | real-time | ~25K CVEs | paid (verify ToS) | included in GH AS |

### Q4: Synthetic data

| name                                                           | format | cadence | volume     | license   | access cost   |
| -------------------------------------------------------------- | ------ | ------- | ---------- | --------- | ------------- |
| Eval set: 40 hand-crafted "what would an engineer ask" prompts | JSONL  | static  | 40 prompts | synthetic | ~$3 API spend |

**Reading the example:** Q1 is the heavy quadrant (five entries, all
engineering-time access cost). Q2 has volume but governance concerns
(rate limits, ToS). Q3 is one line because the team did not need to
license much. Q4 is small but is the gate for prompt changes.

Stalls are most likely in Q1 (governance on Slack archive, PII flagging)
and in Q2 if scraping cadence runs into anti-bot defenses. The cost
center is whichever Q3 contract grows the fastest at scale.

---

## Blank template (copy below for your project)

### Project: **\*\***\*\*\*\***\*\***\_\_**\*\***\*\*\*\***\*\***

**One sentence about what this LLM system is supposed to do:** \***\*\*\*\*\*\*\***\*\*\***\*\*\*\*\*\*\***\_\_\***\*\*\*\*\*\*\***\*\*\***\*\*\*\*\*\*\***

### Q1: Your own data

| name | format | cadence | volume | license | access cost |
| ---- | ------ | ------- | ------ | ------- | ----------- |
|      |        |         |        |         |             |
|      |        |         |        |         |             |
|      |        |         |        |         |             |
|      |        |         |        |         |             |
|      |        |         |        |         |             |

**Notes (governance, PII, who owns access):**

---

### Q2: Public data

| name | format | cadence | volume | license | access cost |
| ---- | ------ | ------- | ------ | ------- | ----------- |
|      |        |         |        |         |             |
|      |        |         |        |         |             |
|      |        |         |        |         |             |
|      |        |         |        |         |             |
|      |        |         |        |         |             |

**Notes (robots.txt, rate limits, copyright posture):**

---

### Q3: Paid / licensed data

| name | format | cadence | volume | license | access cost |
| ---- | ------ | ------- | ------ | ------- | ----------- |
|      |        |         |        |         |             |
|      |        |         |        |         |             |
|      |        |         |        |         |             |
|      |        |         |        |         |             |
|      |        |         |        |         |             |

**Notes (AI-use clause status, redistribution rights, refresh SLA):**

---

### Q4: Synthetic data

| name | format | cadence | volume | license | access cost |
| ---- | ------ | ------- | ------ | ------- | ----------- |
|      |        |         |        |         |             |
|      |        |         |        |         |             |
|      |        |         |        |         |             |

**Notes (generator model, labeling rule, human review status):**

---

---

## After you fill it in

1. Count rows per quadrant. The heaviest quadrant is where most of your
   work will go.
2. For every Q3 row, run the 10-question due-diligence checklist in
   `license-checklist.md`. Send the questions to the vendor in writing.
3. For every Q2 row, check robots.txt, ToS, and the relevant license
   (CC-BY, ODbL, etc.). Module 4 covers the common public licenses.
4. For every Q1 row, trace the full path: who creates it, where it lives,
   who has access, what format, how often it updates, when it last
   changed schema.
5. For every Q4 row, write down which model generated it and on what date.
   Synthetic data passing through your pipeline as if it were real is the
   most common Quadrant 4 failure mode.
6. If Q3 spend at projected volume exceeds 10% of your project budget,
   revisit. Paid data is often replaced by careful Q1 + Q2 combinations.
