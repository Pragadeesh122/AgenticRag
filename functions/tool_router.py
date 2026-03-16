import json
import logging
from functions.search import search
from functions.portfolio import portfolio
from functions.local_kb import query_local_kb

logger = logging.getLogger("tool-router")

available_functions = {
    "search": search,
    "portfolio": portfolio,
    "query_local_kb": query_local_kb,
}


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

    logger.info(f"executing: {name}({args})")
    try:
        result = available_functions[name](**args)
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result),
        }
    except Exception as e:
        logger.error(f"tool {name} failed: {e}")
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps({"error": f"Tool execution failed: {e}"}),
        }
