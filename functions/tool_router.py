import json
import logging
from functions.search import search
from functions.portfolio import portfolio

logger = logging.getLogger("tool-router")

available_functions = {"search": search, "portfolio": portfolio}


def execute_tool_call(tool_call) -> dict:
    fn = available_functions[tool_call.function.name]
    args = json.loads(tool_call.function.arguments)
    logger.info(f"executing: {tool_call.function.name}({args})")
    result = fn(**args)
    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(result),
    }
