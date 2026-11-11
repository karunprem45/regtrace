from regtrace.compare import NOT_FOUND, draft_comparison
from regtrace.retrieve import Retriever, chunk_pages
from tests.fixtures import SUMMARY_PAGES, FakeLLM


def test_chunks_keep_page_numbers():
    chunks = chunk_pages("K201234", SUMMARY_PAGES, max_words=15, overlap=5)
    assert all(c.chunk_id.startswith(f"K201234:p{c.page}:") for c in chunks)
    assert {c.page for c in chunks} == {1, 2, 3}


def test_retriever_ranks_relevant_page_first():
    r = Retriever(chunk_pages("K201234", SUMMARY_PAGES))
    top, _ = r.search("battery energy source")[0]
    assert top.page == 3


def test_only_cited_and_verified_cells_survive():
    chunks = chunk_pages("K201234", SUMMARY_PAGES)
    p2 = next(c for c in chunks if c.page == 2).chunk_id
    p3 = next(c for c in chunks if c.page == 3).chunk_id
    llm = FakeLLM({"cells": [
        {"row": "Intended use", "value": "Spot-check SpO2 and pulse rate in adults",
         "chunk_id": p2, "evidence": "spot-check measurement of functional oxygen saturation"},
        {"row": "Energy source", "value": "Two AAA batteries", "chunk_id": p3,
         "evidence": "two AAA alkaline batteries"},
        {"row": "Materials", "value": "Titanium", "chunk_id": p3,
         "evidence": "titanium housing"},                       # quote not in source
        {"row": "Sterilization", "value": "EtO", "chunk_id": "K201234:p9:c0",
         "evidence": "ethylene oxide"},                          # chunk never retrieved
    ]})
    rows = ["Intended use", "Energy source", "Materials", "Sterilization"]
    cells = draft_comparison("finger pulse oximeter for adults", chunks, llm, rows)
    by_row = {c["row"]: c for c in cells}
    assert by_row["Intended use"]["supported"] and by_row["Intended use"]["page"] == 2
    assert by_row["Energy source"]["k_number"] == "K201234"
    assert by_row["Materials"]["value"] == NOT_FOUND
    assert by_row["Sterilization"]["value"] == NOT_FOUND
    assert [c["row"] for c in cells] == rows
