search = {
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

portfolio = {
    "type": "function",
    "function": {
        "name": "portfolio",
        "description": "Use this function whenever a question is asked about an individual named pragadeesh",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "the search about Pragadeesh",
                },
            },
            "required": ["query"],
        },
    },
}

tools = [search, portfolio]
