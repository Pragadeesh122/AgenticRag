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
- OpenAI, Pinecone, and Google OAuth remain external services and still need valid credentials in `.env`.
- Document ingestion defaults to the ARQ worker through Redis. For a no-worker fallback, set `DOCUMENT_INGEST_MODE=background`.
