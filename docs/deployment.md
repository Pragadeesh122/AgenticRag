# Deployment

## Docker Compose

The full stack is defined in `compose.yml`. All services start with a single command:

```bash
docker compose up
```

### Service Dependencies

```
postgres (healthy) ─┐
redis (healthy) ────┤
minio (healthy) ────┤
                    ├── minio-setup (completed) ─── api ─── frontend
                    │                            └── worker
                    │
prometheus ─────────┤
loki ── promtail    ├── grafana
tempo ──────────────┘
```

Health checks ensure services start in the correct order:
- **postgres** — `pg_isready` check every 5s
- **redis** — `redis-cli ping` every 5s
- **minio** — TCP check on port 9000
- **minio-setup** — must complete (creates bucket and attempts CORS config) before API starts

### Secrets

The `.env` file is read at runtime by Docker Compose but is excluded from the Docker build context (via `.dockerignore`). Secrets are never baked into images.

Required secrets: `DB_ADMIN_PASSWORD`, `DB_PASSWORD`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `PINECONE_API_KEY`, plus at least one LLM provider API key.

### Database Migrations

Both the API and worker run `uv run alembic upgrade head` on startup. The first container to start handles schema creation. Subsequent containers see the migration is already applied and proceed.

### MinIO Setup

The `minio-setup` init container:
1. Waits for MinIO to accept connections
2. Creates the `agenticrag-documents` bucket
3. Tries to apply CORS configuration from `minio/cors.xml`

Some MinIO builds return `NotImplemented` for bucket CORS. In that case the setup container logs the failure and continues so the rest of the stack can still start.

### Volumes

| Volume | Purpose |
|--------|---------|
| `postgres_data` | Database persistence |
| `redis_data` | Redis persistence (sessions, memory, cache) |
| `minio_data` | Uploaded document files |
| `frontend_node_modules` | Cached node_modules for dev |
| `prometheus_data` | Metric storage |
| `loki_data` | Log storage |
| `tempo_data` | Trace storage |
| `grafana_data` | Dashboard state |

## Scaling

- **API** — stateless (session state is in Redis). Can run multiple instances behind a load balancer.
- **Worker** — stateless ARQ worker. Scale by running additional instances.
- **Frontend** — stateless Next.js. Can run multiple instances.
- **Redis** — single instance. Consider Redis Cluster for high availability.
- **PostgreSQL** — single instance. Consider read replicas for scale.

## Monitoring Setup

### Prometheus

Prometheus scrapes the API's `/metrics` endpoint. Config at `monitoring/prometheus/prometheus.yml`.

The API exposes both standard HTTP metrics and custom AgenticRAG metrics (LLM, tools, agents, orchestration). See [Observability](architecture/observability.md) for the full metrics catalog.

### Loki + Promtail

Promtail scrapes Docker container logs via the Docker socket and ships them to Loki. The app currently writes plain container stdout/stderr logs rather than structured JSON.

Config files:
- `monitoring/promtail/promtail-config.yml`
- `monitoring/loki/loki-config.yml`

### Tempo

OpenTelemetry traces are exported via OTLP HTTP to Tempo on port 4318. Enable with `OTEL_ENABLED=true`.

Config: `monitoring/tempo/tempo-config.yml`

### Grafana

Grafana is pre-provisioned with:
- **Datasources** — Prometheus, Loki, and Tempo (auto-configured)
- **Dashboards** — Economics, Agentic Ops, UX & Latency
- **Alert rules** — pre-configured rules (contact points must be set manually)

Default login on a fresh Grafana volume: `admin`/`admin` (configurable via `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD`). If the `grafana_data` volume already exists, Grafana keeps the previously stored admin password instead of reapplying the env defaults.

## Rebuild

Only rebuild when dependencies or Dockerfiles change:

```bash
docker compose up --build
```

## Reset

Remove all volumes and start fresh:

```bash
docker compose down -v
```
