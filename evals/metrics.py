"""Pure retrieval evaluation metrics: Recall@k, MRR, NDCG@k."""

from __future__ import annotations

import math


def recall_at_k(
    retrieved_filenames: list[str],
    expected_filenames: set[str],
    k: int,
) -> float:
    """Fraction of expected documents found in the top-k retrieved results.

    Returns 0.0 if expected_filenames is empty.
    """
    if not expected_filenames:
        return 0.0
    top_k = retrieved_filenames[:k]
    hits = sum(1 for f in top_k if f in expected_filenames)
    return hits / len(expected_filenames)


def mrr(
    retrieved_filenames: list[str],
    expected_filenames: set[str],
) -> float:
    """Mean Reciprocal Rank — 1/rank of the first relevant result.

    Returns 0.0 if no relevant result is found.
    """
    for i, filename in enumerate(retrieved_filenames):
        if filename in expected_filenames:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(
    retrieved_filenames: list[str],
    expected_filenames: set[str],
    k: int,
) -> float:
    """Normalized Discounted Cumulative Gain at k.

    Binary relevance: 1 if filename is expected, 0 otherwise.
    Returns 0.0 if expected_filenames is empty or k is 0.
    """
    if not expected_filenames or k == 0:
        return 0.0

    top_k = retrieved_filenames[:k]

    # DCG: sum of 1/log2(rank+1) for relevant docs
    dcg = 0.0
    for i, filename in enumerate(top_k):
        if filename in expected_filenames:
            dcg += 1.0 / math.log2(i + 2)  # i+2 because rank is 1-indexed

    # Ideal DCG: all relevant docs ranked at the top
    ideal_relevant = min(len(expected_filenames), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_relevant))

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def substring_recall(
    retrieved_texts: list[str],
    expected_substrings: list[str],
) -> float:
    """Fraction of expected_substrings found in any retrieved chunk text.

    Case-insensitive matching. Returns 0.0 if expected_substrings is empty.
    """
    if not expected_substrings:
        return 0.0
    joined = "\n".join(retrieved_texts).lower()
    hits = sum(1 for sub in expected_substrings if sub.lower() in joined)
    return hits / len(expected_substrings)
