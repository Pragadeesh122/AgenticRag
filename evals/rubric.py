"""Judge rubric and prompt template for LLM-as-judge evaluation."""

RUBRIC_DIMENSIONS = {
    "faithfulness": "Every factual claim in the answer is grounded in the retrieved chunks.",
    "completeness": "The answer covers all must_mention items from the expected traits.",
    "hallucination": "The answer is free of must_not_mention items and unsupported claims.",
    "format_adherence": "The answer matches the expected format (prose, JSON, list, etc.).",
}

JUDGE_SYSTEM_PROMPT = """\
You are an expert evaluator for a RAG (Retrieval-Augmented Generation) system.
You will be given a user query, the system's answer, retrieved context chunks,
and expected answer traits. Score the answer on each dimension using a 1-5 scale.

Scoring guide:
  5 = Excellent — fully meets the criterion
  4 = Good — minor gaps
  3 = Acceptable — noticeable gaps but core info present
  2 = Poor — significant issues
  1 = Very poor — fails the criterion

You MUST respond with valid JSON only, no other text. Use this exact schema:
{
  "faithfulness": {"score": <1-5>, "reason": "<short justification>"},
  "completeness": {"score": <1-5>, "reason": "<short justification>"},
  "hallucination": {"score": <1-5>, "reason": "<short justification>"},
  "format_adherence": {"score": <1-5>, "reason": "<short justification>"}
}
"""


def build_judge_prompt(
    query: str,
    answer: str,
    retrieved_chunks: list[str],
    expected_traits: dict,
) -> str:
    chunks_text = "\n---\n".join(retrieved_chunks) if retrieved_chunks else "(no chunks retrieved)"
    must_mention = ", ".join(expected_traits.get("must_mention", [])) or "(none)"
    must_not_mention = ", ".join(expected_traits.get("must_not_mention", [])) or "(none)"
    fmt = expected_traits.get("format", "prose")

    return f"""\
## User Query
{query}

## System Answer
{answer}

## Retrieved Context Chunks
{chunks_text}

## Expected Answer Traits
- Must mention: {must_mention}
- Must NOT mention: {must_not_mention}
- Expected format: {fmt}

Score the answer on faithfulness, completeness, hallucination, and format_adherence.
Respond with JSON only."""
