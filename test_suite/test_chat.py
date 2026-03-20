"""General conversation test — no specialized tools should fire."""

from clients import openai_client
from prompts import CHAT_AGENT
from test_suite.orchestrator import start_orchestrator, stop_orchestrator, send_prompt


def run(n: int = 5) -> list[dict]:
    """Have an LLM agent hold a general conversation with the orchestrator."""
    proc, stderr_logs = start_orchestrator()
    results = []

    chat_agent_messages = [
        {
            "role": "system",
            "content": CHAT_AGENT,
        }
    ]

    for i in range(n):
        chat_response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=chat_agent_messages,
        )
        prompt = chat_response.choices[0].message.content.strip()
        chat_agent_messages.append({"role": "assistant", "content": prompt})

        print(f"\n{'=' * 60}")
        print(f"TURN {i + 1}/{n}")
        print(f"USER: {prompt}")
        print(f"{'=' * 60}")

        result = send_prompt(proc, stderr_logs, prompt)
        print(f"TOOLS USED: {result['tools_used'] or '(none)'}")
        cache_status = result["cache_hits"] if result["cache_hits"] else "miss"
        print(f"CACHE: {cache_status}")
        print(f"ASSISTANT: {result['response'][:300]}")

        if result["error"]:
            print(f"ERROR: {result['error']}")
            results.append(
                {"prompt": prompt, "passed": False, "reason": result["error"]}
            )
            continue

        chat_agent_messages.append({"role": "user", "content": result["response"]})

        issues = []
        if result["tools_used"]:
            issues.append(
                f"Unexpected tool calls for general chat: {result['tools_used']}"
            )
        if not result["response"].strip():
            issues.append("Empty response")

        passed = len(issues) == 0
        print(f"RESULT: {'PASS' if passed else 'FAIL'}")
        for issue in issues:
            print(f"  - {issue}")

        results.append({
            "prompt": prompt,
            "passed": passed,
            "issues": issues,
            "tools_used": result.get("tools_used", []),
            "cache_hits": result.get("cache_hits", []),
            "response": result["response"],
        })

    stop_orchestrator(proc)
    return results
