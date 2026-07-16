"""
# Publishing responsibility
#
# This is educational reference code only. A recurring brief published
# under your own name has concrete failure modes:
#   - data-feed licensing: permit aggregators and city open-data portals
#     carry terms that limit how much raw data you can republish. Read
#     them before your newsletter quotes a feed wholesale.
#   - accuracy about named businesses: getting a fact wrong about a
#     named applicant or project is a correction at best and a legal
#     problem at worst. Keep a corrections policy and keep the
#     human-review step for anything that names a real company.
#   - keep an audit log of every published brief.
# The claims linter in agent.py enforces "no named project without a
# data row" mechanically, but it is a starting point and not a
# substitute for editorial judgment.

Data layer for the domain intelligence daily brief generator.

Running example: commercial construction permits in one metro area.
Three sources feed the pipeline:
  - permit filings (CSV placeholder for a paid permit-data aggregator)
  - inspection results (placeholder for a city open-data portal)
  - zoning/variance calendar items (same portal, different endpoint)
Plus the analyst's own archive of past briefs (JSONL) for
voice-consistency RAG, retrieved accuracy-weighted: briefs whose calls
held up on later review get retrieval preference.

Replace the placeholder fetchers with real API clients and your own
brief archive before treating this as anything beyond a teaching demo.
"""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

# Permit ids look like P-2026-01184. The linter uses this to tie every
# named project back to a data row.
PERMIT_ID_RE = re.compile(r"\bP-\d{4}-\d{4,6}\b")


# ---------- Schema ----------


@dataclass
class PermitFiling:
    """One row from the permit filings feed."""

    permit_id: str
    filed_date: str
    project_type: str  # 'mixed_use' | 'warehouse' | 'hotel' | 'retail' | 'office_tenant_improvement' | ...
    valuation: float
    status: str  # 'filed' | 'in_review' | 'issued' | 'on_hold' | 'expired' | 'finaled'
    district: str
    applicant: str
    description: str


@dataclass
class InspectionResult:
    """One inspection outcome from the city open-data portal."""

    permit_id: str
    inspection_date: str
    inspection_type: str  # 'foundation' | 'framing' | 'final' | ...
    result: str  # 'passed' | 'failed'
    notes: str


@dataclass
class ZoningItem:
    """One upcoming zoning/variance calendar item."""

    case_id: str
    hearing_date: str
    district: str
    request_type: str  # 'variance' | 'rezone' | 'conditional_use'
    related_permit_id: str  # empty string when no permit is tied yet
    summary: str


@dataclass
class FeedSnapshot:
    """A single day's assembled reading across all three sources."""

    target_date: str
    activity_pattern: str  # 'permit_surge' | 'seasonal_slowdown' | 'steady_volume' | 'approval_backlog'
    filings: list[PermitFiling] = field(default_factory=list)
    inspections: list[InspectionResult] = field(default_factory=list)
    zoning_items: list[ZoningItem] = field(default_factory=list)
    raw_metadata: dict = field(default_factory=dict)


@dataclass
class HistoricalPeriod:
    """A prior period's activity pattern with what actually happened.

    outcome_label records whether the project noted in `note` advanced
    (permit issued, inspection passed, broke ground) or stalled (hold,
    failed inspection, expired permit).
    """

    target_date: str
    activity_pattern: str
    note: str  # one-line description naming the tracked project by permit id
    outcome_label: str  # 'advanced' | 'stalled' | 'mixed'


@dataclass
class BriefExcerpt:
    """An excerpt from a past published brief; used for voice-consistency RAG.

    `accuracy` is the share of that brief's scored calls that held up
    on later review (0.0 - 1.0). Retrieval is weighted toward briefs
    that got it right.
    """

    id: str
    target_date: str
    accuracy: float
    text: str


@dataclass
class DailyContext:
    today: FeedSnapshot
    similar_history: list[HistoricalPeriod] = field(default_factory=list)
    archive_excerpts: list[BriefExcerpt] = field(default_factory=list)
    known_permit_ids: set[str] = field(default_factory=set)


# ---------- Ingest ----------


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        return list(reader)


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def ingest_permits(path: Path = None) -> list[PermitFiling]:
    """
    Read the permit filings feed from CSV. Real implementation calls
    the paid aggregator API with retries + idempotency (Module 5).
    """
    if path is None:
        path = FIXTURES_DIR / "permits.csv"
    rows = _read_csv(path)
    return [
        PermitFiling(
            permit_id=r["permit_id"].strip(),
            filed_date=r["filed_date"],
            project_type=r["project_type"].strip().lower(),
            valuation=float(r["valuation"]),
            status=r["status"].strip().lower(),
            district=r["district"],
            applicant=r["applicant"],
            description=r["description"],
        )
        for r in rows
    ]


def ingest_inspections(path: Path = None) -> list[InspectionResult]:
    """Read recent inspection results (city open-data portal placeholder)."""
    if path is None:
        path = FIXTURES_DIR / "inspections.csv"
    rows = _read_csv(path)
    return [
        InspectionResult(
            permit_id=r["permit_id"].strip(),
            inspection_date=r["inspection_date"],
            inspection_type=r["inspection_type"].strip().lower(),
            result=r["result"].strip().lower(),
            notes=r["notes"],
        )
        for r in rows
    ]


def ingest_zoning(path: Path = None) -> list[ZoningItem]:
    """Read upcoming zoning/variance calendar items."""
    if path is None:
        path = FIXTURES_DIR / "zoning.csv"
    rows = _read_csv(path)
    return [
        ZoningItem(
            case_id=r["case_id"].strip(),
            hearing_date=r["hearing_date"],
            district=r["district"],
            request_type=r["request_type"].strip().lower(),
            related_permit_id=r.get("related_permit_id", "").strip(),
            summary=r["summary"],
        )
        for r in rows
    ]


def ingest_history(path: Path = None) -> list[HistoricalPeriod]:
    """Read the archive of prior periods with labeled outcomes (CSV)."""
    if path is None:
        path = FIXTURES_DIR / "history.csv"
    rows = _read_csv(path)
    return [
        HistoricalPeriod(
            target_date=r["target_date"],
            activity_pattern=r["activity_pattern"].strip().lower(),
            note=r["note"],
            outcome_label=r["outcome_label"].strip().lower(),
        )
        for r in rows
    ]


def ingest_brief_archive(path: Path = None) -> list[BriefExcerpt]:
    """Read past brief excerpts for accuracy-weighted voice RAG."""
    if path is None:
        path = FIXTURES_DIR / "brief_archive.jsonl"
    rows = _read_jsonl(path)
    return [
        BriefExcerpt(
            id=r["id"],
            target_date=r["target_date"],
            accuracy=float(r.get("accuracy", 0.5)),
            text=r["text"],
        )
        for r in rows
    ]


# ---------- Activity pattern classification ----------


def classify_activity_pattern(filings: list[PermitFiling], target_date: str) -> str:
    """
    Tag the day with an activity pattern. Teaching heuristic: a real
    implementation classifies over a trailing window (filings per week
    vs seasonal baseline, median days-in-review), not a single day.
    """
    new_today = [f for f in filings if f.filed_date == target_date]
    held = [f for f in filings if f.status == "on_hold"]
    if filings and len(held) / len(filings) >= 0.4:
        return "approval_backlog"
    if len(new_today) >= 3:
        return "permit_surge"
    if len(new_today) <= 1:
        return "seasonal_slowdown"
    return "steady_volume"


def assemble_today_snapshot() -> FeedSnapshot:
    """Pull all three sources and assemble the day's snapshot.

    Records which sources actually loaded so the brief can disclose
    gaps instead of silently synthesizing around missing data.
    """
    filings = ingest_permits()
    inspections = ingest_inspections()
    zoning_items = ingest_zoning()

    if filings:
        target_date = max(f.filed_date for f in filings)
    else:
        target_date = datetime.now(timezone.utc).date().isoformat()

    missing = [
        name
        for name, rows in (
            ("permits", filings),
            ("inspections", inspections),
            ("zoning", zoning_items),
        )
        if not rows
    ]
    return FeedSnapshot(
        target_date=target_date,
        activity_pattern=classify_activity_pattern(filings, target_date),
        filings=filings,
        inspections=inspections,
        zoning_items=zoning_items,
        raw_metadata={
            "source": "fixture_placeholder",
            "missing_sources": missing,
        },
    )


# ---------- Storage ----------


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS permits (
            permit_id TEXT PRIMARY KEY,
            filed_date TEXT NOT NULL,
            project_type TEXT NOT NULL,
            valuation REAL NOT NULL,
            status TEXT NOT NULL,
            district TEXT NOT NULL,
            applicant TEXT NOT NULL,
            description TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_permits_district ON permits(district);
        CREATE TABLE IF NOT EXISTS inspections (
            permit_id TEXT NOT NULL,
            inspection_date TEXT NOT NULL,
            inspection_type TEXT NOT NULL,
            result TEXT NOT NULL,
            notes TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS zoning (
            case_id TEXT PRIMARY KEY,
            hearing_date TEXT NOT NULL,
            district TEXT NOT NULL,
            request_type TEXT NOT NULL,
            related_permit_id TEXT NOT NULL,
            summary TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS history (
            target_date TEXT PRIMARY KEY,
            activity_pattern TEXT NOT NULL,
            note TEXT NOT NULL,
            outcome_label TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_history_pattern ON history(activity_pattern);
        CREATE TABLE IF NOT EXISTS brief_archive (
            id TEXT PRIMARY KEY,
            target_date TEXT NOT NULL,
            accuracy REAL NOT NULL,
            text TEXT NOT NULL
        );
        """
    )


def build_store() -> sqlite3.Connection:
    """In-memory store loaded from fixtures. Idempotent."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _init_schema(conn)

    for p in ingest_permits():
        conn.execute(
            "INSERT OR REPLACE INTO permits VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                p.permit_id,
                p.filed_date,
                p.project_type,
                p.valuation,
                p.status,
                p.district,
                p.applicant,
                p.description,
            ),
        )
    for i in ingest_inspections():
        conn.execute(
            "INSERT INTO inspections VALUES (?, ?, ?, ?, ?)",
            (i.permit_id, i.inspection_date, i.inspection_type, i.result, i.notes),
        )
    for z in ingest_zoning():
        conn.execute(
            "INSERT OR REPLACE INTO zoning VALUES (?, ?, ?, ?, ?, ?)",
            (z.case_id, z.hearing_date, z.district, z.request_type, z.related_permit_id, z.summary),
        )
    for h in ingest_history():
        conn.execute(
            "INSERT OR REPLACE INTO history VALUES (?, ?, ?, ?)",
            (h.target_date, h.activity_pattern, h.note, h.outcome_label),
        )
    for b in ingest_brief_archive():
        conn.execute(
            "INSERT OR REPLACE INTO brief_archive VALUES (?, ?, ?, ?)",
            (b.id, b.target_date, b.accuracy, b.text),
        )
    conn.commit()
    return conn


# ---------- Read API ----------


def find_similar_periods(
    conn: sqlite3.Connection, snapshot: FeedSnapshot, limit: int = 5
) -> list[HistoricalPeriod]:
    """
    Stub similarity lookup: pull prior periods with the same activity
    pattern. Real implementation: vector similarity over a Postgres
    archive of daily snapshots (Module 7).
    """
    rows = conn.execute(
        "SELECT * FROM history WHERE activity_pattern = ? ORDER BY target_date DESC LIMIT ?",
        (snapshot.activity_pattern, limit),
    ).fetchall()
    return [HistoricalPeriod(**dict(r)) for r in rows]


def archive_excerpts(conn: sqlite3.Connection, limit: int = 3) -> list[BriefExcerpt]:
    """
    Accuracy-weighted voice retrieval: past briefs whose calls proved
    out on later review rank first, recency breaks ties. Voice
    consistency plus a quality signal in one query.
    """
    rows = conn.execute(
        "SELECT * FROM brief_archive ORDER BY accuracy DESC, target_date DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [BriefExcerpt(**dict(r)) for r in rows]


def known_permit_ids(conn: sqlite3.Connection) -> set[str]:
    """
    Every permit id the store can vouch for. The claims linter rejects
    any brief that cites an id outside this set: no claim about a
    project without a data row.
    """
    ids: set[str] = set()
    for (pid,) in conn.execute("SELECT permit_id FROM permits"):
        ids.add(pid)
    for (pid,) in conn.execute("SELECT permit_id FROM inspections"):
        ids.add(pid)
    for (pid,) in conn.execute("SELECT related_permit_id FROM zoning WHERE related_permit_id != ''"):
        ids.add(pid)
    # History notes and archived briefs reference projects by id inline.
    for (note,) in conn.execute("SELECT note FROM history"):
        ids.update(PERMIT_ID_RE.findall(note))
    return ids


def load_today_context(conn: sqlite3.Connection) -> DailyContext:
    """Assemble everything the synthesis agent needs."""
    today = assemble_today_snapshot()
    return DailyContext(
        today=today,
        similar_history=find_similar_periods(conn, today),
        archive_excerpts=archive_excerpts(conn),
        known_permit_ids=known_permit_ids(conn),
    )
