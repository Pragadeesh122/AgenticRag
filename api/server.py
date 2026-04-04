"""FastAPI server exposing the orchestrator as an API."""

import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.session import create_session, delete_session, restore_session, session_exists
from api.chat import chat_stream
from api.projects import router as projects_router
from memory.semantic import MEMORY_KEY_PREFIX, MEMORY_CATEGORIES, _memory_key
from memory.redis_client import redis_client
from database.models import UserMemory, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.core import get_db
from api.auth.manager import current_active_user
from api.chat_sessions import router as chat_sessions_router, messages_router as chat_messages_router

import os
from api.auth.manager import fastapi_users_app
from api.auth.config import auth_backend, google_oauth_client, SECRET
from api.auth.schemas import UserRead, UserUpdate

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

app = FastAPI(title="AgenticRAG", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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


class ChatRequest(BaseModel):
    sessionId: str
    message: str


class RestoreRequest(BaseModel):
    session_id: str
    messages: list[dict]


class MemoryEntry(BaseModel):
    category: str
    content: str


class MemorySyncRequest(BaseModel):
    user_id: str
    memories: list[MemoryEntry]

class MemoryUpdateData(BaseModel):
    category: str
    content: str

@app.post("/chat/backend-session")
def new_session(user: User = Depends(current_active_user)):
    """Create a new conversational orchestrator session."""
    session_id = create_session(str(user.id))
    return {"session_id": session_id}


@app.post("/chat/stream")
def chat(req: ChatRequest):
    """Send a message and receive an SSE stream of tokens."""
    try:
        return StreamingResponse(
            chat_stream(req.sessionId, req.message),
            media_type="text/event-stream",
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/session/{session_id}/exists")
def check_session(session_id: str):
    """Check if a session exists in Redis."""
    return {"exists": session_exists(session_id)}


@app.post("/session/restore")
def restore(req: RestoreRequest):
    """Restore a Redis session from persisted messages."""
    restore_session(req.session_id, req.messages)
    return {"status": "restored", "session_id": req.session_id}


@app.delete("/chat/backend-session/{session_id}")
def remove_session(session_id: str):
    """Delete the session from Redis."""
    delete_session(session_id)
    return {"status": "deleted"}


# ─── Memory (Redis cache — DB is source of truth in Next.js) ───


@app.get("/memory/{user_id}")
def get_memory_redis(user_id: str):
    """Return all user memory categories from Redis cache."""
    key = _memory_key(user_id)
    facts = redis_client.hgetall(key)
    return {cat: facts.get(cat, "") for cat in MEMORY_CATEGORIES}


@app.post("/memory/sync")
def sync_memory(req: MemorySyncRequest):
    """Sync memory from DB to Redis cache. Called by Next.js after DB writes."""
    key = _memory_key(req.user_id)
    redis_client.delete(key)
    for entry in req.memories:
        if entry.category in MEMORY_CATEGORIES and entry.content.strip():
            redis_client.hset(key, entry.category, entry.content.strip())
    return {"status": "synced", "count": len(req.memories)}


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
