import os
import tempfile

from regtrace import etl
from regtrace.db import DB
from tests.fixtures import RAW_510K, SUMMARY_PAGES


def _db():
    path = os.path.join(tempfile.mkdtemp(), "t.db")
    db = DB(f"sqlite:///{path}")
    db.init_schema()
    return db


def test_clean_drops_invalid_and_duplicates():
    rows, stats = etl.clean(RAW_510K)
    assert stats == {"raw": 4, "invalid": 1, "duplicate": 1, "kept": 2}
    assert [r["k_number"] for r in rows] == ["K240001", "K240002"]


def test_normalize_fields():
    row = etl.normalize(RAW_510K[0])
    assert row["product_code"] == "DQA"
    assert row["decision_date"] == "2024-01-15"
    assert row["device_class"] == "2" and row["regulation_number"] == "870.2700"
    assert etl.normalize(RAW_510K[3])["decision_date"] is None


def test_load_is_idempotent():
    db = _db()
    rows, _ = etl.clean(RAW_510K)
    etl.load(db, rows)
    etl.load(db, rows)
    assert db.execute("SELECT COUNT(*) FROM devices").fetchone()[0] == 2


def test_pages_round_trip():
    db = _db()
    etl.load_pages(db, "K240001", SUMMARY_PAGES)
    etl.load_pages(db, "K240001", SUMMARY_PAGES)
    assert etl.get_pages(db, "K240001") == SUMMARY_PAGES
