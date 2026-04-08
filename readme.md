# AgenticRAG

Run the full local stack with Docker Compose:

```bash
docker compose up
```

Rebuild only when dependencies or Dockerfiles change:

```bash
docker compose up --build
```

This starts:

- `frontend` on `http://localhost:3000`
- `api` on `http://localhost:8000`
- `worker` for document ingestion jobs
- `postgres` on `localhost:5432`
- `redis` on `localhost:6379`
- `redisinsight` on `http://localhost:8001`
- `minio` on `http://localhost:9000`
- MinIO console on `http://localhost:9001`

Stop everything with:

```bash
docker compose down
```

Reset local state with:

```bash
docker compose down -v
```

Notes:

- The compose file reads secrets and API keys from the root `.env`.
- `.env` is excluded from the Docker build context so secrets are not baked into images.
- LLM selection is model-driven (no required provider env flags):
  - Pass model names directly to calls (`gpt-4o-mini`, `claude-...`, `gemini-...`, `grok-...`).
  - You can also use explicit provider prefixes (`openai/gpt-4o-mini`, `anthropic/claude-...`).
  - If model is omitted, fallback defaults are used:
    - chat: `openai/gpt-4o-mini`
    - embeddings: `openai/text-embedding-3-large`
- If you switch embedding models/providers, ensure vector dimensions match:
  - `DENSE_EMBEDDING_DIMENSION` for Pinecone dense index
  - `SMALL_EMBEDDING_DIMENSION` for Redis semantic caches
- Document ingestion defaults to the ARQ worker through Redis. For a no-worker fallback, set `DOCUMENT_INGEST_MODE=background`.
- If you run the backend outside Docker after changing Python dependencies, run:
  - `uv sync`
  - `uv run crawl4ai-setup`
