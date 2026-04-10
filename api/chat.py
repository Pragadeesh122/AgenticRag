"""SSE streaming chat endpoint — runs the full orchestrator loop."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from functions.tool_router import execute_tool_call
from utils.streaming import iter_response, ToolCallProxy
from utils.summarizer import summarize_messages
from api.session import get_messages, save_messages, get_session_user
from llm.response_utils import usage_tokens
from observability.context import pop_context, push_context
from observability.metrics import (
    observe_agent_route,
    observe_max_tool_calls_reached,
    observe_summarization,
)
from services.chat_postprocess_service import (
    schedule_memory_persistence,
)

logger = logging.getLogger("api.chat")

MAX_PROMPT_TOKENS = 5000
MAX_TOOL_CALLS = 3


def _format_tool_thinking(name: str, args: dict) -> str:
    """Format a human-readable thinking step for a tool call."""
    if name == "search":
        return f'Searching the web for "{args.get("query", "")}"'
    elif name == "query_db":
        return f'Querying the database: {args.get("question", "")}'
    elif name == "browser_task":
        url = args.get("url", "")
        goal = args.get("goal", "")
        return f"Browsing {url}: {goal}" if url else f"Browsing: {goal}"
    elif name == "crawl_website":
        url = args.get("url", "")
        question = args.get("question", "")
        return (
            f"Extracting website content from {url}: {question}"
            if question
            else f"Extracting website content from {url}"
        )
    elif name == "query_local_kb":
        return f'Searching knowledge base for "{args.get("query", "")}"'
    elif name == "portfolio":
        return f'Looking up: {args.get("query", "")}'
    else:
        return f"Running {name}"


def _format_result_summary(name: str, content: str) -> str:
    """Format a brief summary of a tool result."""
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "error" in data:
            return f"{name} encountered an error: {data['error'][:100]}"
        if isinstance(data, dict) and "count" in data:
            return f"Received {data['count']} results from {name}"
        if isinstance(data, dict) and "rows" in data:
            return f"Got {len(data['rows'])} rows from database"
        if isinstance(data, list):
            return f"Received {len(data)} results from {name}"
    except (json.JSONDecodeError, TypeError):
        pass
    return f"Received results from {name}"


def chat_stream(session_id: str, user_message: str):
    """Generator that yields SSE-formatted events for a single user turn.

    Event types:
        token     — a chunk of the assistant's text response
        tool      — a tool was called (name + args)
        thinking  — reasoning/activity step
        error     — something went wrong
        done      — final event with metadata
    """
    user_id = get_session_user(session_id)
    context_tokens = push_context(
        chat_type="general",
        session_id=session_id,
        user_id=user_id,
    )
    try:
        observe_agent_route(
            selected_agent="orchestrator",
            route_mode="general",
            status="success",
            duration_seconds=0.0,
        )

        messages = get_messages(session_id)
        messages.append({"role": "user", "content": user_message})

        tool_call_count = 0
        prompt_tokens = 0
        tools_used = []
        full_content = ""

        try:
            while True:
                content = ""
                tool_calls = None
                usage = None

                gen = iter_response(messages)
                try:
                    while True:
                        token = next(gen)
                        content += token
                        yield _sse("token", token)
                except StopIteration as e:
                    # iter_response returns (content, tool_calls, usage)
                    content, tool_calls, usage = e.value

                if usage:
                    prompt_tokens, _ = usage_tokens(usage)

                if not tool_calls or tool_call_count >= MAX_TOOL_CALLS:
                    if tool_call_count >= MAX_TOOL_CALLS:
                        logger.info(f"max tool calls reached ({MAX_TOOL_CALLS})")
                        observe_max_tool_calls_reached(chat_type="general")
                        stop_msg = {
                            "role": "system",
                            "content": (
                                "You have reached the maximum number of tool calls. "
                                "Do NOT attempt any more tool calls. Respond with the "
                                "best answer you can based on the information gathered."
                            ),
                        }
                        messages.append(stop_msg)

                        # Final response without tools
                        gen = iter_response(messages, use_tools=False)
                        content = ""
                        final_tool_calls = None
                        try:
                            while True:
                                token = next(gen)
                                content += token
                                yield _sse("token", token)
                        except StopIteration as e:
                            content, final_tool_calls, usage = e.value

                        if (not (content or "").strip()) or final_tool_calls:
                            logger.warning(
                                "final no-tool pass returned empty/tool-calls after max tools; "
                                "retrying with stricter no-tool instruction on same model"
                            )
                            fallback_msg = {
                                "role": "system",
                                "content": (
                                    "Tool-call budget is exhausted. Do not call tools. "
                                    "Provide your best final answer using only the existing "
                                    "tool outputs and conversation context."
                                ),
                            }
                            messages.append(fallback_msg)
                            gen = iter_response(messages, use_tools=False)
                            content = ""
                            try:
                                while True:
                                    token = next(gen)
                                    content += token
                                    yield _sse("token", token)
                            except StopIteration as e:
                                content, _, usage = e.value
                            messages.remove(fallback_msg)

                        if not (content or "").strip():
                            logger.warning("final response still empty; sending graceful fallback text")
                            content = (
                                "I gathered the tool results, but couldn't generate a final response. "
                                "Please retry once and I will answer directly."
                            )
                            yield _sse("token", content)

                        messages.remove(stop_msg)
                        if usage:
                            prompt_tokens, _ = usage_tokens(usage)

                    full_content = content
                    break

                # Process tool calls
                tool_call_count += 1
                tool_names = [tc["function"]["name"] for tc in tool_calls]
                tools_used.extend(tool_names)
                logger.info(f"tool_calls: {tool_names} ({tool_call_count}/{MAX_TOOL_CALLS})")

                for tc in tool_calls:
                    name = tc["function"]["name"]
                    try:
                        args = json.loads(tc["function"]["arguments"])
                    except (json.JSONDecodeError, KeyError):
                        args = {}
                    # Emit thinking step about what we're about to do
                    yield _sse("thinking", json.dumps({"content": _format_tool_thinking(name, args)}))
                    yield _sse("tool", json.dumps({"name": name, "args": args}))

                messages.append(
                    {"role": "assistant", "tool_calls": tool_calls, "content": None}
                )

                # Execute tools
                proxies = [ToolCallProxy(tc) for tc in tool_calls]
                with ThreadPoolExecutor() as executor:
                    futures = {
                        executor.submit(execute_tool_call, p): p for p in proxies
                    }
                    results = []
                    for future in as_completed(futures):
                        results.append((futures[future], future.result()))
                    order = {p.id: i for i, p in enumerate(proxies)}
                    results.sort(key=lambda r: order[r[0].id])
                    for proxy, result in results:
                        messages.append(result)
                        # Emit thinking step about result
                        result_content = result.get("content", "")
                        summary = _format_result_summary(proxy.function.name, result_content)
                        yield _sse("thinking", json.dumps({"content": summary}))

        except Exception as e:
            logger.error(f"chat failed: {e}")
            yield _sse("error", str(e))
            # Remove the failed user message
            if messages and messages[-1].get("role") == "user":
                messages.pop()
            save_messages(session_id, messages)
            return

        messages.append({"role": "assistant", "content": full_content})

        # Summarize if token count is high
        if prompt_tokens > MAX_PROMPT_TOKENS:
            observe_summarization(reason="prompt_tokens")
            updated = summarize_messages(messages)
            messages.clear()
            messages.extend(updated)

        save_messages(session_id, messages)

        if user_id:
            schedule_memory_persistence(messages, user_id)

        yield _sse(
            "done",
            json.dumps({"tools_used": tools_used, "prompt_tokens": prompt_tokens}),
        )
    finally:
        pop_context(context_tokens)


def end_session_with_memory(session_id: str) -> None:
    """Extract memories from the conversation before deleting."""
    try:
        user_id = get_session_user(session_id)
        if not user_id:
            return
        messages = get_messages(session_id)
        schedule_memory_persistence(messages, user_id)
    except KeyError:
        pass


def _sse(event: str, data: str) -> str:
    """Format a single SSE event.

    Per SSE spec, multi-line data must use separate 'data:' lines.
    """
    data_lines = "\n".join(f"data: {line}" for line in data.split("\n"))
    return f"event: {event}\n{data_lines}\n\n"
