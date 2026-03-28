"""Agent registry — discovers and exposes all available agents."""

import importlib
import pkgutil
import logging
from agents.base import Agent

logger = logging.getLogger("agents.registry")

AGENTS: dict[str, Agent] = {}

_SKIP = {"base", "registry", "router"}


def _discover_agents():
    import agents as pkg

    for finder, module_name, _ in pkgutil.iter_modules(pkg.__path__):
        if module_name.startswith("_") or module_name in _SKIP:
            continue

        module = importlib.import_module(f"agents.{module_name}")
        agent_obj = getattr(module, "agent", None)
        if not isinstance(agent_obj, Agent):
            continue

        AGENTS[agent_obj.name] = agent_obj
        logger.info(f"registered agent: {agent_obj.name}")


_discover_agents()


def get_agent(name: str) -> Agent | None:
    return AGENTS.get(name)


def get_agent_names() -> list[str]:
    return list(AGENTS.keys())
