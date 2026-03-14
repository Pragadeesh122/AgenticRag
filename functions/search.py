import requests
import os


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

    return results
