"""FastAPI server exposing the orchestrator as an API."""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
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
from api.health import router as health_router
from memory.semantic import _embed
from database.models import ChatSession, User, UserMemoryFact
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.core import get_db, engine as _db_engine
from api.auth.manager import current_active_user, get_user_manager
from api.chat_sessions import (
    router as chat_sessions_router,
    messages_router as chat_messages_router,
)
from api.rate_limit import rate_limit_middleware

from api.auth.manager import fastapi_users_app
from api.auth.config import auth_backend, google_oauth_client, SECRET
from api.auth.schemas import UserRead, UserCreate, UserUpdate
from api.auth.manager import UserManager

from observability.logging_config import setup_logging
from observability.tracing import setup_tracing

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — nothing special needed (connections are lazy)
    yield
    # Shutdown — clean up connections
    await _db_engine.dispose()
    from memory.redis_client import redis_client

    redis_client.close()


app = FastAPI(title="AgenticRAG", version="0.1.0", lifespan=lifespan)

setup_tracing(app)

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


def _metrics_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return request.url.path


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _serialize_memory_fact(fact: UserMemoryFact) -> dict:
    return {
        "id": fact.id,
        "text": fact.text,
        "observed_at": fact.observed_at.isoformat(),
        "source_session_id": fact.source_session_id,
    }


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


app.middleware("http")(rate_limit_middleware)

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
# In dev, also match any localhost port. Disable in prod by not setting this var.
_cors_localhost_regex = (
    r"https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    if os.getenv("CORS_ALLOW_LOCALHOST_REGEX", "true").lower() == "true"
    else None
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_origin_regex=_cors_localhost_regex,
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
        redirect_url=f"{FRONTEND_URL}/api/auth/callback/google",
    ),
    prefix="/auth/google",
    tags=["auth"],
)

app.include_router(
    fastapi_users_app.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

app.include_router(health_router)
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


class MemoryFactCreate(BaseModel):
    text: str


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
async def get_chat_memory(
    user=Depends(current_active_user), db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(UserMemoryFact)
        .where(
            UserMemoryFact.user_id == user.id,
            UserMemoryFact.superseded_at.is_(None),
        )
        .order_by(UserMemoryFact.observed_at.desc(), UserMemoryFact.id.desc())
    )
    facts = (await db.execute(stmt)).scalars().all()
    return {"facts": [_serialize_memory_fact(fact) for fact in facts]}


@app.post("/chat/memory")
async def create_chat_memory_fact(
    data: MemoryFactCreate,
    user=Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    text = data.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Memory text cannot be empty")

    existing_stmt = select(UserMemoryFact).where(
        UserMemoryFact.user_id == user.id,
        UserMemoryFact.text == text,
        UserMemoryFact.superseded_at.is_(None),
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        return _serialize_memory_fact(existing)

    embedding = await asyncio.to_thread(_embed, text)
    fact = UserMemoryFact(
        user_id=user.id,
        text=text,
        embedding=embedding,
        observed_at=_utc_now_naive(),
        source_session_id="manual-memory",
    )
    db.add(fact)
    await db.commit()
    await db.refresh(fact)
    return _serialize_memory_fact(fact)


@app.delete("/chat/memory/{fact_id}")
async def delete_chat_memory_fact(
    fact_id: str,
    user=Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserMemoryFact).where(
        UserMemoryFact.id == fact_id,
        UserMemoryFact.user_id == user.id,
        UserMemoryFact.superseded_at.is_(None),
    )
    fact = (await db.execute(stmt)).scalar_one_or_none()
    if not fact:
        raise HTTPException(status_code=404, detail="Memory fact not found")

    fact.superseded_at = _utc_now_naive()
    await db.commit()
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
