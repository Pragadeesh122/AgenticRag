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
        "description": "Use this function whenever a question is asked about an individual named Pragadeesh",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search about Pragadeesh",
                },
            },
            "required": ["query"],
        },
    },
}

query_local_kb = {
    "type": "function",
    "function": {
        "name": "query_local_kb",
        "description": "Search the local knowledge base for information about Citro Essential Oils Distillery Industry, essential oils, their products, processes, or any related company data.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to search the local knowledge base",
                },
            },
            "required": ["query"],
        },
    },
}

tools = [search, portfolio, query_local_kb]
