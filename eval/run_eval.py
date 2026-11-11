"""Run: python -m eval.run_eval --db sqlite:///regtrace.db --gold eval/gold_predicates.jsonl
         [--cells eval/labeled_cells.jsonl]

gold_predicates.jsonl: one line per device you checked by hand against the PDF:
  {"k_number": "K......", "predicates": ["K......", ...]}
labeled_cells.jsonl: comparison-table cells you checked, each with "correct": true/false.
Results are printed and written to eval/results.json. Nothing here is filled in for you.
"""
import argparse
import json

from regtrace.db import DB
from regtrace.evaluate import score_citations, score_predicates


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def predicted_by_method(db: DB, method: str) -> dict:
    out: dict[str, list[str]] = {}
    for k, p in db.execute("SELECT k_number, predicate_k FROM predicates WHERE method = ?",
                           (method,)).fetchall():
        out.setdefault(k, []).append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--cells")
    a = ap.parse_args()
    db = DB(a.db)
    gold = {r["k_number"]: r["predicates"] for r in read_jsonl(a.gold)}
    results = {m: score_predicates(gold, predicted_by_method(db, m)) for m in ("regex", "llm")}
    if a.cells:
        results["citations"] = score_citations(read_jsonl(a.cells))
    print(json.dumps(results, indent=2))
    with open("eval/results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
