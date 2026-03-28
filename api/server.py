"""FastAPI server exposing the orchestrator as an API."""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.session import create_session, delete_session
from api.chat import chat_stream, end_session_with_memory
from api.projects import router as projects_router

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

app = FastAPI(title="AgenticRAG", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.post("/session")
def new_session():
    """Create a new conversation session."""
    session_id = create_session()
    return {"session_id": session_id}


@app.post("/chat")
def chat(req: ChatRequest):
    """Send a message and receive an SSE stream of tokens."""
    try:
        return StreamingResponse(
            chat_stream(req.session_id, req.message),
            media_type="text/event-stream",
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")


@app.delete("/session/{session_id}")
def remove_session(session_id: str):
    """Extract memories and delete the session."""
    end_session_with_memory(session_id)
    delete_session(session_id)
    return {"status": "deleted"}
