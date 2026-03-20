import json
import logging
from clients import openai_client

logger = logging.getLogger("orchestrator")


def _is_tool_msg(msg):
    """Check if a message is a tool response or an assistant with tool_calls."""
    if isinstance(msg, dict):
        return msg.get("role") == "tool" or msg.get("tool_calls")
    return getattr(msg, "role", None) == "tool" or getattr(msg, "tool_calls", None)


def summarize_messages(messages):
    system_msg = messages[0]
    split = max(len(messages) - 4, 1)
    while split > 1 and _is_tool_msg(messages[split]):
        split -= 1

    recent_msgs = messages[split:]
    old_msgs = messages[1:split]

    if not old_msgs:
        return messages

    logger.info("summarizing older messages to reduce token usage")
    try:
        summary_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Summarize this conversation concisely. Preserve key facts, names, data, and context. Be brief.",
                },
                {"role": "user", "content": json.dumps(old_msgs)},
            ],
        )

        summary = summary_response.choices[0].message.content
        logger.info(
            f"summary tokens: {summary_response.usage.prompt_tokens} in, {summary_response.usage.completion_tokens} out"
        )

        return [
            system_msg,
            {
                "role": "assistant",
                "content": f"[Previous conversation summary]: {summary}",
            },
            *recent_msgs,
        ]
    except Exception as e:
        logger.error(f"summarization failed, keeping full messages: {e}")
        return messages
