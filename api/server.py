"""FastAPI server exposing the orchestrator as an API."""

import logging
import re
import time
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from api.session import (
    create_session,
    delete_session,
    restore_session,
    session_exists,
    session_owned_by_user,
)
from api.chat import chat_stream
from api.projects import router as projects_router
from memory.semantic import _memory_key
from memory.redis_client import redis_client
from database.models import ChatSession, UserMemory, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.core import get_db
from api.auth.manager import current_active_user, get_user_manager
from api.chat_sessions import router as chat_sessions_router, messages_router as chat_messages_router

import os
from api.auth.manager import fastapi_users_app
from api.auth.config import auth_backend, google_oauth_client, SECRET
from api.auth.schemas import UserRead, UserCreate, UserUpdate
from api.auth.manager import UserManager

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

app = FastAPI(title="AgenticRAG", version="0.1.0")

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests.",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

RATE_LIMIT_RULES = (
    {
        "name": "auth_login",
        "method": "POST",
        "pattern": re.compile(r"^/auth/login$"),
        "limit": 5,
        "window": 60,
    },
    {
        "name": "auth_register",
        "method": "POST",
        "pattern": re.compile(r"^/auth/register$"),
        "limit": 5,
        "window": 60,
    },
    {
        "name": "chat_stream",
        "method": "POST",
        "pattern": re.compile(r"^/chat/stream$"),
        "limit": 20,
        "window": 60,
    },
    {
        "name": "project_chat",
        "method": "POST",
        "pattern": re.compile(r"^/projects/[^/]+/chat$"),
        "limit": 20,
        "window": 60,
    },
    {
        "name": "project_upload_init",
        "method": "POST",
        "pattern": re.compile(r"^/projects/[^/]+/upload$"),
        "limit": 20,
        "window": 60,
    },
    {
        "name": "project_upload_confirm",
        "method": "PUT",
        "pattern": re.compile(r"^/projects/[^/]+/upload$"),
        "limit": 30,
        "window": 60,
    },
)
_RATE_LIMIT_FALLBACK: dict[str, tuple[float, int]] = {}


def _metrics_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return request.url.path


def _match_rate_limit_rule(request: Request) -> dict | None:
    path = request.url.path
    method = request.method.upper()
    for rule in RATE_LIMIT_RULES:
        if rule["method"] == method and rule["pattern"].match(path):
            return rule
    return None


def _rate_limit_subject(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _consume_rate_limit(rule: dict, subject: str) -> tuple[bool, int, int]:
    key = f"ratelimit:{rule['name']}:{subject}"
    now = time.time()

    try:
        count = int(redis_client.incr(key))
        if count == 1:
            redis_client.expire(key, rule["window"])
        ttl = max(int(redis_client.ttl(key) or rule["window"]), 1)
    except Exception:
        expires_at, count = _RATE_LIMIT_FALLBACK.get(key, (0.0, 0))
        if expires_at <= now:
            expires_at = now + rule["window"]
            count = 0
        count += 1
        _RATE_LIMIT_FALLBACK[key] = (expires_at, count)
        ttl = max(int(expires_at - now), 1)

    remaining = max(rule["limit"] - count, 0)
    return count <= rule["limit"], remaining, ttl


@app.middleware("http")
async def _prometheus_http_middleware(request: Request, call_next):
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        path = _metrics_path(request)
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=path,
            status_code=str(status_code),
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            path=path,
        ).observe(time.perf_counter() - start)


@app.middleware("http")
async def _rate_limit_middleware(request: Request, call_next):
    rule = _match_rate_limit_rule(request)
    if rule is None:
        return await call_next(request)

    allowed, remaining, retry_after = _consume_rate_limit(
        rule,
        _rate_limit_subject(request),
    )
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(rule["limit"]),
                "X-RateLimit-Remaining": "0",
            },
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(rule["limit"])
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Auth Routers
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.include_router(
    fastapi_users_app.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users_app.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users_app.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users_app.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users_app.get_oauth_router(
        google_oauth_client, 
        auth_backend, 
        SECRET,
        associate_by_email=True,
        redirect_url=f"{FRONTEND_URL}/api/auth/callback/google"
    ),
    prefix="/auth/google",
    tags=["auth"],
)

app.include_router(
    fastapi_users_app.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

app.include_router(projects_router)
app.include_router(chat_sessions_router)
app.include_router(chat_messages_router)


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


class ChatRequest(BaseModel):
    sessionId: str
    message: str


class RestoreRequest(BaseModel):
    session_id: str
    messages: list[dict]
    project_name: str | None = None


class MemoryUpdateData(BaseModel):
    category: str
    content: str


class ChangePasswordData(BaseModel):
    current_password: str
    new_password: str

@app.post("/chat/backend-session")
def new_session(user: User = Depends(current_active_user)):
    """Create a new conversational orchestrator session."""
    session_id = create_session(str(user.id))
    return {"session_id": session_id}


@app.post("/chat/stream")
def chat(req: ChatRequest, user: User = Depends(current_active_user)):
    """Send a message and receive an SSE stream of tokens."""
    if not session_owned_by_user(req.sessionId, str(user.id)):
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        return StreamingResponse(
            chat_stream(req.sessionId, req.message),
            media_type="text/event-stream",
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/session/{session_id}/exists")
def check_session(session_id: str, user: User = Depends(current_active_user)):
    """Check if a session exists in Redis."""
    return {"exists": session_owned_by_user(session_id, str(user.id))}


@app.post("/session/restore")
async def restore(
    req: RestoreRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore a Redis session from persisted messages."""
    if session_exists(req.session_id):
        if not session_owned_by_user(req.session_id, str(user.id)):
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        stmt = select(ChatSession).where(
            ChatSession.user_id == user.id,
            ChatSession.backend_session_id == req.session_id,
        )
        owned_session = (await db.execute(stmt)).scalar_one_or_none()
        if not owned_session:
            raise HTTPException(status_code=404, detail="Session not found")

    restore_session(
        req.session_id,
        req.messages,
        str(user.id),
        req.project_name or "",
    )
    return {"status": "restored", "session_id": req.session_id}


@app.delete("/chat/backend-session/{session_id}")
def remove_session(session_id: str, user: User = Depends(current_active_user)):
    """Delete the session from Redis."""
    if not session_owned_by_user(session_id, str(user.id)):
        raise HTTPException(status_code=404, detail="Session not found")
    delete_session(session_id)
    return {"status": "deleted"}


@app.get("/chat/memory")
async def get_chat_memory(user=Depends(current_active_user), db: AsyncSession = Depends(get_db)):
    stmt = select(UserMemory).where(UserMemory.user_id == user.id)
    memory = (await db.execute(stmt)).scalar_one_or_none()
    if not memory:
        return {"work_context": "", "personal_context": "", "top_of_mind": "", "preferences": ""}
    return {
        "work_context": memory.work_context or "",
        "personal_context": memory.personal_context or "",
        "top_of_mind": memory.top_of_mind or "",
        "preferences": memory.preferences or ""
    }


@app.put("/chat/memory")
async def update_chat_memory(data: MemoryUpdateData, user=Depends(current_active_user), db: AsyncSession = Depends(get_db)):
    stmt = select(UserMemory).where(UserMemory.user_id == user.id)
    memory = (await db.execute(stmt)).scalar_one_or_none()
    if not memory:
        # Create
        memory = UserMemory(user_id=user.id)
        db.add(memory)
    
    cat = data.category
    # Map TS camelCase or snake_case if necessary, assume snake given frontend types usually sync.
    if hasattr(memory, cat):
        setattr(memory, cat, data.content)
        await db.commit()
        # Also sync to Redis
        key = _memory_key(str(user.id))
        if data.content.strip():
            redis_client.hset(key, cat, data.content.strip())
        else:
            redis_client.hdel(key, cat)
            
    return {"status": "ok"}


@app.post("/auth/change-password")
async def change_password(
    data: ChangePasswordData,
    user: User = Depends(current_active_user),
    manager: UserManager = Depends(get_user_manager),
):
    if not user.hashed_password:
        raise HTTPException(
            status_code=400,
            detail="Password changes are unavailable for OAuth-only accounts",
        )

    verified, _ = manager.password_helper.verify_and_update(
        data.current_password,
        user.hashed_password,
    )
    if not verified:
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    await manager.validate_password(data.new_password, user)
    next_hash = manager.password_helper.hash(data.new_password)
    await manager.user_db.update(user, {"hashed_password": next_hash})
    return {"status": "ok"}
