from regtrace.evaluate import score_citations, score_predicates


def test_predicate_scores():
    gold = {"K1": ["KA", "KB"], "K2": ["KC"]}
    pred = {"K1": ["KA", "KX"], "K2": ["KC"], "K9": ["KZ"]}   # K9 not in gold, ignored
    s = score_predicates(gold, pred)
    assert (s["tp"], s["fp"], s["fn"]) == (2, 1, 1)
    assert s["precision"] == 0.667 and s["recall"] == 0.667


def test_citation_precision_counts_only_checked_supported_cells():
    cells = [{"supported": True, "correct": True}, {"supported": True, "correct": False},
             {"supported": True}, {"supported": False}]
    s = score_citations(cells)
    assert s == {"cells": 4, "supported": 3, "not_found": 1, "checked": 2,
                 "citation_precision": 0.5}
