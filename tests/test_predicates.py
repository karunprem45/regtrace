from regtrace import predicates
from tests.fixtures import SUMMARY_PAGES, FakeLLM


def test_regex_finds_other_k_numbers_not_self():
    found = predicates.regex_predicates("K240001", SUMMARY_PAGES)
    assert [p["k_number"] for p in found] == ["K201234", "K199876"]
    assert all(p["page"] == 2 for p in found)


def test_llm_answers_are_checked_against_page_text():
    llm = FakeLLM({"predicates": [
        {"k_number": "K201234", "page": 2, "quote": "Example Oximeter cleared under K201234"},
        {"k_number": "K555555", "page": 2, "quote": "cleared under K555555"},          # invented
        {"k_number": "K199876", "page": 3, "quote": "A reference device, K199876"},    # wrong page
        {"k_number": "K240001", "page": 1, "quote": "510(k) Summary K240001"},         # itself
        {"k_number": "K20", "page": 2, "quote": "x"},                                  # malformed
    ]})
    ok, bad = predicates.llm_predicates("K240001", SUMMARY_PAGES, llm)
    assert [p["k_number"] for p in ok] == ["K201234"]
    assert sorted(b["reason"] for b in bad) == [
        "bad_k_number", "quote_not_on_page", "quote_not_on_page", "self_reference"]
    assert "--- PAGE 2 ---" in llm.calls[0][1]
