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
| GET | `/auth/google/callback` | No | Google OAuth callback |
| POST | `/auth/change-password` | Yes | Change password (email/password accounts only) |
| GET | `/users/me` | Yes | Get current user |
| PATCH | `/users/me` | Yes | Update current user |

Current local-development behavior:
- password reset and verification tokens are logged by the backend
- no email delivery service is wired in this repo by default

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
{"sessionId": "a1b2c3d4e5f6", "message": "What is..."}
```

**Response:** Server-Sent Events stream. See [Streaming](../frontend/streaming.md) for event types.

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
| GET | `/chat/memory` | Yes | Get user's stored memory (all 4 categories) |
| PUT | `/chat/memory` | Yes | Update a single memory category |

**PUT `/chat/memory`** request:
```json
{"category": "work_context", "content": "Senior engineer at..."}
```

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
| GET | `/metrics` | No | Prometheus metrics endpoint |

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

Allowed origins: `http://localhost:3000`, `http://127.0.0.1:3000`, plus regex matching `https?://(localhost|127\.0\.0\.1)(:\d+)?`.

Credentials are allowed (cookies).

## See Also

- [Agents](agents.md)
- [RAG Pipeline](pipeline.md)
- [Tools](tools.md)
