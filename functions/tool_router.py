import json
import logging
from functions import available_functions, cacheable_tools
from memory.cache import get_cached_result, cache_result

logger = logging.getLogger("tool-router")


def execute_tool_call(tool_call) -> dict:
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as e:
        logger.error(f"failed to parse arguments for {name}: {e}")
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps({"error": f"Invalid arguments: {e}"}),
        }

    if name not in available_functions:
        logger.error(f"unknown tool: {name}")
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
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": cached,
            }

    logger.info(f"executing: {name}({args})")
    try:
        result = available_functions[name](**args)
        result_str = json.dumps(result)

        # Cache the result
        if name in cacheable_tools and query_str:
            cache_result(name, query_str, result_str)

        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result_str,
        }
    except Exception as e:
        logger.error(f"tool {name} failed: {e}")
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps({"error": f"Tool execution failed: {e}"}),
        }
