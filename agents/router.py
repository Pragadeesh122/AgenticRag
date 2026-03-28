"""Agent router — classifies user intent and selects the appropriate agent."""

import json
import logging
from clients import openai_client
from agents.registry import AGENTS, get_agent
from agents.base import Agent

logger = logging.getLogger("agents.router")

CLASSIFICATION_PROMPT = """\
You are an intent classifier for a document Q&A system. Given the user's message, \
classify which agent should handle it.

Available agents:
- reasoning: Deep analysis, Q&A, comparisons, explaining concepts, finding relationships
- quiz: Generating quizzes, test questions, flashcards, practice problems
- visualization: Creating charts, graphs, plotting data, showing statistics visually
- summary: Summarizing documents, key takeaways, executive summaries, overviews

Respond with ONLY the agent name (one word). If unclear, default to "reasoning".\
"""


def classify_intent(user_message: str) -> str:
    """Classify user message intent and return the best agent name."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": CLASSIFICATION_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_completion_tokens=10,
            temperature=0,
        )
        agent_name = response.choices[0].message.content.strip().lower()

        if agent_name in AGENTS:
            logger.info(f"classified intent → {agent_name}")
            return agent_name

        logger.warning(f"unknown agent '{agent_name}', falling back to reasoning")
        return "reasoning"

    except Exception as e:
        logger.error(f"intent classification failed: {e}")
        return "reasoning"


def route(user_message: str, agent_name: str | None = None) -> Agent:
    """Get the agent for a message — uses explicit name or auto-classifies.

    Args:
        user_message: the user's input
        agent_name: explicit agent name, or None to auto-classify

    Returns:
        The selected Agent instance
    """
    if agent_name and agent_name in AGENTS:
        return AGENTS[agent_name]

    if agent_name == "auto" or agent_name is None:
        classified = classify_intent(user_message)
        return AGENTS[classified]

    # Unknown name — fall back to reasoning
    logger.warning(f"unknown agent '{agent_name}', using reasoning")
    return AGENTS["reasoning"]
