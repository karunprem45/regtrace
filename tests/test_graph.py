from regtrace import graph
from tests.fixtures import FakeSession


def test_devices_loaded_in_batches_with_merge():
    s = FakeSession()
    rows = [{"k_number": f"K24{i:04d}"} for i in range(1200)]
    graph.load_devices(s, rows, batch=500)
    assert [len(c[1]["rows"]) for c in s.calls] == [500, 500, 200]
    assert "MERGE (d:Device" in s.calls[0][0] and "CREATE" not in s.calls[0][0]


def test_predicate_edges_and_empty_skip():
    s = FakeSession()
    graph.load_predicates(s, "K240001", [{"k_number": "K201234", "page": 2}], "llm")
    graph.load_predicates(s, "K240002", [], "llm")
    assert len(s.calls) == 1
    assert s.calls[0][1]["rows"][0] == {"k_number": "K240001", "predicate_k": "K201234",
                                        "page": 2, "method": "llm"}


def test_lineage_depth_is_bounded():
    s = FakeSession(result=[{"chain": ["K240001", "K201234"]}])
    assert graph.lineage(s, "K240001", depth=99) == [["K240001", "K201234"]]
    assert "*1..5" in s.calls[0][0]
