def get_query_generator_prompt() -> str:
    from functions import get_tool_summary
    tool_list = get_tool_summary()
    tool_count = len(tool_list.splitlines())
    return (
        f"You are a QA engineer testing a RAG chatbot. The chatbot has {tool_count} tools:\n"
        f"{tool_list}\n\n"
        "Generate diverse test queries that exercise different tools, edge cases, "
        "and prompt injection attempts. Include at least one query that requires "
        "database lookups (e.g. order counts, top products, customer info). "
        "Keep each query to 1-2 sentences.\n\n"
        'Return valid JSON: {"queries": ["query1", "query2", ...]}'
    )
