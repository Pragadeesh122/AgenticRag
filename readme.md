# AgenticRAG

An agentic RAG chat application that combines document-grounded retrieval with autonomous tool use. Upload documents to a project and chat with them using specialized AI agents, or use the general chat with web search, database queries, and headless browsing. Built with FastAPI, Next.js, Pinecone, and Redis.

## Quick Start

```bash
docker compose up
```

This starts the frontend on [localhost:3000](http://localhost:3000), the API on [localhost:8000](http://localhost:8000), and all supporting services (PostgreSQL, Redis, MinIO, Prometheus, Grafana, Loki, Tempo).

Create a root `.env` file and use [Getting Started](docs/getting-started.md) for the required environment variables.

## Documentation

Full documentation lives in [`docs/`](docs/index.md):

- [Getting Started](docs/getting-started.md) — setup, environment variables, local dev
- [Architecture](docs/architecture/overview.md) — system design, chat modes, LLM layer, memory, observability
- [Backend](docs/backend/api-reference.md) — API reference, agents, RAG pipeline, tools
- [Frontend](docs/frontend/overview.md) — app structure, SSE streaming, components
- [Security](docs/security.md) — rate limiting, auth, session ownership
- [Deployment](docs/deployment.md) — production Docker, monitoring
- [Contributing](docs/contributing.md) — how to add tools, agents, and LLM providers

Documentation hubs:

- [Docs Index](docs/index.md) — full doc map
- [Architecture Subsystem Guides](docs/architecture/overview.md) — links to chat modes, LLM layer, memory, and observability
- [Backend Subsystem Guides](docs/backend/api-reference.md) — links to agents, RAG pipeline, and tools
- [Frontend Subsystem Guides](docs/frontend/overview.md) — links to streaming and component docs
