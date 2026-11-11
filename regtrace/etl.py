"""Normalize openFDA records, drop duplicates and bad rows, load idempotently."""
import re
from datetime import datetime

from .db import DB

K_RE = re.compile(r"^K\d{6}$")


def _first(v):
    if isinstance(v, list):
        return v[0] if v else None
    return v


def normalize(rec: dict) -> dict | None:
    """Return a clean row, or None if the record has no valid K-number to trace back to."""
    k = (rec.get("k_number") or "").strip().upper()
    if not K_RE.match(k):
        return None
    of = rec.get("openfda") or {}
    raw_date = (rec.get("decision_date") or "").replace("-", "")
    try:
        date = datetime.strptime(raw_date, "%Y%m%d").date().isoformat()
    except ValueError:
        date = None
    return {
        "k_number": k,
        "device_name": (rec.get("device_name") or "").strip() or None,
        "applicant": (rec.get("applicant") or "").strip() or None,
        "product_code": (rec.get("product_code") or "").strip().upper() or None,
        "decision_date": date,
        "decision": rec.get("decision_description"),
        "clearance_type": rec.get("clearance_type"),
        "device_class": _first(of.get("device_class")),
        "regulation_number": _first(of.get("regulation_number")),
        "specialty": _first(of.get("medical_specialty_description")),
    }


def clean(records) -> tuple[list[dict], dict]:
    """Normalize and dedupe by K-number. Returns rows plus counts for the run report."""
    seen, rows = set(), []
    stats = {"raw": 0, "invalid": 0, "duplicate": 0, "kept": 0}
    for rec in records:
        stats["raw"] += 1
        row = normalize(rec)
        if row is None:
            stats["invalid"] += 1
            continue
        if row["k_number"] in seen:
            stats["duplicate"] += 1
            continue
        seen.add(row["k_number"])
        rows.append(row)
    stats["kept"] = len(rows)
    return rows, stats


COLS = ["k_number", "device_name", "applicant", "product_code", "decision_date",
        "decision", "clearance_type", "device_class", "regulation_number", "specialty"]


def load(db: DB, rows: list[dict]) -> int:
    """Upsert rows. Re-running the same load leaves the table unchanged."""
    placeholders = ", ".join("?" for _ in COLS)
    updates = ", ".join(f"{c} = excluded.{c}" for c in COLS[1:])
    q = (f"INSERT INTO devices ({', '.join(COLS)}) VALUES ({placeholders}) "
         f"ON CONFLICT (k_number) DO UPDATE SET {updates}")
    db.executemany(q, [tuple(r[c] for c in COLS) for r in rows])
    db.commit()
    return len(rows)


def load_pages(db: DB, k_number: str, pages: list[str]) -> None:
    q = ("INSERT INTO summary_pages (k_number, page, text) VALUES (?, ?, ?) "
         "ON CONFLICT (k_number, page) DO UPDATE SET text = excluded.text")
    db.executemany(q, [(k_number, i + 1, t) for i, t in enumerate(pages)])
    db.commit()


def get_pages(db: DB, k_number: str) -> list[str]:
    cur = db.execute("SELECT text FROM summary_pages WHERE k_number = ? ORDER BY page", (k_number,))
    return [r[0] for r in cur.fetchall()]
