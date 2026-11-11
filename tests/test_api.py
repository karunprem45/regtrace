import os
import tempfile

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from api import main  # noqa: E402
from regtrace import etl  # noqa: E402
from regtrace.db import DB  # noqa: E402
from tests.fixtures import RAW_510K, SUMMARY_PAGES, FakeLLM  # noqa: E402


def _client(llm):
    path = os.path.join(tempfile.mkdtemp(), "api.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{path}"
    db = DB(os.environ["DATABASE_URL"])
    db.init_schema()
    etl.load(db, etl.clean(RAW_510K)[0])
    etl.load_pages(db, "K201234", SUMMARY_PAGES)
    main.app.dependency_overrides[main.get_llm] = lambda: llm
    return TestClient(main.app)


def test_devices_and_compare():
    c = _client(FakeLLM({"cells": []}))
    assert c.get("/health").json() == {"ok": True}
    assert len(c.get("/devices", params={"product_code": "dqa"}).json()) == 2
    r = c.post("/compare", json={"subject_description": "oximeter", "predicate_k": "k201234",
                                 "rows": ["Intended use"]})
    assert r.status_code == 200 and r.json()["cells"][0]["supported"] is False
    assert c.post("/compare", json={"subject_description": "x", "predicate_k": "K000000"}).status_code == 404
