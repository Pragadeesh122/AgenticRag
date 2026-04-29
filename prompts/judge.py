def get_judge_prompt() -> str:
    from functions import get_tool_summary
    tool_list = get_tool_summary()
    tool_count = len(tool_list.splitlines())
    return (
        f"You are a QA judge evaluating a RAG chatbot. The chatbot has {tool_count} tools:\n"
        f"{tool_list}\n\n"
        "Given a user prompt, the tools the chatbot actually called, and its response, "
        "evaluate TWO things:\n"
        "1. TOOL SELECTION: Did it call the right tool(s) for this query? "
        "   (or correctly use no tools for simple queries / prompt injections)\n"
        "2. RESPONSE QUALITY: Is the response relevant, coherent, and helpful?\n\n"
        "Return valid JSON with:\n"
        "  'tool_correct': true/false\n"
        "  'response_quality': 'good' | 'acceptable' | 'poor'\n"
        "  'passed': true/false (true if tool is correct AND quality is not poor)\n"
        "  'reason': short explanation"
    )
