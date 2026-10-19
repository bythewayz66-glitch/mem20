"""5000QA harness: scoring and refusal-detection tests.

The harness must never report a score it did not measure, and it must be able
to tell "the server answered" from "the server reported absence" - a memory
system that answers every question is not accurate, it is agreeable.
"""
import importlib.util
import os

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_QA = os.path.join(os.path.dirname(_HERE), "bench", "qa5000", "qa5000.py")

spec = importlib.util.spec_from_file_location("qa5000", _QA)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


# --- token F1 -------------------------------------------------------------

def test_f1_identical_is_one():
    assert qa.token_f1("the ledger is append-only", "the ledger is append-only") == 1.0


def test_f1_disjoint_is_zero():
    assert qa.token_f1("alpha beta", "gamma delta") == 0.0


def test_f1_partial_is_between():
    v = qa.token_f1("the ledger is append-only jsonl", "the ledger is append-only")
    assert 0.0 < v < 1.0


def test_f1_empty_both_is_one():
    assert qa.token_f1("", "") == 1.0


def test_f1_one_empty_is_zero():
    assert qa.token_f1("something", "") == 0.0


def test_f1_is_case_and_punctuation_insensitive():
    assert qa.token_f1("The Ledger, append-only!", "the ledger append only") == 1.0


# --- exact match ----------------------------------------------------------

def test_exact_match_normalises():
    assert qa.exact_match("The  Ledger!", "the ledger") == 1.0


def test_exact_match_rejects_extra_words():
    assert qa.exact_match("the ledger is here", "the ledger") == 0.0


# --- refusal detection ----------------------------------------------------

def test_empty_results_is_a_refusal():
    assert qa._looks_like_refusal({"results": []}) is True


def test_found_false_is_a_refusal():
    assert qa._looks_like_refusal({"found": False}) is True


def test_populated_results_is_not_a_refusal():
    assert qa._looks_like_refusal({"results": [{"id": "x", "content": "y"}]}) is False


def test_no_results_phrase_is_a_refusal():
    assert qa._looks_like_refusal({"_raw": "No results found for that query"}) is True


def test_non_dict_is_not_a_refusal():
    assert qa._looks_like_refusal("plain text") is False


# --- answer / id extraction ----------------------------------------------

def test_extract_answer_prefers_answer_field():
    assert qa._extract_answer({"answer": "42", "content": "other"}) == "42"


def test_extract_answer_falls_back_to_first_result():
    assert qa._extract_answer({"results": [{"content": "hit"}]}) == "hit"


def test_extract_ids_collects_result_ids():
    got = qa._extract_ids({"results": [{"id": "a"}, {"id": "b"}]})
    assert got == {"a", "b"}


def test_extract_ids_empty_when_no_results():
    assert qa._extract_ids({"results": []}) == set()


# --- aggregation ----------------------------------------------------------

def _row(cat="factual_recall", f1=1.0, correct=True, refusal_ok=True,
         ev=None, diff="easy"):
    return {"id": "q", "category": cat, "difficulty": diff, "f1": f1,
            "em": 0.0, "refused": False, "refusal_ok": refusal_ok,
            "evidence_hit": ev, "correct": correct, "latency_ms": 1.0,
            "error": None}


def test_agg_accuracy_is_fraction_correct():
    a = qa._agg([_row(correct=True), _row(correct=False)])
    assert a["n"] == 2
    assert a["accuracy"] == 0.5


def test_agg_evidence_hit_ignores_none():
    a = qa._agg([_row(ev=1.0), _row(ev=None)])
    assert a["evidence_hit"] == 1.0


def test_agg_empty_is_safe():
    assert qa._agg([])["n"] == 0


def test_categories_are_the_documented_six():
    assert qa.CATEGORIES == [
        "factual_recall", "temporal_recall", "partition_integrity",
        "epistemic_provenance", "multi_hop", "negative_control",
    ]


# --- the results template must not contain a score ------------------------

def test_results_template_ships_empty():
    """The template must not carry a fabricated number."""
    path = os.path.join(os.path.dirname(_HERE), "bench", "qa5000",
                        "results.template.md")
    with open(path) as fh:
        body = fh.read()
    assert "NOT RUN" in body
    assert "*(not run)*" in body
    # No percentage or decimal score may appear in the template.
    import re
    assert not re.search(r"\b\d+\.\d+%", body), "template contains a score"
    assert not re.search(r"\|\s*\d+\.\d+\s*\|", body), "template contains a score"
