import requests
import os
import logging
from clients import openai_client

logger = logging.getLogger("search-agent")


def search(query: str) -> list:

    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"X-Subscription-Token": os.getenv("BRAVE_API_KEY")},
        params={"q": query, "count": 5, "extra_snippets": True},
    )

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

    llm_response = openai_client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "system",
                "content": "Summarize the search results concisely. Keep key facts, dates, and URLs.",
            },
            {"role": "user", "content": str(results)},
        ],
    )

    logger.info(f"summarize: {llm_response.usage.prompt_tokens} in, {llm_response.usage.completion_tokens} out")

    return llm_response.choices[0].message.content
