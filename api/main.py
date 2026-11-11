"""FastAPI backend for the web app."""
import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from regtrace import etl
from regtrace.compare import DEFAULT_ROWS, draft_comparison
from regtrace.db import DB
from regtrace.retrieve import chunk_pages

app = FastAPI(title="RegTrace")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
                   allow_methods=["*"], allow_headers=["*"])


def get_db() -> DB:
    db = DB(os.environ.get("DATABASE_URL", "sqlite:///regtrace.db"))
    db.init_schema()
    return db


def get_llm():
    from regtrace.llm import ClaudeJSON
    return ClaudeJSON()


class CompareRequest(BaseModel):
    subject_description: str
    predicate_k: str
    rows: list[str] = DEFAULT_ROWS


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/devices")
def devices(product_code: str, db: DB = Depends(get_db)):
    cur = db.execute("SELECT k_number, device_name, applicant, decision_date FROM devices "
                     "WHERE product_code = ? ORDER BY decision_date DESC LIMIT 200",
                     (product_code.upper(),))
    return [dict(zip(["k_number", "device_name", "applicant", "decision_date"], r))
            for r in cur.fetchall()]


@app.get("/devices/{k_number}/predicates")
def device_predicates(k_number: str, db: DB = Depends(get_db)):
    cur = db.execute("SELECT predicate_k, page, method FROM predicates WHERE k_number = ? "
                     "ORDER BY method, predicate_k", (k_number.upper(),))
    return [dict(zip(["predicate_k", "page", "method"], r)) for r in cur.fetchall()]


@app.post("/compare")
def compare(req: CompareRequest, db: DB = Depends(get_db), llm=Depends(get_llm)):
    k = req.predicate_k.upper()
    pages = etl.get_pages(db, k)
    if not pages:
        raise HTTPException(404, f"No summary text stored for {k}")
    cells = draft_comparison(req.subject_description, chunk_pages(k, pages), llm, req.rows)
    return {"predicate_k": k, "cells": cells}
