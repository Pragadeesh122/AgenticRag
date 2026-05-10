# API Reference

## Related Backend Docs

- [Agents](agents.md) — agent discovery, routing, and agent responsibilities
- [RAG Pipeline](pipeline.md) — document ingestion, chunking, embeddings, retrieval
- [Tools](tools.md) — tool schemas, execution model, planner integration, caching

## Authentication

FastAPI-Users with cookie-based JWT. The auth cookie (`app_token`) is set as `httponly`, `secure`, `samesite=lax` with a 7-day lifetime.

### Auth Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | No | Email/password login, sets JWT cookie |
| POST | `/auth/logout` | Yes | Clears JWT cookie |
| POST | `/auth/register` | No | Create account with email/password |
| POST | `/auth/forgot-password` | No | Request a password reset token |
| POST | `/auth/reset-password` | No | Reset password with token |
| POST | `/auth/verify` | No | Verify email with token |
| GET | `/auth/google/authorize` | No | Start Google OAuth flow |
| GET | `/auth/google/callback` | No | Backend OAuth exchange endpoint used by the frontend callback |
| POST | `/auth/change-password` | Yes | Change password (email/password accounts only) |
| GET | `/users/me` | Yes | Get current user |
| PATCH | `/users/me` | Yes | Update current user |

Current local-development behavior:
- password reset and verification tokens are logged by the backend
- no email delivery service is wired in this repo by default
- Google should redirect to `${FRONTEND_URL}/api/auth/callback/google`; that frontend callback forwards `code` and `state` to `/auth/google/callback`

## Chat

### Session Management

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/chat/backend-session` | Yes | Create a new Redis session |
| DELETE | `/chat/backend-session/{id}` | Yes | Delete a Redis session |
| GET | `/session/{id}/exists` | Yes | Check if session exists and is owned by user |
| POST | `/session/restore` | Yes | Restore Redis session from persisted messages |

**POST `/chat/backend-session`** response:
```json
{"session_id": "a1b2c3d4e5f6"}
```

**POST `/session/restore`** request:
```json
{
  "session_id": "a1b2c3d4e5f6",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "project_name": null
}
```

### Streaming Chat

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/chat/stream` | Yes | SSE stream for general chat |

**Request:**
```json
{"sessionId": "a1b2c3d4e5f6", "message": "What is...", "attachments": []}
```

**Response:** Server-Sent Events stream. See [Streaming](../frontend/streaming.md) for event types.

### General Chat Attachments

General chat supports direct-to-MinIO attachment uploads. Images are passed to the LLM as presigned image URLs. PDFs are sent as native file blocks when accepted by the token limit. TXT, MD, CSV, and DOCX files are text-extracted and inlined into the LLM message.

Limits enforced by both frontend and backend:

| Limit | Value |
|-------|-------|
| Files per message | 5 |
| Files per chat session | 10 |
| File size | 20 MB |
| Total session attachment bytes | 20 MB |
| Tokens per document | 25,000 |
| Total attachment tokens per session | 25,000 |

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/chat/upload` | Yes | Create a chat attachment ref and presigned PUT URL |
| GET | `/chat/attachments/url?key=...` | Yes | Get a short-lived presigned GET URL for preview/download |

**POST `/chat/upload`** request:
```json
{"filename": "notes.pdf", "fileSize": 1048576, "mimeType": "application/pdf"}
```

The returned `storageKey` is scoped under `chat/{user_id}/...`; `/chat/stream` rejects attachments outside the caller's prefix.

### Persisted Chat History

These endpoints manage durable chat sessions and messages stored in PostgreSQL.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/chat/sessions` | Yes | List general chat sessions |
| POST | `/chat/sessions` | Yes | Create a general chat session row |
| PATCH | `/chat/sessions/{id}` | Yes | Update title or backend session ID |
| DELETE | `/chat/sessions/{id}` | Yes | Delete a general chat session row |
| GET | `/chat/sessions/{id}/messages` | Yes | Load persisted messages for a session |
| POST | `/chat/sessions/{id}/messages` | Yes | Persist streamed user + assistant messages |
| GET | `/chat/sessions/{id}/export` | Yes | Export the session as Markdown |
| PATCH | `/chat/messages/{id}` | Yes | Update message metadata (quiz state, agent name, parts) |

### Memory

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/chat/memory` | Yes | List active atomic memory facts |
| POST | `/chat/memory` | Yes | Add one manual atomic memory fact |
| DELETE | `/chat/memory/{fact_id}` | Yes | Supersede one active memory fact |

**POST `/chat/memory`** request:
```json
{"text": "Prefers concise explanations"}
```

Memory is stored in `user_memory_fact`; the old four-category `user_memory` table is legacy compatibility, not the primary API.

## Projects

### Project CRUD

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/projects` | Yes | List user's projects |
| POST | `/projects` | Yes | Create a project |
| GET | `/projects/{id}` | Yes | Get project with documents |
| PATCH | `/projects/{id}` | Yes | Update project name/description/status |
| DELETE | `/projects/{id}` | Yes | Delete project and all documents |
| GET | `/projects/agents` | Yes | List available agents |

**POST `/projects`** request:
```json
{"name": "My Project", "description": "Optional description"}
```

### Document Upload

Three-step presigned URL flow:

1. **Init** — create a DB record and get a presigned PUT URL
2. **Upload** — the browser PUTs the file directly to MinIO using the presigned URL
3. **Confirm** — trigger background ingestion

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/projects/{id}/upload` | Yes | Init: create document record + presigned URL |
| PUT | `/projects/{id}/upload` | Yes | Confirm: trigger ingestion |
| GET | `/projects/{id}/documents` | Yes | List project documents |
| DELETE | `/projects/{id}/documents/{doc_id}` | Yes | Delete a document |
| GET | `/projects/{id}/documents/{doc_id}/status` | Yes | Poll ingestion status |
| GET | `/projects/{id}/documents/{doc_id}/download` | Yes | Get presigned download URL |
| PATCH | `/projects/{id}/documents/{doc_id}/reingest` | Yes | Re-upload and re-ingest a document |

**POST `/projects/{id}/upload`** request:
```json
{"filename": "paper.pdf", "fileSize": 1048576}
```

Response includes `uploadUrl` (presigned MinIO PUT URL) and document metadata.

**PUT `/projects/{id}/upload`** request:
```json
{"documentId": "doc_abc123", "filename": "paper.pdf"}
```

Supported file types: `pdf`, `txt`, `md`, `csv`, `docx`

**Document status values:** `pending` → `processing` → `ready` | `failed`

### Project Search

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/projects/{id}/search` | Yes | Search project documents (vector similarity) |

**Request:**
```json
{"query": "revenue growth", "limit": 5}
```

### Project Chat

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/projects/{id}/chat` | Yes | SSE stream for project chat |
| POST | `/projects/{id}/session` | Yes | Create project chat session |
| DELETE | `/projects/{id}/session/{session_id}` | Yes | Delete project chat session |
| GET | `/projects/{id}/sessions` | Yes | List project chat sessions |

**POST `/projects/{id}/chat`** request:
```json
{
  "sessionId": "a1b2c3d4e5f6",
  "message": "Summarize the key findings",
  "agent": "summary"
}
```

## Metrics

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/metrics` | No | Prometheus metrics endpoint; rejects public proxy-forwarded requests |

## Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Liveness probe |
| GET | `/ready` | No | Readiness probe for PostgreSQL, Redis, and MinIO connectivity |

## OpenAPI Docs

FastAPI's generated docs are disabled by default. Set `ENABLE_API_DOCS=true` to expose `/docs`, `/redoc`, and `/openapi.json`.

## Rate Limits

Sliding window algorithm (Redis sorted set + Lua script, with in-memory deque fallback).

| Rule | Method | Pattern | Limit | Window |
|------|--------|---------|-------|--------|
| `auth_login` | POST | `/auth/login` | 5 | 60s |
| `auth_register` | POST | `/auth/register` | 5 | 60s |
| `chat_stream` | POST | `/chat/stream` | 20 | 60s |
| `project_chat` | POST | `/projects/*/chat` | 20 | 60s |
| `project_upload_init` | POST | `/projects/*/upload` | 20 | 60s |
| `project_upload_confirm` | PUT | `/projects/*/upload` | 30 | 60s |

Rate limit subject: user ID (from JWT cookie) with IP fallback for unauthenticated requests.

Response headers on all rate-limited endpoints:
- `X-RateLimit-Limit` — max requests in window
- `X-RateLimit-Remaining` — requests remaining
- `Retry-After` — seconds until reset (only on 429)

## SSE Event Types

Both `/chat/stream` and `/projects/{id}/chat` return SSE streams:

| Event | Data format | Description |
|-------|-------------|-------------|
| `token` | Raw text | Streamed text chunk |
| `tool` | `{"name": "search", "args": {"query": "..."}}` | Tool call started |
| `thinking` | `{"content": "Searching for..."}` | Reasoning step or result summary |
| `agent` | `{"name": "reasoning", "description": "..."}` | Agent selected (project chat) |
| `retrieval` | `{"sources": [...], "count": 5}` | Documents retrieved (project chat) |
| `error` | Error message string | Error occurred |
| `done` | `{"tools_used": [...], "prompt_tokens": 1234}` | Turn complete |

## CORS

Allowed origins come from `CORS_ALLOWED_ORIGINS` (default `http://localhost:3000`). In development, `CORS_ALLOW_LOCALHOST_REGEX=true` also allows regex matches for `https?://(localhost|127\.0\.0\.1)(:\d+)?`.

Credentials are allowed (cookies).

## See Also

- [Agents](agents.md)
- [RAG Pipeline](pipeline.md)
- [Tools](tools.md)
