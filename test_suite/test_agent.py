"""LLM-generated test queries with an LLM judge."""

import json

from clients import openai_client
from prompts import QUERY_GENERATOR, JUDGE
from test_suite.orchestrator import start_orchestrator, stop_orchestrator, send_prompt


def generate_test_queries(n: int = 5) -> list[str]:
    """Ask an LLM to generate diverse test queries for our agent."""
    response = openai_client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {
                "role": "system",
                "content": QUERY_GENERATOR,
            },
            {
                "role": "user",
                "content": f"Generate {n} test queries as JSON.",
            },
        ],
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(response.choices[0].message.content)
        queries = (
            data
            if isinstance(data, list)
            else data.get("queries", data.get("tests", []))
        )
        return queries
    except (json.JSONDecodeError, AttributeError):
        print("Failed to parse LLM-generated queries")
        return []


def judge_response(prompt: str, tools_used: list[str], actual_response: str) -> dict:
    """Use an LLM to judge whether the agent chose the right tool and responded well."""
    tools_str = ", ".join(tools_used) if tools_used else "(none)"
    response = openai_client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {
                "role": "system",
                "content": JUDGE,
            },
            {
                "role": "user",
                "content": (
                    f"PROMPT: {prompt}\n\n"
                    f"TOOLS CALLED: {tools_str}\n\n"
                    f"RESPONSE: {actual_response}"
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"passed": False, "reason": "Failed to parse judge response"}


def run(n: int = 5) -> list[dict]:
    """Generate queries with an LLM, run them, and judge the responses."""
    print("Generating test queries with LLM...")
    queries = generate_test_queries(n)
    if not queries:
        print("No queries generated.")
        return []

    print(f"Generated {len(queries)} test queries\n")

    proc, stderr_logs = start_orchestrator()
    results = []

    for i, prompt in enumerate(queries):
        print(f"\n{'=' * 60}")
        print(f"TEST {i + 1}/{len(queries)}")
        print(f"PROMPT: {prompt}")
        print(f"{'=' * 60}")

        result = send_prompt(proc, stderr_logs, prompt, timeout=300)
        print(f"TOOLS USED: {result['tools_used'] or '(none)'}")
        cache_status = result["cache_hits"] if result["cache_hits"] else "miss"
        print(f"CACHE: {cache_status}")
        print(f"RESPONSE: {result['response'][:300]}")

        if result["error"]:
            print(f"ERROR: {result['error']}")
            results.append(
                {"prompt": prompt, "passed": False, "reason": result["error"]}
            )
            continue

        verdict = judge_response(prompt, result["tools_used"], result["response"])
        passed = verdict.get("passed", False)
        reason = verdict.get("reason", "")
        tool_ok = verdict.get("tool_correct", "?")
        quality = verdict.get("response_quality", "?")
        print(
            f"JUDGE: {'PASS' if passed else 'FAIL'} | tool_correct={tool_ok} | quality={quality}"
        )
        print(f"  {reason}")
        results.append(
            {
                "prompt": prompt,
                "passed": passed,
                "reason": reason,
                "tools_used": result.get("tools_used", []),
                "cache_hits": result.get("cache_hits", []),
                "response": result["response"],
                "judge": verdict,
            }
        )

    stop_orchestrator(proc)
    return results
