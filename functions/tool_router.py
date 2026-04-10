import json
import logging
import time
from functions import available_functions, cacheable_tools
from memory.cache import get_cached_result, cache_result
from observability.metrics import observe_tool_cache, observe_tool_outcome

logger = logging.getLogger("tool-router")


def execute_tool_call(tool_call) -> dict:
    name = tool_call.function.name
    started = time.perf_counter()
    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as e:
        logger.error(f"failed to parse arguments for {name}: {e}")
        observe_tool_outcome(
            tool_name=name or "unknown",
            status="error",
            duration_seconds=time.perf_counter() - started,
        )
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps({"error": f"Invalid arguments: {e}"}),
        }

    if name not in available_functions:
        logger.error(f"unknown tool: {name}")
        observe_tool_outcome(
            tool_name=name or "unknown",
            status="error",
            duration_seconds=time.perf_counter() - started,
        )
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps({"error": f"Unknown tool: {name}"}),
        }

    # Check cache for similar queries
    query_str = args.get("query", "")
    if name in cacheable_tools and query_str:
        cached = get_cached_result(name, query_str)
        if cached:
            observe_tool_cache(tool_name=name, cache_status="hit")
            observe_tool_outcome(
                tool_name=name,
                status="success",
                duration_seconds=time.perf_counter() - started,
            )
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": cached,
            }
        observe_tool_cache(tool_name=name, cache_status="miss")
    else:
        observe_tool_cache(tool_name=name, cache_status="skip")

    logger.info(f"executing: {name}({args})")
    try:
        result = available_functions[name](**args)
        result_str = json.dumps(result)

        # Cache the result
        if name in cacheable_tools and query_str:
            cache_result(name, query_str, result_str)

        observe_tool_outcome(
            tool_name=name,
            status="success",
            duration_seconds=time.perf_counter() - started,
        )

        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result_str,
        }
    except Exception as e:
        logger.error(f"tool {name} failed: {e}")
        observe_tool_outcome(
            tool_name=name,
            status="error",
            duration_seconds=time.perf_counter() - started,
        )
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps({"error": f"Tool execution failed: {e}"}),
        }
