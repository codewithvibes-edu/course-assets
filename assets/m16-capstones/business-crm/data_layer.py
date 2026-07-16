"""
Data layer for the CRM intelligence assistant.

Implements the data-spine pattern from module 4: a typed schema, ingest
from multiple sources (CRM accounts JSON, support tickets CSV, notes
JSONL), light cleaning, and SQLite storage. Reads from `fixtures/`
in this directory; falls back to in-memory mode if the SQLite path is
unavailable.

The agent layer (agent.py) talks to this module via stable function
signatures, so you can swap the backend (real Salesforce / HubSpot /
Attio API) without touching agent code.

This is educational reference code. Real production deployments need
adaptations covered in module 13 (cost / reliability) and module 14
(safety) before treating it as shippable for any real workload.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
DEFAULT_DB_PATH = Path(__file__).resolve().parent / ".crm_cache.sqlite"


# ---------- Schema ----------


@dataclass
class Account:
    """Canonical account record. Source-agnostic; populated from CRM ingest."""

    id: str
    name: str
    plan: str
    mrr_cents: int
    contract_start: str
    contract_end: str
    owner: str
    health_score: int  # 0-100; placeholder for real risk modeling
    last_active_at: str = ""

    def renewal_in_days(self) -> int:
        end = datetime.fromisoformat(self.contract_end).replace(tzinfo=timezone.utc)
        return max(0, (end - datetime.now(timezone.utc)).days)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Ticket:
    id: str
    account_id: str
    subject: str
    status: str  # 'open' | 'pending' | 'resolved'
    severity: str  # 'low' | 'medium' | 'high'
    opened_at: str
    last_updated_at: str


@dataclass
class Note:
    id: str
    account_id: str
    author: str
    body: str
    created_at: str


# ---------- Ingest helpers ----------


def _read_json(path: Path) -> list:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    out: list = []
    with path.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def _read_csv(path: Path) -> list:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        return list(reader)


def _clean_text(value: str) -> str:
    """Trim whitespace and collapse internal whitespace. M6 cleaning pattern."""
    return " ".join(value.split())


def ingest_accounts(path: Path = None) -> list:
    """Read CRM accounts JSON; produce typed Account records."""
    if path is None:
        path = FIXTURES_DIR / "accounts.json"
    raw = _read_json(path)
    out = []
    for row in raw:
        out.append(
            Account(
                id=row["id"],
                name=_clean_text(row["name"]),
                plan=row["plan"].strip().lower(),
                mrr_cents=int(row["mrr_cents"]),
                contract_start=row["contract_start"],
                contract_end=row["contract_end"],
                owner=row["owner"].strip().lower(),
                health_score=int(row["health_score"]),
                last_active_at=row.get("last_active_at", ""),
            )
        )
    return out


def ingest_tickets(path: Path = None) -> list:
    """Read support tickets CSV; produce typed Ticket records."""
    if path is None:
        path = FIXTURES_DIR / "tickets.csv"
    raw = _read_csv(path)
    out = []
    for row in raw:
        out.append(
            Ticket(
                id=row["id"],
                account_id=row["account_id"],
                subject=_clean_text(row["subject"]),
                status=row["status"].strip().lower(),
                severity=row["severity"].strip().lower(),
                opened_at=row["opened_at"],
                last_updated_at=row["last_updated_at"],
            )
        )
    return out


def ingest_notes(path: Path = None) -> list:
    """Read account notes JSONL; produce typed Note records."""
    if path is None:
        path = FIXTURES_DIR / "notes.jsonl"
    raw = _read_jsonl(path)
    out = []
    for row in raw:
        out.append(
            Note(
                id=row["id"],
                account_id=row["account_id"],
                author=row["author"].strip().lower(),
                body=_clean_text(row["body"]),
                created_at=row["created_at"],
            )
        )
    return out


# ---------- Storage ----------


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            plan TEXT NOT NULL,
            mrr_cents INTEGER NOT NULL,
            contract_start TEXT NOT NULL,
            contract_end TEXT NOT NULL,
            owner TEXT NOT NULL,
            health_score INTEGER NOT NULL,
            last_active_at TEXT
        );
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            status TEXT NOT NULL,
            severity TEXT NOT NULL,
            opened_at TEXT NOT NULL,
            last_updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_tickets_account ON tickets(account_id);
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            author TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_notes_account ON notes(account_id);
        """
    )


def build_store(db_path=None) -> sqlite3.Connection:
    """
    Build (or rebuild) the SQLite store from fixtures. Idempotent:
    re-running clears + reloads. Pass `:memory:` (str) for in-memory.
    """
    if db_path is None:
        target = ":memory:"
    else:
        target = str(db_path)
        if Path(target).exists():
            Path(target).unlink()
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    _init_schema(conn)

    accounts = ingest_accounts()
    tickets = ingest_tickets()
    notes = ingest_notes()

    conn.executemany(
        "INSERT INTO accounts VALUES (:id, :name, :plan, :mrr_cents, :contract_start, "
        ":contract_end, :owner, :health_score, :last_active_at)",
        [asdict(a) for a in accounts],
    )
    conn.executemany(
        "INSERT INTO tickets VALUES (:id, :account_id, :subject, :status, :severity, "
        ":opened_at, :last_updated_at)",
        [asdict(t) for t in tickets],
    )
    conn.executemany(
        "INSERT INTO notes VALUES (:id, :account_id, :author, :body, :created_at)",
        [asdict(n) for n in notes],
    )
    conn.commit()
    return conn


# ---------- Read API (what the agent calls) ----------


def search_accounts(conn: sqlite3.Connection, query: str, limit: int = 5) -> list:
    """Substring match on name + owner."""
    q = "%" + query.lower() + "%"
    rows = conn.execute(
        "SELECT * FROM accounts WHERE LOWER(name) LIKE ? OR LOWER(owner) LIKE ? LIMIT ?",
        (q, q, limit),
    ).fetchall()
    return [Account(**dict(r)) for r in rows]


def get_account(conn: sqlite3.Connection, account_id: str):
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    return Account(**dict(row)) if row else None


def get_account_notes(conn: sqlite3.Connection, account_id: str, limit: int = 10) -> list:
    rows = conn.execute(
        "SELECT * FROM notes WHERE account_id = ? ORDER BY created_at DESC LIMIT ?",
        (account_id, limit),
    ).fetchall()
    return [Note(**dict(r)) for r in rows]


def get_account_tickets(conn: sqlite3.Connection, account_id: str) -> list:
    rows = conn.execute(
        "SELECT * FROM tickets WHERE account_id = ? ORDER BY opened_at DESC", (account_id,)
    ).fetchall()
    return [Ticket(**dict(r)) for r in rows]


def renewals_within(conn: sqlite3.Connection, days: int) -> list:
    """Accounts whose contract ends within N days; sorted by health (worst first)."""
    threshold = (datetime.now(timezone.utc) + timedelta(days=days)).date().isoformat()
    rows = conn.execute(
        "SELECT * FROM accounts WHERE contract_end <= ? ORDER BY health_score ASC", (threshold,)
    ).fetchall()
    return [Account(**dict(r)) for r in rows]


def at_risk_accounts(conn: sqlite3.Connection, health_threshold: int = 60) -> list:
    rows = conn.execute(
        "SELECT * FROM accounts WHERE health_score < ? ORDER BY health_score ASC",
        (health_threshold,),
    ).fetchall()
    return [Account(**dict(r)) for r in rows]


# ---------- Context assembly (for the agent) ----------


def assemble_account_context(conn: sqlite3.Connection, account_id: str) -> dict:
    """
    Bundle all signal for one account into a single dict the agent can
    pass into a prompt. Keeps the prompt-building code free of DB calls.
    """
    account = get_account(conn, account_id)
    if not account:
        return {"account_id": account_id, "found": False}
    return {
        "found": True,
        "account": account.to_dict(),
        "renewal_in_days": account.renewal_in_days(),
        "notes": [asdict(n) for n in get_account_notes(conn, account_id, limit=5)],
        "tickets": [asdict(t) for t in get_account_tickets(conn, account_id)],
    }


def all_accounts(conn: sqlite3.Connection) -> list:
    rows = conn.execute("SELECT * FROM accounts").fetchall()
    return [Account(**dict(r)) for r in rows]
