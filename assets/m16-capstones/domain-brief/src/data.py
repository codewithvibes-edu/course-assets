"""
Data layer for the domain intelligence daily brief generator. Pulls
today's permit filings plus inspection and zoning context, looks up
prior similar periods, returns a structured DailyContext object the
synthesis agent works against.

Running example: commercial construction permits in one metro area.
Replace the placeholder fetchers with real API clients (permit
aggregator, city open-data portal) before treating this as anything
other than a teaching demo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any


@dataclass
class PermitFiling:
    """One row from the permit filings feed."""

    permit_id: str
    filed_date: str
    project_type: str   # 'mixed_use' | 'warehouse' | 'hotel' | 'retail' | ...
    valuation: float
    status: str         # 'filed' | 'in_review' | 'issued' | 'on_hold' | 'expired' | 'finaled'
    district: str
    applicant: str
    description: str


@dataclass
class FeedSnapshot:
    """A single day's reading across the sources."""

    target_date: str
    activity_pattern: str  # 'permit_surge' | 'seasonal_slowdown' | 'steady_volume' | 'approval_backlog'
    filings: list[PermitFiling]
    raw_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HistoricalPeriod:
    """A prior period's activity pattern with what actually happened."""

    target_date: str
    activity_pattern: str
    note: str           # one-line description naming the tracked project by permit id
    outcome_label: str  # 'advanced' | 'stalled' | 'mixed'


@dataclass
class DailyContext:
    today: FeedSnapshot
    similar_history: list[HistoricalPeriod]
    archive_excerpts: list[str]


def fetch_today() -> FeedSnapshot:
    """Stub for a real permit-aggregator API call."""
    return FeedSnapshot(
        target_date=date.today().isoformat(),
        activity_pattern="permit_surge",
        filings=[
            PermitFiling(
                permit_id="P-2026-01184",
                filed_date=date.today().isoformat(),
                project_type="mixed_use",
                valuation=18_500_000.0,
                status="filed",
                district="Riverfront",
                applicant="Meridian Commons Development LLC",
                description="Six-story mixed-use with ground-floor retail at 400 Dock St",
            ),
            PermitFiling(
                permit_id="P-2026-01187",
                filed_date=date.today().isoformat(),
                project_type="warehouse",
                valuation=7_200_000.0,
                status="filed",
                district="East Industrial",
                applicant="Bluestem Properties LLC",
                description="Cold-storage addition to the existing distribution facility",
            ),
        ],
        raw_metadata={
            "source": "permit_feed_placeholder",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "missing_sources": [],
        },
    )


def find_similar_periods(snapshot: FeedSnapshot, limit: int = 5) -> list[HistoricalPeriod]:
    """
    Stub history lookup. Real implementation: vector similarity over
    a Postgres archive of prior daily snapshots; return the top-K
    most-similar periods with their actual outcomes attached.
    """
    return [
        HistoricalPeriod(
            target_date="2026-04-22",
            activity_pattern="permit_surge",
            note="Riverfront mixed-use wave: P-2026-01011 cleared plan review in three weeks and broke ground.",
            outcome_label="advanced",
        ),
        HistoricalPeriod(
            target_date="2026-03-15",
            activity_pattern="permit_surge",
            note="Two warehouse filings in East Industrial; P-2026-00788 sat at drainage review for six weeks.",
            outcome_label="stalled",
        ),
        HistoricalPeriod(
            target_date="2026-02-08",
            activity_pattern="permit_surge",
            note="Downtown tenant-improvement cluster; P-2026-00512 issued in nine days.",
            outcome_label="advanced",
        ),
    ][:limit]


def archive_excerpts(snapshot: FeedSnapshot, limit: int = 3) -> list[str]:
    """
    Stub for accuracy-weighted RAG over your archive of prior briefs.
    Real implementation: embed the today snapshot, retrieve top-K
    excerpts weighted by each brief's accuracy score (the share of its
    calls that held up on later review), so the voice examples come
    from briefs that got it right.
    """
    return [
        "A surge in filings is not a surge in construction until plan review "
        "clears; count issued permits, not filed ones.",
        "The drainage desk is the bottleneck for East Industrial; anything "
        "routed there adds a month before you see movement.",
        "Repeat framing failures usually mean a contractor problem, not a "
        "paperwork problem; watch reinspection dates over press releases.",
    ][:limit]


def load_today_context() -> DailyContext:
    today = fetch_today()
    return DailyContext(
        today=today,
        similar_history=find_similar_periods(today),
        archive_excerpts=archive_excerpts(today),
    )
