"""Scoring for the two things that must be right: predicate links and table citations."""


def prf(pred: set, gold: set) -> dict:
    tp = len(pred & gold)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gold) if gold else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": len(pred - gold), "fn": len(gold - pred),
            "precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3)}


def score_predicates(gold: dict[str, list[str]], predicted: dict[str, list[str]]) -> dict:
    """Micro-averaged over devices. gold/predicted map K-number -> predicate K-numbers."""
    pred_pairs = {(k, p) for k, ps in predicted.items() if k in gold for p in ps}
    gold_pairs = {(k, p) for k, ps in gold.items() for p in ps}
    return {"devices": len(gold), **prf(pred_pairs, gold_pairs)}


def score_citations(labeled_cells: list[dict]) -> dict:
    """labeled_cells: table cells a person checked, each with "correct": true/false.
    citation_precision = share of supported cells whose value really matches the cited text."""
    supported = [c for c in labeled_cells if c.get("supported")]
    checked = [c for c in supported if "correct" in c]
    correct = sum(1 for c in checked if c["correct"])
    return {
        "cells": len(labeled_cells),
        "supported": len(supported),
        "not_found": len(labeled_cells) - len(supported),
        "checked": len(checked),
        "citation_precision": round(correct / len(checked), 3) if checked else None,
    }
