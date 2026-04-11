import json
import time

from api import chat as chat_module
from functions import tool_policies
from utils.tool_planner import plan_tool_calls


def _tool_call(name: str, args: dict, call_id: str) -> dict:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(args),
        },
    }


def _response_generator(*, content="", tool_calls=None, usage=None):
    def _gen():
        if content:
            yield content
        return content, tool_calls, usage

    return _gen()


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


def test_chat_stream_executes_only_first_tool_in_sequential_mode(monkeypatch):
    responses = [
        {
            "tool_calls": [
                _tool_call("crawl_website", {"url": "https://example.com"}, "crawl-1"),
                _tool_call("search", {"query": "example company"}, "search-1"),
            ]
        },
        {"content": "Final answer from crawl."},
    ]
    response_index = {"value": 0}
    executed = []
    saved = {}

    def fake_iter_response(messages, use_tools=True):
        current = responses[response_index["value"]]
        response_index["value"] += 1
        return _response_generator(**current)

    def fake_execute_tool_call(proxy):
        executed.append(proxy.function.name)
        return {
            "role": "tool",
            "tool_call_id": proxy.id,
            "content": json.dumps({"content": f"result for {proxy.function.name}"}),
        }

    monkeypatch.setattr(chat_module, "iter_response", fake_iter_response)
    monkeypatch.setattr(chat_module, "execute_tool_call", fake_execute_tool_call)
    monkeypatch.setattr(chat_module, "get_messages", lambda *_: [])
    monkeypatch.setattr(chat_module, "get_session_user", lambda *_: "user-1")
    monkeypatch.setattr(chat_module, "save_messages", lambda session_id, messages: saved.setdefault("messages", messages))
    monkeypatch.setattr(chat_module, "schedule_memory_persistence", lambda *args, **kwargs: None)

    events = list(chat_module.chat_stream("session-1", "check example"))

    assert executed == ["crawl_website"]
    assert sum(1 for event in events if event.startswith("event: tool")) == 1
    assert '"name": "crawl_website"' in "".join(events)
    assert '"name": "search"' not in "".join(events)
    assert saved["messages"][1]["tool_calls"][0]["function"]["name"] == "crawl_website"
    assert saved["messages"][-1]["content"] == "Final answer from crawl."


def test_chat_stream_parallel_search_keeps_tool_results_in_request_order(monkeypatch):
    responses = [
        {
            "tool_calls": [
                _tool_call("search", {"query": "slow"}, "search-1"),
                _tool_call("search", {"query": "fast"}, "search-2"),
            ]
        },
        {"content": "Final answer from search."},
    ]
    response_index = {"value": 0}
    saved = {}

    def fake_iter_response(messages, use_tools=True):
        current = responses[response_index["value"]]
        response_index["value"] += 1
        return _response_generator(**current)

    def fake_execute_tool_call(proxy):
        if proxy.function.arguments == json.dumps({"query": "slow"}):
            time.sleep(0.02)
        return {
            "role": "tool",
            "tool_call_id": proxy.id,
            "content": json.dumps({"result": proxy.function.arguments}),
        }

    monkeypatch.setattr(chat_module, "iter_response", fake_iter_response)
    monkeypatch.setattr(chat_module, "execute_tool_call", fake_execute_tool_call)
    monkeypatch.setattr(chat_module, "get_messages", lambda *_: [])
    monkeypatch.setattr(chat_module, "get_session_user", lambda *_: "user-1")
    monkeypatch.setattr(chat_module, "save_messages", lambda session_id, messages: saved.setdefault("messages", messages))
    monkeypatch.setattr(chat_module, "schedule_memory_persistence", lambda *args, **kwargs: None)

    list(chat_module.chat_stream("session-1", "search both"))

    tool_messages = [message for message in saved["messages"] if message.get("role") == "tool"]
    assert [message["tool_call_id"] for message in tool_messages] == ["search-1", "search-2"]


def test_chat_stream_forces_final_answer_when_reasoning_budget_is_exhausted(monkeypatch):
    responses = [
        {"tool_calls": [_tool_call("search", {"query": "one"}, "search-1")]},
        {"tool_calls": [_tool_call("search", {"query": "two"}, "search-2")]},
        {"content": "Budget-limited final answer."},
    ]
    response_index = {"value": 0}
    use_tools_history = []
    executed = []
    saved = {}

    def fake_iter_response(messages, use_tools=True):
        use_tools_history.append(use_tools)
        current = responses[response_index["value"]]
        response_index["value"] += 1
        return _response_generator(**current)

    def fake_execute_tool_call(proxy):
        executed.append(proxy.function.name)
        return {
            "role": "tool",
            "tool_call_id": proxy.id,
            "content": json.dumps({"result": proxy.function.arguments}),
        }

    monkeypatch.setattr(chat_module, "iter_response", fake_iter_response)
    monkeypatch.setattr(chat_module, "execute_tool_call", fake_execute_tool_call)
    monkeypatch.setattr(chat_module, "get_messages", lambda *_: [])
    monkeypatch.setattr(chat_module, "get_session_user", lambda *_: "user-1")
    monkeypatch.setattr(chat_module, "save_messages", lambda session_id, messages: saved.setdefault("messages", messages))
    monkeypatch.setattr(chat_module, "schedule_memory_persistence", lambda *args, **kwargs: None)
    monkeypatch.setattr(chat_module, "MAX_REASONING_STEPS", 1)
    monkeypatch.setattr(chat_module, "MAX_TOTAL_TOOL_CALLS", 6)

    events = list(chat_module.chat_stream("session-1", "keep searching"))

    assert executed == ["search"]
    assert use_tools_history == [True, True, False]
    assert "Budget-limited final answer." in "".join(events)
    assert saved["messages"][-1]["content"] == "Budget-limited final answer."
