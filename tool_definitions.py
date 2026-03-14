search_tool = {
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


tools = [search_tool]
