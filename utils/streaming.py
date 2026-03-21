import sys
import logging
from clients import openai_client
from tools import tools

logger = logging.getLogger("orchestrator")


def stream_response(messages, model="gpt-5.4-mini", use_tools=True):
    """Stream an LLM response, printing text tokens as they arrive.

    Returns (content, tool_calls, usage) where:
    - content: full text response (or None if tool calls)
    - tool_calls: list of tool call objects (or None if text)
    - usage: token usage dict
    """
    kwargs = {"model": model, "messages": messages, "stream": True,
              "stream_options": {"include_usage": True}}
    if use_tools:
        kwargs["tools"] = tools

    stream = openai_client.chat.completions.create(**kwargs)

    content = ""
    tool_calls_by_index = {}
    usage = None

    for chunk in stream:
        # Capture usage from the final chunk
        if chunk.usage:
            usage = chunk.usage

        delta = chunk.choices[0].delta if chunk.choices else None
        if not delta:
            continue

        # Stream text content to stdout immediately
        if delta.content:
            sys.stdout.write(delta.content)
            sys.stdout.flush()
            content += delta.content

        # Accumulate tool call deltas
        if delta.tool_calls:
            for tc_delta in delta.tool_calls:
                idx = tc_delta.index
                if idx not in tool_calls_by_index:
                    tool_calls_by_index[idx] = {
                        "id": tc_delta.id or "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    }
                tc = tool_calls_by_index[idx]
                if tc_delta.id:
                    tc["id"] = tc_delta.id
                if tc_delta.function:
                    if tc_delta.function.name:
                        tc["function"]["name"] += tc_delta.function.name
                    if tc_delta.function.arguments:
                        tc["function"]["arguments"] += tc_delta.function.arguments

    if content:
        sys.stdout.write("\n")
        sys.stdout.flush()

    if usage:
        logger.info(f"tokens: {usage.prompt_tokens} in, {usage.completion_tokens} out")

    # Build tool_calls list sorted by index
    if tool_calls_by_index:
        sorted_tcs = [tool_calls_by_index[i] for i in sorted(tool_calls_by_index)]
        return None, sorted_tcs, usage

    return content, None, usage


class ToolCallProxy:
    """Lightweight wrapper so execute_tool_call can access .id, .function.name, .function.arguments."""
    def __init__(self, tc_dict):
        self.id = tc_dict["id"]
        self.function = type("Fn", (), {
            "name": tc_dict["function"]["name"],
            "arguments": tc_dict["function"]["arguments"],
        })()
