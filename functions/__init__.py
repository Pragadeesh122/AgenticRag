import importlib
import pkgutil
import logging

from utils.tool_planner import DEFAULT_TOOL_POLICY, ToolPolicy, normalize_tool_policy

logger = logging.getLogger("registry")

# Auto-discovered tool data
available_functions = {}
tool_schemas = []
cacheable_tools = set()
tool_policies: dict[str, ToolPolicy] = {}

# Files that are not tools
_SKIP = {"tool_router", "compare_kb"}


def _discover_tools():
    """Scan the functions package for modules that export a SCHEMA and a matching function."""
    import functions as pkg

    for finder, module_name, _ in pkgutil.iter_modules(pkg.__path__):
        if module_name.startswith("_") or module_name in _SKIP:
            continue

        module = importlib.import_module(f"functions.{module_name}")
        schema = getattr(module, "SCHEMA", None)
        if not schema:
            continue

        func_name = schema["function"]["name"]
        func = getattr(module, func_name, None)
        if not func:
            logger.warning(
                f"tool '{func_name}' has SCHEMA but no matching function in {module_name}.py"
            )
            continue

        available_functions[func_name] = func
        tool_schemas.append(schema)
        tool_policies[func_name] = normalize_tool_policy(
            getattr(module, "POLICY", DEFAULT_TOOL_POLICY)
        )
        if getattr(module, "CACHEABLE", False):
            cacheable_tools.add(func_name)

        logger.info(f"registered tool: {func_name}")


_discover_tools()


def get_tool_summary() -> str:
    """Return a numbered list of registered tools with their descriptions."""
    lines = []
    for i, schema in enumerate(tool_schemas, 1):
        name = schema["function"]["name"]
        desc = schema["function"]["description"]
        lines.append(f"{i}. {name} — {desc}")
    return "\n".join(lines)
