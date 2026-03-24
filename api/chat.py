"""SSE streaming chat endpoint — runs the full orchestrator loop."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from functions.tool_router import execute_tool_call
from utils.streaming import iter_response, ToolCallProxy
from utils.summarizer import summarize_messages
from memory import extract_and_save_memories
from api.session import get_messages, save_messages

logger = logging.getLogger("api.chat")

MAX_PROMPT_TOKENS = 5000
MAX_TOOL_CALLS = 3


def chat_stream(session_id: str, user_message: str):
    """Generator that yields SSE-formatted events for a single user turn.

    Event types:
        token   — a chunk of the assistant's text response
        tool    — a tool was called (name + args)
        error   — something went wrong
        done    — final event with metadata
    """
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
                prompt_tokens = usage.prompt_tokens

            if not tool_calls or tool_call_count >= MAX_TOOL_CALLS:
                if tool_call_count >= MAX_TOOL_CALLS:
                    logger.info(f"max tool calls reached ({MAX_TOOL_CALLS})")
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
                    try:
                        while True:
                            token = next(gen)
                            content += token
                            yield _sse("token", token)
                    except StopIteration as e:
                        content, _, usage = e.value

                    messages.remove(stop_msg)
                    if usage:
                        prompt_tokens = usage.prompt_tokens

                full_content = content
                break

            # Process tool calls
            tool_call_count += 1
            tool_names = [tc["function"]["name"] for tc in tool_calls]
            tools_used.extend(tool_names)
            logger.info(f"tool_calls: {tool_names} ({tool_call_count}/{MAX_TOOL_CALLS})")

            for name in tool_names:
                yield _sse("tool", json.dumps({"name": name}))

            messages.append(
                {"role": "assistant", "tool_calls": tool_calls, "content": None}
            )

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
                for _, result in results:
                    messages.append(result)

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
        updated = summarize_messages(messages)
        messages.clear()
        messages.extend(updated)

    save_messages(session_id, messages)

    yield _sse(
        "done",
        json.dumps({"tools_used": tools_used, "prompt_tokens": prompt_tokens}),
    )


def end_session_with_memory(session_id: str) -> None:
    """Extract memories from the conversation before deleting."""
    try:
        messages = get_messages(session_id)
        extract_and_save_memories(messages)
    except KeyError:
        pass


def _sse(event: str, data: str) -> str:
    """Format a single SSE event.

    Per SSE spec, multi-line data must use separate 'data:' lines.
    """
    data_lines = "\n".join(f"data: {line}" for line in data.split("\n"))
    return f"event: {event}\n{data_lines}\n\n"
