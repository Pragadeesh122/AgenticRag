import json
import logging
from clients import llm_client
from llm.response_utils import extract_first_text, usage_tokens

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
        summary_response = llm_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Summarize this conversation concisely. Preserve key facts, names, data, and context. Be brief.",
                },
                {"role": "user", "content": json.dumps(old_msgs)},
            ],
        )

        summary = extract_first_text(summary_response, "")
        prompt_tokens, completion_tokens = usage_tokens(
            getattr(summary_response, "usage", None) or {}
        )
        logger.info(
            f"summary tokens: {prompt_tokens} in, {completion_tokens} out"
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
