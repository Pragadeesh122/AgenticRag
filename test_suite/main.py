"""
CLI entry point for the test suite.

Usage:
    python -m test_suite.main                 # run predefined tests
    python -m test_suite.main --agent         # LLM-generated queries
    python -m test_suite.main --agent -n 5    # generate 5 queries
    python -m test_suite.main --chat          # general conversation test
    python -m test_suite.main --chat -n 8     # 8 turns of conversation
    python -m test_suite.main -k search       # only predefined tests matching "search"
    python -m test_suite.main --list          # list predefined tests
"""

import argparse
import sys

from test_suite import test_predefined, test_agent, test_chat
from test_suite.test_predefined import TEST_CASES
from test_suite.report import print_summary, save_report


def main():
    parser = argparse.ArgumentParser(description="Test the AgenticRag orchestrator")
    parser.add_argument(
        "-k", "--filter", help="Only run predefined tests matching this string"
    )
    parser.add_argument("--list", action="store_true", help="List predefined tests")
    parser.add_argument(
        "--agent", action="store_true", help="Use LLM to generate test queries"
    )
    parser.add_argument(
        "--chat", action="store_true", help="General conversation test (no tools)"
    )
    parser.add_argument(
        "-n", type=int, default=5, help="Number of queries/turns for --agent or --chat"
    )
    args = parser.parse_args()

    if args.list:
        for t in TEST_CASES:
            tool = t.get("expect_tool") or "(no tool)"
            print(f"  {t['name']:30s} expect_tool={tool}")
        return

    if args.chat:
        mode = "chat"
        results = test_chat.run(args.n)
    elif args.agent:
        mode = "agent"
        results = test_agent.run(args.n)
    else:
        mode = "predefined"
        cases = TEST_CASES
        if args.filter:
            cases = [t for t in TEST_CASES if args.filter.lower() in t["name"].lower()]
            if not cases:
                print(f"No tests matched filter '{args.filter}'")
                sys.exit(1)
        results = test_predefined.run(cases)

    print_summary(results)
    save_report(results, mode)
    sys.exit(1 if any(not r["passed"] for r in results) else 0)


if __name__ == "__main__":
    main()
