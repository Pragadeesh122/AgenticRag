"""SSE streaming chat for project-scoped RAG conversations with agent selection."""

import json
import logging

from utils.streaming import iter_response
from utils.summarizer import summarize_messages
from api.session import get_messages, save_messages
from pipeline.retriever import retrieve
from prompts.project_chat import build_context_block
from agents.router import route as route_agent

logger = logging.getLogger("api.project_chat")

MAX_PROMPT_TOKENS = 10000


def project_chat_stream(
    session_id: str,
    user_message: str,
    project_id: str,
    chunk_count: int = 0,
    agent_name: str | None = None,
):
    """Generator that yields SSE events for a project-scoped chat turn."""
    messages = get_messages(session_id)

    # 1. Route to agent (pass full conversation for context-aware classification)
    agent = route_agent(user_message, agent_name, messages)
    yield _sse("thinking", json.dumps({"content": f"Routing to {agent.name} agent"}))
    yield _sse("agent", json.dumps({"name": agent.name, "description": agent.description}))
    logger.info(f"using agent: {agent.name}")

    # Always set the agent's system prompt
    if messages and messages[0].get("role") == "system":
        messages[0]["content"] = agent.system_prompt

    # 2. Retrieve with agent-specific overrides
    yield _sse("thinking", json.dumps({"content": "Searching for relevant passages in your documents..."}))
    try:
        results = retrieve(
            project_id=project_id,
            query=user_message,
            chunk_count=chunk_count,
            top_k=agent.top_k_override,
            alpha=agent.alpha_override,
        )
    except Exception as e:
        logger.error(f"retrieval failed: {e}")
        results = []

    sources = [
        {"source": r.get("source", ""), "page": r.get("page"), "score": r.get("score", 0)}
        for r in results
    ]
    yield _sse("thinking", json.dumps({"content": f"Found {len(results)} relevant passages"}))
    yield _sse("retrieval", json.dumps({"sources": sources, "count": len(results)}))

    # 3. Build the context-augmented message
    context_block = build_context_block(results)
    if agent.context_instructions:
        context_block += f"\n**Instructions:** {agent.context_instructions}\n"

    augmented_message = f"{user_message}\n{context_block}"
    messages.append({"role": "user", "content": augmented_message})

    prompt_tokens = 0
    full_content = ""

    # 4. Stream LLM response
    try:
        gen = iter_response(messages, use_tools=False)
        try:
            while True:
                token = next(gen)
                full_content += token
                yield _sse("token", token)
        except StopIteration as e:
            full_content, _, usage = e.value
            if usage:
                prompt_tokens = usage.prompt_tokens

    except Exception as e:
        logger.error(f"project chat failed: {e}")
        yield _sse("error", str(e))
        if messages and messages[-1].get("role") == "user":
            messages.pop()
        save_messages(session_id, messages)
        return

    messages.append({"role": "assistant", "content": full_content})

    # Summarize if context is getting large
    if prompt_tokens > MAX_PROMPT_TOKENS:
        updated = summarize_messages(messages)
        messages.clear()
        messages.extend(updated)

    save_messages(session_id, messages)

    yield _sse(
        "done",
        json.dumps({
            "agent": agent.name,
            "sources_used": len(results),
            "prompt_tokens": prompt_tokens,
            "structured": agent.structured_output,
        }),
    )


def _sse(event: str, data: str) -> str:
    data_lines = "\n".join(f"data: {line}" for line in data.split("\n"))
    return f"event: {event}\n{data_lines}\n\n"
