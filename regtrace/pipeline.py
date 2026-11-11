"""Command line entry points.

  python -m regtrace.pipeline ingest --product-code DQY
  python -m regtrace.pipeline summaries --product-code DQY --max 50
  python -m regtrace.pipeline predicates --product-code DQY [--llm]
  python -m regtrace.pipeline graph --product-code DQY
"""
import argparse
import json
import os

from . import etl, graph, predicates
from .db import DB


def devices_for(db: DB, code: str, limit: int | None = None) -> list[str]:
    q = "SELECT k_number FROM devices WHERE product_code = ? ORDER BY decision_date DESC"
    rows = [r[0] for r in db.execute(q, (code,)).fetchall()]
    return rows[:limit] if limit else rows


def cmd_ingest(db, a):
    from .openfda import fetch_510k

    rows, stats = etl.clean(fetch_510k(a.product_code, os.environ.get("OPENFDA_API_KEY")))
    etl.load(db, rows)
    print(json.dumps(stats))


def cmd_summaries(db, a):
    from .pdftext import fetch_pages

    got = missing = 0
    for k in devices_for(db, a.product_code, a.max):
        if etl.get_pages(db, k):
            continue  # already have it; re-runs only fetch new devices
        pages = fetch_pages(k)
        if pages:
            etl.load_pages(db, k, pages)
            got += 1
        else:
            missing += 1
    print(json.dumps({"fetched": got, "no_summary_pdf": missing}))


def cmd_predicates(db, a):
    llm = None
    if a.llm:
        from .llm import ClaudeJSON
        llm = ClaudeJSON()
    report = {"devices": 0, "regex": 0, "llm_accepted": 0, "llm_rejected": {}}
    for k in devices_for(db, a.product_code):
        pages = etl.get_pages(db, k)
        if not pages:
            continue
        report["devices"] += 1
        rx = predicates.regex_predicates(k, pages)
        predicates.save(db, k, rx, "regex")
        report["regex"] += len(rx)
        if llm:
            ok, bad = predicates.llm_predicates(k, pages, llm)
            predicates.save(db, k, ok, "llm")
            report["llm_accepted"] += len(ok)
            for b in bad:
                report["llm_rejected"][b["reason"]] = report["llm_rejected"].get(b["reason"], 0) + 1
    print(json.dumps(report))


def cmd_graph(db, a):
    from neo4j import GraphDatabase

    drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
                               auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    cols = etl.COLS
    rows = [dict(zip(cols, r)) for r in db.execute(
        f"SELECT {', '.join(cols)} FROM devices WHERE product_code = ?", (a.product_code,)).fetchall()]
    method = "llm" if a.llm else "regex"
    with drv.session() as s:
        graph.load_devices(s, rows)
        for k in devices_for(db, a.product_code):
            preds = [{"k_number": p, "page": pg} for p, pg in db.execute(
                "SELECT predicate_k, page FROM predicates WHERE k_number = ? AND method = ?",
                (k, method)).fetchall()]
            graph.load_predicates(s, k, preds, method)
    drv.close()
    print(json.dumps({"devices": len(rows), "method": method}))


def main():
    ap = argparse.ArgumentParser(prog="regtrace")
    ap.add_argument("command", choices=["ingest", "summaries", "predicates", "graph"])
    ap.add_argument("--product-code", required=True)
    ap.add_argument("--max", type=int)
    ap.add_argument("--llm", action="store_true")
    a = ap.parse_args()
    db = DB(os.environ.get("DATABASE_URL", "sqlite:///regtrace.db"))
    db.init_schema()
    {"ingest": cmd_ingest, "summaries": cmd_summaries,
     "predicates": cmd_predicates, "graph": cmd_graph}[a.command](db, a)


if __name__ == "__main__":
    main()
