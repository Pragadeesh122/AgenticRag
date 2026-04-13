# Contributing

## Adding a New Tool

Tools are autonomous capabilities available to the general chat orchestrator. They're auto-discovered — no manual registration needed.

### 1. Create the module

Create `functions/my_tool.py`:

```python
import logging

logger = logging.getLogger("my_tool")

SCHEMA = {
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": (
            "Describe what this tool does and when the LLM should use it. "
            "Be specific about when to use vs. not use this tool."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for",
                },
            },
            "required": ["query"],
        },
    },
}

# Optional: cache results for identical queries
CACHEABLE = True

# Optional: execution policy for the tool planner
POLICY = {
    "execution_mode": "parallel_safe",    # or "sequential_first"
    "max_parallel_instances": 3,
    "requires_fresh_input": False,
    "dedupe_key_fields": ("query",),
}


def my_tool(query: str) -> dict:
    """Function name MUST match SCHEMA["function"]["name"]."""
    logger.info(f"executing my_tool: {query}")
    # ... implementation ...
    return {"result": "..."}
```

### 2. Restart the API

The tool is auto-discovered on import. You'll see `registered tool: my_tool` in the logs.

### 3. Update the orchestrator prompt (optional)

If the LLM needs guidance on when to use the tool, update `prompts/orchestrator.py` to mention it.

## Adding a New Agent

Agents are specialized response generators for project chat.

### 1. Create the module

Create `agents/my_agent.py`:

```python
from agents.base import Agent

agent = Agent(
    name="my_agent",
    description="One-line description shown in the UI agent selector",
    system_prompt="""You are a specialized assistant that...

When given context from documents, you should...

Always...
Never...
""",
    # Override retrieval defaults (optional)
    top_k_override=15,       # More chunks for comprehensive coverage
    alpha_override=0.8,      # Favor dense (semantic) over sparse (keyword)

    # Structured JSON output (optional)
    structured_output=True,
    output_schema='{"type": "object", "properties": {...}}',

    # Extra instructions appended to retrieved context (optional)
    context_instructions="Focus on quantitative data and cite page numbers.",
)
```

### 2. Update the router

Add the agent to the classification prompt in `agents/router.py`:

```python
CLASSIFICATION_PROMPT = """\
...
Available agents:
- reasoning: Deep analysis, Q&A, comparisons
- my_agent: One-line description of when to use this agent
...\
"""
```

### 3. Add a frontend renderer (structured output only)

If `structured_output=True`, add:

1. A parser function (`tryParseMyFormat()`) in a new renderer component
2. Detection in `MessageBubble.tsx` (after `tryParseQuiz` and `tryParseChart`)
3. A renderer component to display the parsed JSON

### 4. Restart the API

The agent is auto-discovered. You'll see `registered agent: my_agent` in the logs.

## Adding a New LLM Provider

All providers go through LiteLLM, so adding a new one is primarily a matter of configuring model name resolution.

### 1. Create the provider

Create `llm/providers/my_provider.py`:

```python
from llm.providers.litellm_provider import LiteLLMProvider


class MyProvider(LiteLLMProvider):
    def __init__(self):
        super().__init__(
            name="myprovider",
            model_prefix="myprovider",              # LiteLLM routing prefix
            default_chat_model="myprovider-default", # Fallback model
            default_embedding_model=None,            # Or a model name
        )

    # Optional: extra kwargs for all completion calls
    def _completion_extra_kwargs(self):
        return {"api_base": "https://api.myprovider.com/v1"}
```

### 2. Register the provider

In `llm/providers/__init__.py`:

```python
from llm.providers.my_provider import MyProvider

PROVIDER_BUILDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    # ...
    "myprovider": MyProvider,
}
```

### 3. Add aliases (optional)

In `llm/factory.py`:

```python
PROVIDER_ALIASES = {
    # ...
    "mp": "myprovider",
}
```

And optionally add inference rules in `_infer_provider_from_model()` if model names have a distinctive prefix.

### 4. Use it

```python
# Explicit prefix
client.chat.completions.create(model="myprovider/model-name", ...)

# Or with alias
client.chat.completions.create(model="mp/model-name", ...)
```

## Code Conventions

| Area | Convention |
|------|-----------|
| **Python** | `uv` for package management, `pyproject.toml` for dependencies |
| **Frontend** | `yarn` (not npm), TypeScript strict mode |
| **Testing** | pytest, test files named `tests/test_*.py` |
| **Commit messages** | Short single-line messages, no conventional commit prefixes |
| **Branches** | Work on feature branches, merge to `main` |

## Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_chunker.py

# With verbose output
uv run pytest -v
```

## Running the Eval Harness

```bash
# Quick retrieval-only evaluation
uv run python evals/run_eval.py --dataset smoke --skip-judge

# Full evaluation with LLM judge
uv run python evals/run_eval.py --dataset smoke
```

See [Evaluation](evaluation.md) for details on metrics and dataset format.
