# Module 4: Data source inventory + vendor sheet + license checklist

Reference assets for module 4 (The data sources that matter). The spine
module for the rest of the course. The exercise here is mechanical: take
the four-quadrant map, list every data source for your project, and walk
the questions that follow.

These are educational starting points, not production-ready guarantees.
Vendor names, pricing, and license terms are 2026 Q2 snapshots and must
be verified directly with each vendor before relying on them.

## Files

| File                                                         | Shape          | Best for                                              |
| ------------------------------------------------------------ | -------------- | ----------------------------------------------------- |
| [`data-inventory-template.md`](./data-inventory-template.md) | Worksheet      | Filling in the four-quadrant inventory for a project  |
| [`vendor-sheet-2026.md`](./vendor-sheet-2026.md)             | Reference list | Starting list of free / paid / synthetic providers    |
| [`license-checklist.md`](./license-checklist.md)             | Checklist      | 10-question due-diligence checklist for paid licenses |

## How to use these together

1. Open `data-inventory-template.md`. Copy the blank template section
   into a doc for your own project.
2. Fill in every data source you can think of, broken across the four
   quadrants (your own data, public, paid, synthetic).
3. For any Q2 (public) entry, check the relevant license (CC-BY, ODbL,
   public domain), robots.txt, and the provider's rate limits. The
   `vendor-sheet-2026.md` lists common Q2 providers.
4. For any Q3 (paid) entry, run `license-checklist.md` against the
   vendor in writing. Save the responses with the contract.
5. For any Q4 (synthetic) entry, document the generator model, the
   generation date, and the human-review status. Synthetic data passing
   through your pipeline as if it were real is the most common Q4
   failure mode.

## Conventions

- Vendor names and pricing in `vendor-sheet-2026.md` are May 2026
  snapshots. The list churns quarterly because the paid-data space is
  consolidating; the watch note at the top of the sheet explains the
  pattern.
- The license checklist is a primer, not legal advice. Route any
  material-risk question through a lawyer who knows AI / data law.
- The inventory template uses Markdown tables so it round-trips
  through GitHub, Notion, and most text editors without formatting loss.

## License

MIT. Use them, adapt them, ship them. No attribution required.
