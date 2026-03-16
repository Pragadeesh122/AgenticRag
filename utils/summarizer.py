import json
import logging
from clients import openai_client

logger = logging.getLogger("orchestrator")


def summarize_messages(messages):
    system_msg = messages[0]
    recent_msgs = messages[-4:]
    old_msgs = messages[1:-4]

    if not old_msgs:
        return messages

    logger.info("summarizing older messages to reduce token usage")
    try:
        summary_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarize this conversation concisely. Preserve key facts, names, data, and context. Be brief."},
                {"role": "user", "content": json.dumps(old_msgs)},
            ],
        )

        summary = summary_response.choices[0].message.content
        logger.info(f"summary tokens: {summary_response.usage.prompt_tokens} in, {summary_response.usage.completion_tokens} out")

        return [
            system_msg,
            {"role": "assistant", "content": f"[Previous conversation summary]: {summary}"},
            *recent_msgs,
        ]
    except Exception as e:
        logger.error(f"summarization failed, keeping full messages: {e}")
        return messages
