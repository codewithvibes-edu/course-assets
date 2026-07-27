"""The daily-repo-check job. Deterministic on purpose: the same data
produces the same findings, byte for byte, so workflow eval cases can
assert on it. This is the job the whole module operates: you wrap it as
a reusable workflow, plan around it, schedule it, and recover it.

    python3 scripts/repo_check.py --run-id manual-001

Writes reports/<run-id>.json and prints a one-line summary. Exit 0 when
no findings, exit 1 when findings exist (so schedulers and hooks can
read the outcome without parsing JSON). Running the same run-id twice
overwrites the same report file: one run, one artifact, no duplicates.
"""

import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
STALE_DAYS = 30
# The fixture freezes "today" so findings are deterministic forever.
# A real deployment would use date.today(); the lesson needs stable output.
TODAY = date(2026, 7, 24)


def read_rows(name):
    with open(ROOT / "data" / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_checks():
    findings = []
    inventory = read_rows("inventory.csv")
    suppliers = read_rows("suppliers.csv")
    orders = read_rows("orders.csv")

    known_skus = {row["sku"] for row in inventory}

    for row in inventory:
        counted = datetime.strptime(row["last_counted"], "%Y-%m-%d").date()
        age = (TODAY - counted).days
        if age > STALE_DAYS:
            findings.append({
                "check": "stale_count",
                "item": row["sku"],
                "detail": f"last counted {age} days ago (limit {STALE_DAYS})",
            })
        if row["quantity"] == "0":
            findings.append({
                "check": "zero_stock",
                "item": row["sku"],
                "detail": f"{row['name']} is out of stock",
            })

    for row in suppliers:
        if not row["contact"].strip():
            findings.append({
                "check": "missing_contact",
                "item": row["supplier_id"],
                "detail": f"{row['name']} has no contact on file",
            })

    for row in orders:
        if row["sku"] not in known_skus:
            findings.append({
                "check": "unknown_sku",
                "item": row["order_id"],
                "detail": f"order references {row['sku']}, not in inventory",
            })

    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True,
                        help="stable ID for this run; also the report filename")
    args = parser.parse_args()

    findings = run_checks()
    report = {
        "run_id": args.run_id,
        "checks_run": ["stale_count", "zero_stock", "missing_contact", "unknown_sku"],
        "records_scanned": {
            "inventory": len(read_rows("inventory.csv")),
            "suppliers": len(read_rows("suppliers.csv")),
            "orders": len(read_rows("orders.csv")),
        },
        "findings": findings,
        "outcome": "findings" if findings else "clean",
    }

    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    out = reports / f"{args.run_id}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"[repo-check {args.run_id}] {len(findings)} finding(s) -> {out.relative_to(ROOT)}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
