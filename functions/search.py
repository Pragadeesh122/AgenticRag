import requests
import os
import logging
from clients import llm_client
from prompts.search_summarizer import SEARCH_SUMMARIZER
from llm.response_utils import extract_first_text, usage_tokens

logger = logging.getLogger("search-agent")

SCHEMA = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "Search the web for any information. Use this for questions about current events, dates, weather, news, facts, or anything you don't know.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on the web",
                },
            },
            "required": ["query"],
        },
    },
}

CACHEABLE = True


def search(query: str) -> str:
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        logger.error("BRAVE_API_KEY not set")
        return "Search failed: BRAVE_API_KEY not configured."

    try:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": api_key},
            params={"q": query, "count": 5, "extra_snippets": True},
            timeout=10,
        )
        response.raise_for_status()
    except requests.Timeout:
        logger.error(f"brave search timed out for: '{query}'")
        return "Search failed: request timed out."
    except requests.RequestException as e:
        logger.error(f"brave search request failed: {e}")
        return f"Search failed: {e}"

    searchResponse = response.json().get("web", {}).get("results", [])

    results = []
    for result in searchResponse:
        results.append(
            {
                "title": result["title"],
                "url": result["url"],
                "description": result.get("description", ""),
                "extra_snippets": result.get("extra_snippets", []),
            }
        )

    logger.info(f"brave search: '{query}' → {len(results)} results")

    if not results:
        return f"No search results found for: '{query}'"

    try:
        llm_response = llm_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SEARCH_SUMMARIZER,
                },
                {"role": "user", "content": str(results)},
            ],
        )
        prompt_tokens, completion_tokens = usage_tokens(
            getattr(llm_response, "usage", None) or {}
        )

        logger.info(f"summarize: {prompt_tokens} in, {completion_tokens} out")
        return extract_first_text(llm_response, "")
    except Exception as e:
        logger.error(f"summarization failed: {e}")
        return str(results)
