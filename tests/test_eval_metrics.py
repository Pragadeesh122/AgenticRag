"""Unit tests for evals/metrics.py — pure metric functions."""

import math

from evals.metrics import recall_at_k, mrr, ndcg_at_k, substring_recall


# --- recall_at_k ---

def test_recall_at_k_perfect():
    retrieved = ["a.pdf", "b.pdf", "c.pdf"]
    expected = {"a.pdf", "b.pdf"}
    assert recall_at_k(retrieved, expected, k=3) == 1.0


def test_recall_at_k_partial():
    retrieved = ["a.pdf", "c.pdf", "d.pdf"]
    expected = {"a.pdf", "b.pdf"}
    assert recall_at_k(retrieved, expected, k=3) == 0.5


def test_recall_at_k_none_found():
    retrieved = ["x.pdf", "y.pdf"]
    expected = {"a.pdf"}
    assert recall_at_k(retrieved, expected, k=2) == 0.0


def test_recall_at_k_truncates_to_k():
    retrieved = ["x.pdf", "y.pdf", "a.pdf"]
    expected = {"a.pdf"}
    # k=2, so a.pdf at position 3 is not considered
    assert recall_at_k(retrieved, expected, k=2) == 0.0


def test_recall_at_k_empty_expected():
    assert recall_at_k(["a.pdf"], set(), k=5) == 0.0


def test_recall_at_k_empty_retrieved():
    assert recall_at_k([], {"a.pdf"}, k=5) == 0.0


# --- mrr ---

def test_mrr_first_position():
    assert mrr(["a.pdf", "b.pdf"], {"a.pdf"}) == 1.0


def test_mrr_second_position():
    assert mrr(["x.pdf", "a.pdf", "b.pdf"], {"a.pdf"}) == 0.5


def test_mrr_not_found():
    assert mrr(["x.pdf", "y.pdf"], {"a.pdf"}) == 0.0


def test_mrr_multiple_expected_returns_first_hit():
    # First relevant hit is at position 2 (0-indexed=1)
    assert mrr(["x.pdf", "b.pdf", "a.pdf"], {"a.pdf", "b.pdf"}) == 0.5


def test_mrr_empty_retrieved():
    assert mrr([], {"a.pdf"}) == 0.0


# --- ndcg_at_k ---

def test_ndcg_perfect_single():
    # Single expected doc at rank 1
    assert ndcg_at_k(["a.pdf"], {"a.pdf"}, k=5) == 1.0


def test_ndcg_perfect_multiple():
    # All expected at top positions
    retrieved = ["a.pdf", "b.pdf", "c.pdf"]
    expected = {"a.pdf", "b.pdf"}
    assert abs(ndcg_at_k(retrieved, expected, k=3) - 1.0) < 1e-9


def test_ndcg_imperfect_ordering():
    # Expected at position 2, not position 1
    retrieved = ["x.pdf", "a.pdf", "y.pdf"]
    expected = {"a.pdf"}
    # DCG = 1/log2(3) = 0.6309...
    # IDCG = 1/log2(2) = 1.0
    expected_ndcg = (1.0 / math.log2(3)) / (1.0 / math.log2(2))
    assert abs(ndcg_at_k(retrieved, expected, k=3) - expected_ndcg) < 1e-9


def test_ndcg_no_relevant():
    assert ndcg_at_k(["x.pdf", "y.pdf"], {"a.pdf"}, k=2) == 0.0


def test_ndcg_empty_expected():
    assert ndcg_at_k(["a.pdf"], set(), k=5) == 0.0


def test_ndcg_k_zero():
    assert ndcg_at_k(["a.pdf"], {"a.pdf"}, k=0) == 0.0


# --- substring_recall ---

def test_substring_recall_all_found():
    texts = ["The warranty is 24 months for the XR-7 controller."]
    expected = ["warranty", "24 months"]
    assert substring_recall(texts, expected) == 1.0


def test_substring_recall_partial():
    texts = ["The warranty covers defects."]
    expected = ["warranty", "24 months"]
    assert substring_recall(texts, expected) == 0.5


def test_substring_recall_none_found():
    texts = ["Unrelated text about something else."]
    expected = ["warranty", "24 months"]
    assert substring_recall(texts, expected) == 0.0


def test_substring_recall_case_insensitive():
    texts = ["WARRANTY PERIOD is 24 MONTHS"]
    expected = ["warranty", "24 months"]
    assert substring_recall(texts, expected) == 1.0


def test_substring_recall_across_chunks():
    texts = ["chunk one has warranty info", "chunk two mentions 24 months"]
    expected = ["warranty", "24 months"]
    assert substring_recall(texts, expected) == 1.0


def test_substring_recall_empty_expected():
    assert substring_recall(["some text"], []) == 0.0


def test_substring_recall_empty_texts():
    assert substring_recall([], ["warranty"]) == 0.0
