"""Agent router — classifies user intent and selects the appropriate agent."""

import logging
from clients import openai_client
from agents.registry import AGENTS
from agents.base import Agent

logger = logging.getLogger("agents.router")

CLASSIFICATION_PROMPT = """\
You are an intent classifier for a document Q&A system. Based on the conversation, \
decide which agent should handle the user's latest message.

Available agents:
- reasoning: Deep analysis, Q&A, comparisons, explaining concepts
- quiz: Generating quizzes, test questions, flashcards
- visualization: Charts, diagrams, visual comparisons, data visualization
- summary: Summarizing documents, key takeaways, overviews

If the user is continuing a previous task (e.g. "one more", "again", "next"), \
keep the same agent. Only switch when the intent clearly changes.

Respond with ONLY the agent name (one word). Default to "reasoning" if unclear.\
"""


def classify_intent(messages: list[dict]) -> str:
    """Classify intent from the full conversation."""
    try:
        classification_messages = [{"role": "system", "content": CLASSIFICATION_PROMPT}]

        # Pass the full conversation (skip system prompt)
        for msg in messages:
            if msg["role"] in ("user", "assistant"):
                classification_messages.append({
                    "role": msg["role"],
                    "content": msg["content"][:300],
                })

        response = openai_client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=classification_messages,
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


def route(user_message: str, agent_name: str | None, messages: list[dict]) -> Agent:
    """Route to an agent — explicit name or auto-classify from conversation."""
    if agent_name and agent_name != "auto" and agent_name in AGENTS:
        return AGENTS[agent_name]

    # Auto: classify from full conversation + new message
    classify_msgs = messages + [{"role": "user", "content": user_message}]
    classified = classify_intent(classify_msgs)
    return AGENTS[classified]
