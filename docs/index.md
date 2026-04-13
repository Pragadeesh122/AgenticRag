# AgenticRAG

An agentic RAG chat application that combines document-grounded retrieval with autonomous tool use. Upload documents to a project and chat with them using specialized AI agents, or use the general chat with web search, database queries, and headless browsing.

```
Browser  <-->  Next.js (frontend + API routes)  <-->  FastAPI (Python backend)
                      |                                      |
                 PostgreSQL (Prisma)                    Redis (sessions)
                 (auth, sessions, messages)             Pinecone (vectors)
                                                       MinIO (file storage)
                                                       PostgreSQL (app data)
```

## Documentation

### Getting Started

| Document | Description |
|----------|-------------|
| [Getting Started](getting-started.md) | Prerequisites, environment setup, Docker, local dev |

### Architecture

| Document | Description |
|----------|-------------|
| [System Overview](architecture/overview.md) | Two-server design, data flow, service topology |
| [Chat Modes](architecture/chat-modes.md) | General orchestration loop vs project RAG pipeline |
| [LLM Layer](architecture/llm-layer.md) | Provider abstraction, model routing, cost tracking |
| [Memory](architecture/memory.md) | Redis working memory, Postgres history, user memory |
| [Observability](architecture/observability.md) | Prometheus, Loki, Tempo, Grafana dashboards |

### Backend

| Document | Description |
|----------|-------------|
| [API Reference](backend/api-reference.md) | Endpoints, request/response shapes, rate limits |
| [Agents](backend/agents.md) | Agent system, auto-discovery, intent routing |
| [RAG Pipeline](backend/pipeline.md) | Ingestion, chunking, embedding, adaptive retrieval |
| [Tools](backend/tools.md) | Tool system, planner, caching, adding new tools |

### Frontend

| Document | Description |
|----------|-------------|
| [Overview](frontend/overview.md) | App structure, routing, auth, component tree |
| [Streaming](frontend/streaming.md) | SSE protocol, message lifecycle |
| [Components](frontend/components.md) | Quiz, charts, mermaid rendering |

### Operations & Contributing

| Document | Description |
|----------|-------------|
| [Security](security.md) | Rate limiting, authentication, session ownership |
| [Deployment](deployment.md) | Production Docker setup, monitoring, migrations |
| [Evaluation](evaluation.md) | Test suite, RAG eval harness, metrics |
| [Contributing](contributing.md) | Adding tools, agents, and LLM providers |
