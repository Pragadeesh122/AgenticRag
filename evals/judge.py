"""LLM-as-judge wrapper for RAG answer evaluation."""

from __future__ import annotations

import json
import logging

from evals.rubric import JUDGE_SYSTEM_PROMPT, build_judge_prompt

logger = logging.getLogger("evals.judge")

EXPECTED_DIMENSIONS = {"faithfulness", "completeness", "hallucination", "format_adherence"}


def _parse_judge_response(text: str) -> dict | None:
    """Try to parse the judge's JSON response, with code-fence fallback."""
    text = text.strip()

    # Try raw JSON
    try:
        parsed = json.loads(text)
        if EXPECTED_DIMENSIONS <= set(parsed):
            return parsed
    except json.JSONDecodeError:
        pass

    # Try extracting from code fence
    for marker in ("```json", "```"):
        if marker in text:
            start = text.index(marker) + len(marker)
            end = text.index("```", start) if "```" in text[start:] else len(text)
            try:
                parsed = json.loads(text[start:end].strip())
                if EXPECTED_DIMENSIONS <= set(parsed):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass

    # Try brace-matching
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        try:
            parsed = json.loads(text[brace_start : brace_end + 1])
            if EXPECTED_DIMENSIONS <= set(parsed):
                return parsed
        except json.JSONDecodeError:
            pass

    return None


def judge_answer(
    query: str,
    answer: str,
    retrieved_chunks: list[str],
    expected_traits: dict,
    llm_client,
    model: str = "gpt-4o-mini",
    max_retries: int = 1,
) -> dict:
    """Run the LLM judge and return structured scores.

    Returns dict with keys: faithfulness, completeness, hallucination, format_adherence.
    Each value is {"score": int, "reason": str}.
    Falls back to all-zeros with error reason on failure.
    """
    user_prompt = build_judge_prompt(query, answer, retrieved_chunks, expected_traits)

    for attempt in range(1 + max_retries):
        try:
            response = llm_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
            text = response.choices[0].message.content or ""
            parsed = _parse_judge_response(text)
            if parsed is not None:
                return parsed
            logger.warning(f"judge attempt {attempt + 1}: malformed JSON, retrying")
        except Exception as e:
            logger.error(f"judge attempt {attempt + 1} failed: {e}")

    # Fallback: zero scores
    logger.error("judge failed after all retries, returning zero scores")
    return {
        dim: {"score": 0, "reason": "judge_failed"}
        for dim in EXPECTED_DIMENSIONS
    }
