"""Draft a substantial-equivalence comparison table where every cell points to its source.

Claude fills each row using only retrieved chunks and must cite a chunk_id plus an exact
evidence quote. validate_cells() drops any cell whose citation was not retrieved or whose
quote is not in the cited chunk. Dropped cells show as "Not found in source", never as a guess.
"""
import re

from .retrieve import Chunk, Retriever

DEFAULT_ROWS = ["Intended use", "Technology / principle of operation", "Materials",
                "Energy source", "Sterilization", "Performance testing"]

SYSTEM = (
    "You help draft a 510(k) substantial equivalence comparison. Use ONLY the provided chunks. "
    'Return JSON only: {"cells": [{"row": "...", "value": "...", "chunk_id": "...", "evidence": "..."}]}. '
    "evidence must be copied exactly from the chunk. If a row is not covered, omit it."
)

NOT_FOUND = "Not found in source"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def validate_cells(cells: list[dict], retrieved: dict[str, Chunk], rows: list[str]) -> list[dict]:
    kept = {}
    for c in cells:
        row, cid, ev = c.get("row"), c.get("chunk_id"), c.get("evidence", "")
        if row not in rows or row in kept:
            continue
        chunk = retrieved.get(cid)
        if chunk is None or not ev or _norm(ev) not in _norm(chunk.text):
            continue
        kept[row] = {"row": row, "value": c.get("value", ""), "chunk_id": cid,
                     "k_number": chunk.k_number, "page": chunk.page, "evidence": ev,
                     "supported": True}
    return [kept.get(r) or {"row": r, "value": NOT_FOUND, "supported": False} for r in rows]


def draft_comparison(subject_description: str, predicate_chunks: list[Chunk], llm,
                     rows: list[str] = DEFAULT_ROWS, per_row: int = 3) -> list[dict]:
    retr = Retriever(predicate_chunks)
    retrieved: dict[str, Chunk] = {}
    for row in rows:
        for chunk, _ in retr.search(f"{row} {subject_description}", k=per_row):
            retrieved[chunk.chunk_id] = chunk
    context = "\n\n".join(f"[{c.chunk_id}] {c.text}" for c in retrieved.values())
    user = (f"Subject device: {subject_description}\nRows: {rows}\n\nChunks from the predicate "
            f"device's 510(k) summary:\n{context}")
    data = llm.complete_json(SYSTEM, user) if retrieved else {"cells": []}
    return validate_cells(data.get("cells", []), retrieved, rows)
