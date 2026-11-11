"""Find predicate devices in a 510(k) summary.

Two methods run side by side:
  * regex: every K-number on the page, minus the device's own number
  * llm:   Claude reads the pages and says which K-numbers are predicates, with a quote

An LLM answer is kept only if its K-number is well formed and its quote really appears
on the page it cites. That check is what makes each predicate link traceable.
"""
import re

K_ANY = re.compile(r"\bK\s?(\d{6})\b")

SYSTEM = (
    "You read FDA 510(k) summaries. Return JSON only: "
    '{"predicates": [{"k_number": "K123456", "page": 1, "quote": "exact text from that page"}]}. '
    "List only devices named as predicate or reference devices for substantial equivalence. "
    "The quote must be copied exactly from the page and contain the K-number."
)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def regex_predicates(k_number: str, pages: list[str]) -> list[dict]:
    found, out = set(), []
    for i, text in enumerate(pages, start=1):
        for m in K_ANY.finditer(text):
            k = "K" + m.group(1)
            if k != k_number and k not in found:
                found.add(k)
                out.append({"k_number": k, "page": i})
    return out


def llm_predicates(k_number: str, pages: list[str], llm) -> tuple[list[dict], list[dict]]:
    """Returns (accepted, rejected). Rejected items carry a reason for the run report."""
    numbered = "\n\n".join(f"--- PAGE {i} ---\n{t}" for i, t in enumerate(pages, start=1))
    data = llm.complete_json(SYSTEM, f"Device under review: {k_number}\n\n{numbered}")
    accepted, rejected, seen = [], [], set()
    for item in data.get("predicates", []):
        k = str(item.get("k_number", "")).replace(" ", "").upper()
        page, quote = item.get("page"), item.get("quote", "")
        reason = None
        if not re.fullmatch(r"K\d{6}", k):
            reason = "bad_k_number"
        elif k == k_number:
            reason = "self_reference"
        elif not isinstance(page, int) or not 1 <= page <= len(pages):
            reason = "bad_page"
        elif _norm(quote) not in _norm(pages[page - 1]):
            reason = "quote_not_on_page"
        elif k[1:] not in quote.replace(" ", ""):
            reason = "quote_missing_k_number"
        elif k in seen:
            reason = "duplicate"
        if reason:
            rejected.append({**item, "reason": reason})
        else:
            seen.add(k)
            accepted.append({"k_number": k, "page": page, "quote": quote})
    return accepted, rejected


def save(db, k_number: str, preds: list[dict], method: str) -> None:
    q = ("INSERT INTO predicates (k_number, predicate_k, page, method) VALUES (?, ?, ?, ?) "
         "ON CONFLICT (k_number, predicate_k, method) DO UPDATE SET page = excluded.page")
    db.executemany(q, [(k_number, p["k_number"], p["page"], method) for p in preds])
    db.commit()
