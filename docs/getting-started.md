# Getting Started

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- For local dev without Docker:
  - Python 3.12+ with [uv](https://docs.astral.sh/uv/)
  - Node.js 18+ with [yarn](https://yarnpkg.com/)
  - PostgreSQL 17
  - Redis Stack

## Quick Start

```bash
docker compose up
```

This starts the full stack:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | `http://localhost:3000` | Next.js app |
| API | `http://localhost:8000` | FastAPI backend |
| Worker | — | ARQ document ingestion worker |
| PostgreSQL | `localhost:5432` | Auth + app data |
| Redis | `localhost:6379` | Sessions, cache, memory, job queue |
| RedisInsight | `http://localhost:8001` | Redis GUI |
| MinIO | `http://localhost:9000` | Object storage for uploads |
| MinIO Console | `http://localhost:9001` | MinIO admin UI |
| Prometheus | `http://localhost:9090` | Metrics |
| Loki | `http://localhost:3100` | Log aggregation |
| Tempo | `http://localhost:3200` | Distributed tracing |
| Grafana | `http://localhost:3001` | Dashboards and alerting |

Rebuild when dependencies or Dockerfiles change:

```bash
docker compose up --build
```

Stop and remove containers:

```bash
docker compose down
```

Reset all local state (volumes):

```bash
docker compose down -v
```

## Environment Variables

The compose file reads from a root `.env` file. `.env` is excluded from the Docker build context so secrets are never baked into images.

### Required

| Variable | Description |
|----------|-------------|
| `DB_ADMIN_PASSWORD` | PostgreSQL admin password |
| `DB_PASSWORD` | PostgreSQL app user password |
| `MINIO_ACCESS_KEY` | MinIO root user |
| `MINIO_SECRET_KEY` | MinIO root password |
| `PINECONE_API_KEY` | Pinecone vector database API key |

### LLM Providers

Set API keys for whichever providers you use:

| Variable | Provider |
|----------|----------|
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic |
| `GEMINI_API_KEY` | Google Gemini |
| `XAI_API_KEY` | xAI / Grok |

No provider env flags needed — model selection is name-driven. Pass model names directly (e.g. `gpt-4o-mini`, `claude-sonnet-4-20250514`, `gemini-2.0-flash`) or with explicit prefixes (`openai/gpt-4o-mini`). Defaults when omitted:

- **Chat:** `openai/gpt-5.4-mini`
- **Embeddings:** `openai/text-embedding-3-large`

### Embedding Dimensions

If you switch embedding models, ensure dimensions match:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DENSE_EMBEDDING_DIMENSION` | 3072 | Pinecone dense index |
| `DENSE_EMBEDDING_MODEL` | `text-embedding-3-large` | Dense retrieval embedding model |
| `SMALL_EMBEDDING_MODEL` | `text-embedding-3-small` | Redis semantic caches and memory embeddings |
| `SMALL_EMBEDDING_DIMENSION` | 1536 | Redis semantic caches and `user_memory_fact.embedding` |

### Auth

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | JWT signing secret |
| `AUTH_GOOGLE_ID` | Google OAuth client ID |
| `AUTH_GOOGLE_SECRET` | Google OAuth client secret |
| `FRONTEND_URL` | Frontend base URL used for OAuth callback redirects |
| `COOKIE_SECURE` | Set to `false` only for non-HTTPS local browser testing |
| `COOKIE_DOMAIN` | Optional cookie domain for production deployments |

Google OAuth should be configured with the frontend callback URL:

```text
${FRONTEND_URL}/api/auth/callback/google
```

The frontend callback forwards the returned `code` and `state` to the backend exchange endpoint at `/auth/google/callback`.

### API and Browser URLs

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | — | Browser-visible FastAPI base URL used by the frontend |
| `INTERNAL_API_URL` | `NEXT_PUBLIC_API_URL` fallback | Server-side FastAPI base URL for protected route SSR |
| `MINIO_PUBLIC_BASE_URL` | — | Browser-visible MinIO/S3 base URL for presigned upload/download URLs |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated browser origins allowed by FastAPI |
| `CORS_ALLOW_LOCALHOST_REGEX` | `true` | Allows any localhost/127.0.0.1 port in development |
| `ENABLE_API_DOCS` | `false` | Enables `/docs`, `/redoc`, and `/openapi.json` when set to `true` |

### Observability (optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_ENABLED` | `false` | Enable OpenTelemetry tracing |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | Tempo OTLP HTTP endpoint |
| `OBSERVABILITY_HASH_SALT` | — | Salt for hashed identity labels |
| `OBS_ENABLE_HIGH_CARDINALITY_METRICS` | `true` | Session-level token/spend counters |

### Ingestion

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCUMENT_INGEST_MODE` | `worker` | `worker` (ARQ via Redis) or `background` (asyncio fallback) |

## Local Development (without Docker)

### Backend

```bash
# Install dependencies
uv sync
uv run crawl4ai-setup  # headless browser for web crawling

# Run database migrations
uv run alembic upgrade head

# Start the API server
uv run uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
yarn install

# Start the dev server
yarn dev  # Next.js on :3000
```

### Database Setup

A single PostgreSQL instance stores everything, managed by SQLAlchemy + Alembic. Migrations run automatically on API startup, or manually with:

```bash
uv run alembic upgrade head
```

The `database/setup-reader.sh` script creates a read-only PostgreSQL user for the SQL query tool (prevents LLM-generated SQL from modifying data).

## After Dependency Changes

```bash
# Python
uv sync
uv run crawl4ai-setup

# Frontend
cd frontend && yarn install
```
