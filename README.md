# RegTrace

Evidence workbench for FDA 510(k) submissions. It pulls cleared devices from openFDA,
finds which predicate devices each one cited, stores those links as a Neo4j graph, and drafts
a substantial-equivalence comparison table where every filled cell points to a page in the
predicate's 510(k) summary. Cells the source does not support are left blank instead of guessed.

## How it works

| Step | Code | What happens |
|---|---|---|
| Ingest | `regtrace/openfda.py`, `regtrace/etl.py` | Pages through the openFDA 510(k) API for one product code, drops records without a valid K-number, dedupes by K-number, upserts into PostgreSQL |
| Summaries | `regtrace/pdftext.py` | Downloads each 510(k) summary PDF and stores text page by page; re-runs skip devices already stored |
| Predicates | `regtrace/predicates.py` | Regex baseline finds every K-number on the pages. Claude names the actual predicates with a quote; an answer is kept only if the quote is really on the cited page and contains the K-number |
| Graph | `regtrace/graph.py` | `Device -HAS_PRODUCT_CODE-> ProductCode -UNDER_REGULATION-> Regulation` and `Device -CITES_PREDICATE-> Device`, all written with MERGE |
| Comparison | `regtrace/retrieve.py`, `regtrace/compare.py` | TF-IDF retrieval over page-tagged chunks; Claude fills rows from retrieved chunks only; each cell must cite a retrieved chunk and quote it exactly, or it is dropped |
| Eval | `regtrace/evaluate.py`, `eval/run_eval.py` | Precision/recall of regex vs Claude predicates against devices checked by hand; citation precision on table cells checked by hand |
| App | `api/main.py`, `web/` | FastAPI backend, React + TypeScript frontend |

## Run locally

```bash
pip install -r requirements.txt
export DATABASE_URL=sqlite:///regtrace.db ANTHROPIC_API_KEY=...
python -m regtrace.pipeline ingest --product-code DQA
python -m regtrace.pipeline summaries --product-code DQA --max 50
python -m regtrace.pipeline predicates --product-code DQA --llm
uvicorn api.main:app --reload            # backend on :8000
cd web && npm install && npm run dev     # frontend on :5173
```

Full stack with Postgres and Neo4j: `docker compose up --build`. AWS steps: `deploy/aws.md`.

## Tests

`pytest -q` runs offline with made-up fixtures and fake LLM / Neo4j objects
(no API key needed). CI runs the Python tests and the TypeScript build on every push.

## Results

Not measured yet. Fill this in from `eval/results.json` after labeling:

- Devices checked by hand:
- Predicate extraction, regex: precision / recall
- Predicate extraction, Claude: precision / recall
- Comparison cells checked by hand / citation precision:

## Limits

- The summary PDF URL pattern in `pdftext.py` works for most recent K-numbers; older ones may 404.
- Scanned PDFs with no text layer return empty pages (no OCR yet).
- Output is a draft for a regulatory professional to verify, not submission-ready text.
