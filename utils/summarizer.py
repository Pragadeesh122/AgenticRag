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


def _dedupe_attachments(messages):
    """Return unique user-message attachments in order of first appearance."""
    seen = set()
    out = []
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("role") != "user":
            continue
        for att in msg.get("attachments") or []:
            aid = att.get("id")
            if not aid or aid in seen:
                continue
            seen.add(aid)
            out.append(att)
    return out


def _strip_for_summary(msg):
    """Sanitize a message for the summarizer prompt.

    Drops the structured ``attachments`` field and folds it into an inline
    filename annotation so the summarizer LLM has lightweight context about
    which files were involved without seeing raw ref objects.
    """
    if not isinstance(msg, dict):
        return msg
    out = {k: v for k, v in msg.items() if k != "attachments"}
    atts = msg.get("attachments") or []
    if atts and msg.get("role") == "user":
        names = ", ".join(a.get("filename") or "?" for a in atts)
        text = msg.get("content") or ""
        out["content"] = (
            f"{text}\n[attached: {names}]" if text else f"[attached: {names}]"
        )
    return out


def summarize_messages(messages):
    system_msg = messages[0]
    split = max(len(messages) - 4, 1)
    while split > 1 and _is_tool_msg(messages[split]):
        split -= 1

    recent_msgs = messages[split:]
    old_msgs = messages[1:split]

    if not old_msgs:
        return messages

    old_attachments = _dedupe_attachments(old_msgs)
    summarizable = [_strip_for_summary(m) for m in old_msgs]

    file_list = ", ".join(a.get("filename") or "?" for a in old_attachments)
    files_clause = (
        f" The user attached these files during this portion of the conversation: "
        f"{file_list}. Reference them by filename when relevant — never drop "
        f"file references from the summary."
        if file_list
        else ""
    )
    system_prompt = (
        "Summarize this conversation concisely. Preserve key facts, names, data, "
        "decisions, and any conclusions tied to specific files."
        + files_clause
        + " Be brief."
    )

    logger.info("summarizing older messages to reduce token usage")
    try:
        summary_response = llm_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(summarizable)},
            ],
        )

        summary = extract_first_text(summary_response, "")
        prompt_tokens, completion_tokens = usage_tokens(
            getattr(summary_response, "usage", None) or {}
        )
        logger.info(
            f"llm  call=summary tokens_in={prompt_tokens} tokens_out={completion_tokens}"
        )

        summary_msg: dict = {
            "role": "user",
            "content": f"[Previous conversation summary]: {summary}",
        }
        if old_attachments:
            summary_msg["attachments"] = old_attachments

        return [system_msg, summary_msg, *recent_msgs]
    except Exception as e:
        logger.error(f"summarization failed, keeping full messages: {e}")
        return messages
