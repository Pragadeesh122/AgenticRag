"""Base agent definition for project-scoped RAG agents."""

from dataclasses import dataclass, field


@dataclass
class Agent:
    """A specialized agent with its own system prompt and retrieval config."""

    name: str
    description: str
    system_prompt: str

    # Retrieval overrides (None = use adaptive defaults)
    top_k_override: int | None = None
    alpha_override: float | None = None

    # Whether output should be parsed as structured JSON
    structured_output: bool = False

    # JSON schema hint injected into the prompt for structured agents
    output_schema: str = ""

    # Extra instructions appended to the context block
    context_instructions: str = ""
