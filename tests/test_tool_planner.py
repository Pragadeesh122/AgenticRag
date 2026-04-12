"""Focused unit tests for utils/tool_planner.py — tool execution planning logic."""

import json

from functions import tool_policies
from utils.tool_planner import (
    plan_tool_calls,
    tool_call_fingerprint,
    ToolPolicy,
)


def _tool_call(name: str, args: dict, call_id: str) -> dict:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(args),
        },
    }


# --- Tests moved from test_chat_orchestration.py ---


def test_plan_runs_distinct_search_calls_in_parallel():
    tool_calls = [
        _tool_call("search", {"query": "openai pricing"}, "search-1"),
        _tool_call("search", {"query": "anthropic pricing"}, "search-2"),
    ]

    plan = plan_tool_calls(
        tool_calls,
        tool_policies=tool_policies,
        last_evidence_by_fingerprint={},
        current_evidence_version=0,
        max_parallel_calls_per_step=3,
    )

    assert plan.mode == "parallel"
    assert [call.tool_name for call in plan.selected_calls] == ["search", "search"]
    assert plan.reason == "parallel_safe_batch"
    assert plan.suppressed_calls == ()


def test_plan_mixed_batch_falls_back_to_first_call_only():
    tool_calls = [
        _tool_call("crawl_website", {"url": "https://example.com"}, "crawl-1"),
        _tool_call("search", {"query": "example company"}, "search-1"),
    ]

    plan = plan_tool_calls(
        tool_calls,
        tool_policies=tool_policies,
        last_evidence_by_fingerprint={},
        current_evidence_version=0,
        max_parallel_calls_per_step=3,
    )

    assert plan.mode == "sequential"
    assert [call.tool_name for call in plan.selected_calls] == ["crawl_website"]
    assert len(plan.suppressed_calls) == 1
    assert plan.reason == "mixed_batch_requires_sequence"


def test_plan_multiple_query_db_calls_run_sequential():
    tool_calls = [
        _tool_call("query_db", {"question": "top customers"}, "db-1"),
        _tool_call("query_db", {"question": "recent orders"}, "db-2"),
    ]

    plan = plan_tool_calls(
        tool_calls,
        tool_policies=tool_policies,
        last_evidence_by_fingerprint={},
        current_evidence_version=0,
        max_parallel_calls_per_step=3,
    )

    assert plan.mode == "sequential"
    assert [call.tool_name for call in plan.selected_calls] == ["query_db"]
    assert len(plan.suppressed_calls) == 1
    assert plan.reason == "sequential_mode_deferred"


def test_plan_suppresses_duplicate_without_new_evidence():
    tool_call = _tool_call("query_db", {"question": "top customers"}, "db-1")

    first_plan = plan_tool_calls(
        [tool_call],
        tool_policies=tool_policies,
        last_evidence_by_fingerprint={},
        current_evidence_version=0,
        max_parallel_calls_per_step=3,
    )
    fingerprint = first_plan.selected_calls[0].fingerprint

    second_plan = plan_tool_calls(
        [tool_call],
        tool_policies=tool_policies,
        last_evidence_by_fingerprint={fingerprint: 1},
        current_evidence_version=1,
        max_parallel_calls_per_step=3,
    )

    assert second_plan.selected_calls == ()
    assert len(second_plan.suppressed_calls) == 1
    assert second_plan.suppressed_calls[0].reason == "duplicate_without_new_evidence"
    assert second_plan.reason == "all_calls_suppressed"


def test_plan_truncates_parallel_search_fanout_to_cap():
    tool_calls = [
        _tool_call("search", {"query": "q1"}, "search-1"),
        _tool_call("search", {"query": "q2"}, "search-2"),
        _tool_call("search", {"query": "q3"}, "search-3"),
        _tool_call("search", {"query": "q4"}, "search-4"),
    ]

    plan = plan_tool_calls(
        tool_calls,
        tool_policies=tool_policies,
        last_evidence_by_fingerprint={},
        current_evidence_version=0,
        max_parallel_calls_per_step=3,
    )

    assert plan.mode == "parallel"
    assert len(plan.selected_calls) == 3
    assert len(plan.suppressed_calls) == 1
    assert plan.suppressed_calls[0].reason == "parallel_cap_exceeded"
    assert plan.reason == "parallel_truncated"


# --- New tests ---


def test_plan_fingerprint_stable_across_arg_order():
    """Same tool + same args in different JSON key order -> same fingerprint."""
    policy = ToolPolicy()  # default, no dedupe_key_fields

    fp1 = tool_call_fingerprint("search", {"query": "test", "limit": 5}, policy)
    fp2 = tool_call_fingerprint("search", {"limit": 5, "query": "test"}, policy)
    assert fp1 == fp2


def test_plan_fingerprint_differs_for_different_args():
    policy = ToolPolicy()
    fp1 = tool_call_fingerprint("search", {"query": "alpha"}, policy)
    fp2 = tool_call_fingerprint("search", {"query": "beta"}, policy)
    assert fp1 != fp2


def test_plan_fingerprint_uses_dedupe_key_fields():
    """When dedupe_key_fields is set, only those fields matter for fingerprint."""
    policy = ToolPolicy(dedupe_key_fields=("query",))
    fp1 = tool_call_fingerprint("search", {"query": "test", "limit": 5}, policy)
    fp2 = tool_call_fingerprint("search", {"query": "test", "limit": 10}, policy)
    assert fp1 == fp2


def test_plan_respects_requires_fresh_input_policy():
    """Tool with requires_fresh_input=True blocks parallel execution."""
    fresh_policy = ToolPolicy(
        execution_mode="parallel_safe",
        requires_fresh_input=True,
        max_parallel_instances=5,
    )
    custom_policies = {"my_tool": fresh_policy}

    tool_calls = [
        _tool_call("my_tool", {"q": "a"}, "t-1"),
        _tool_call("my_tool", {"q": "b"}, "t-2"),
    ]

    plan = plan_tool_calls(
        tool_calls,
        tool_policies=custom_policies,
        last_evidence_by_fingerprint={},
        current_evidence_version=0,
        max_parallel_calls_per_step=5,
    )

    # requires_fresh_input=True means parallel_eligible is False
    assert plan.mode == "sequential"
    assert len(plan.selected_calls) == 1


def test_plan_verification_only_after_result_blocks_parallel():
    """verification_only_after_result doesn't affect parallel eligibility directly,
    but sequential_first execution_mode does."""
    verify_policy = ToolPolicy(
        execution_mode="sequential_first",
        verification_only_after_result=True,
    )
    custom_policies = {"verify_tool": verify_policy}

    tool_calls = [
        _tool_call("verify_tool", {"data": "x"}, "v-1"),
        _tool_call("verify_tool", {"data": "y"}, "v-2"),
    ]

    plan = plan_tool_calls(
        tool_calls,
        tool_policies=custom_policies,
        last_evidence_by_fingerprint={},
        current_evidence_version=0,
        max_parallel_calls_per_step=5,
    )

    assert plan.mode == "sequential"
    assert len(plan.selected_calls) == 1


def test_plan_empty_tool_calls():
    plan = plan_tool_calls(
        [],
        tool_policies=tool_policies,
        last_evidence_by_fingerprint={},
        current_evidence_version=0,
        max_parallel_calls_per_step=3,
    )
    assert plan.mode == "sequential"
    assert plan.selected_calls == ()
    assert plan.reason == "no_tool_calls"
    assert plan.requested_count == 0


def test_plan_duplicate_in_same_batch_suppressed():
    """Exact same tool call appearing twice in one batch — second is suppressed."""
    tool_calls = [
        _tool_call("search", {"query": "same"}, "search-1"),
        _tool_call("search", {"query": "same"}, "search-2"),
    ]

    plan = plan_tool_calls(
        tool_calls,
        tool_policies=tool_policies,
        last_evidence_by_fingerprint={},
        current_evidence_version=0,
        max_parallel_calls_per_step=3,
    )

    assert len(plan.selected_calls) == 1
    assert len(plan.suppressed_calls) == 1
    assert plan.suppressed_calls[0].reason == "duplicate_in_batch"


def test_plan_single_call_reason():
    tool_calls = [_tool_call("query_db", {"question": "count"}, "db-1")]

    plan = plan_tool_calls(
        tool_calls,
        tool_policies=tool_policies,
        last_evidence_by_fingerprint={},
        current_evidence_version=0,
        max_parallel_calls_per_step=3,
    )

    assert plan.mode == "sequential"
    assert len(plan.selected_calls) == 1
    assert plan.reason == "single_call"
