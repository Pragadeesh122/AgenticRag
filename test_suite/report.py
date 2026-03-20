"""Report saving and summary printing."""

import json
import os
from datetime import datetime, timezone


def print_summary(results: list[dict]):
    """Print final pass/fail summary."""
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        label = r.get("name", r.get("prompt", "")[:50])
        print(f"  [{status}] {label}")
        if not r["passed"]:
            for issue in r.get("issues", []):
                print(f"         {issue}")
            if r.get("reason"):
                print(f"         {r['reason']}")
    print(f"\n{passed} passed, {failed} failed out of {len(results)} tests")


def save_report(results: list[dict], mode: str) -> str:
    """Save test results as a JSON report for analysis."""
    os.makedirs("test_reports", exist_ok=True)

    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed

    all_tools = []
    all_cache_hits = []
    for r in results:
        all_tools.extend(r.get("tools_used", []))
        all_cache_hits.extend(r.get("cache_hits", []))

    tool_counts = {}
    for t in all_tools:
        tool_counts[t] = tool_counts.get(t, 0) + 1

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / len(results) * 100, 1) if results else 0,
        },
        "tool_usage": {
            "total_calls": len(all_tools),
            "by_tool": tool_counts,
        },
        "cache": {
            "hits": len(all_cache_hits),
            "hit_tools": all_cache_hits,
        },
        "results": results,
    }

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"test_reports/{mode}_{ts}.json"
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nReport saved: {filepath}")
    return filepath
