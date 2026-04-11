import json
import re
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Response

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.core import get_db
from database.models import ChatSession, ChatMessage, User
from api.auth.manager import current_active_user

router = APIRouter(prefix="/chat/sessions", tags=["chat_sessions"])
messages_router = APIRouter(prefix="/chat/messages", tags=["chat_messages"])


# --- Schemas ---
class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New chat"
    project_id: Optional[str] = None


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    backendSessionId: Optional[str] = None


class MessageCreate(BaseModel):
    role: str
    content: str
    toolCalls: Optional[list] = None
    parts: Optional[list] = None
    status: Optional[dict] = None
    thinkingEntries: Optional[list] = None
    sources: Optional[list] = None
    agentName: Optional[str] = None
    metadata: Optional[dict] = None


class MessageUpdate(BaseModel):
    metadata: Optional[dict] = None


class SessionResponse(BaseModel):
    id: str
    projectId: Optional[str] = None
    backendSessionId: Optional[str] = None
    title: str
    createdAt: str
    updatedAt: str

    @classmethod
    def from_orm(cls, obj: ChatSession):
        return cls(
            id=obj.id,
            projectId=obj.project_id,
            backendSessionId=obj.backend_session_id,
            title=obj.title,
            createdAt=obj.created_at.isoformat(),
            updatedAt=obj.updated_at.isoformat(),
        )


def _export_filename(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (title or "chat-session")).strip("-").lower()
    return f"{slug or 'chat-session'}.md"


def _render_tool_calls(tool_calls: list | None, metadata: dict) -> str:
    parts = metadata.get("parts") or []
    rows: list[str] = []
    seen: set[str] = set()

    for part in parts:
        if part.get("type") != "tool-call":
            continue
        key = str(part.get("toolCallId") or part.get("toolName") or len(rows))
        if key in seen:
            continue
        seen.add(key)
        args = part.get("args")
        args_text = part.get("argsText")
        if not args_text and isinstance(args, dict):
            args_text = json.dumps(args, sort_keys=True)
        rows.append(f"- `{part.get('toolName', 'tool')}` {args_text or ''}".rstrip())

    if not rows:
        for index, tool_call in enumerate(tool_calls or []):
            key = str(tool_call.get("id") or index)
            if key in seen:
                continue
            seen.add(key)
            args = tool_call.get("args") if isinstance(tool_call, dict) else None
            args_text = json.dumps(args or {}, sort_keys=True)
            rows.append(
                f"- `{tool_call.get('name', 'tool')}` {args_text}".rstrip()
            )

    if not rows:
        return ""
    return "### Tool Calls\n" + "\n".join(rows)


def _render_sources(metadata: dict) -> str:
    sources = metadata.get("sources") or []
    if not sources:
        return ""

    rows = []
    for source in sources:
        label = f"`{source.get('source', 'Unknown source')}`"
        details: list[str] = []
        if source.get("page") is not None:
            details.append(f"page {source['page']}")
        if source.get("score") is not None:
            details.append(f"score {float(source['score']):.2f}")
        suffix = f" ({', '.join(details)})" if details else ""
        rows.append(f"- {label}{suffix}")

    return "### Sources\n" + "\n".join(rows)


def _render_markdown_export(session: ChatSession, messages: list[ChatMessage]) -> str:
    sections = [f"# {session.title or 'New chat'}"]
    if session.project_id:
        sections.append(f"_Project session: `{session.project_id}`_")

    for index, message in enumerate(messages, start=1):
        role_label = "User" if message.role == "user" else "Assistant"
        body = (message.content or "").strip() or "_No content stored._"
        metadata = message.metadata_ or {}

        parts = [f"## {index}. {role_label}", body]
        tool_section = _render_tool_calls(message.tool_calls, metadata)
        if tool_section:
            parts.append(tool_section)
        source_section = _render_sources(metadata)
        if source_section:
            parts.append(source_section)
        sections.append("\n\n".join(parts))

    return "\n\n".join(sections).strip() + "\n"


# --- Routes ---
@router.get("", response_model=List[dict])
async def get_sessions(
    user: User = Depends(current_active_user), db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user.id, ChatSession.project_id.is_(None))
        .order_by(ChatSession.updated_at.desc())
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return [SessionResponse.from_orm(s).dict() for s in sessions]


@router.post("", response_model=dict)
async def create_session(
    data: ChatSessionCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid

    new_id = str(uuid.uuid4())
    session = ChatSession(
        id=new_id,
        user_id=user.id,
        title=data.title or "New chat",
        project_id=data.project_id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionResponse.from_orm(session).dict()


@router.patch("/{session_id}")
async def update_session(
    session_id: str,
    data: ChatSessionUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChatSession).where(
        ChatSession.id == session_id, ChatSession.user_id == user.id
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if data.title is not None:
        session.title = data.title
    if data.backendSessionId is not None:
        session.backend_session_id = data.backendSessionId

    await db.commit()
    return {"status": "ok"}


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChatSession).where(
        ChatSession.id == session_id, ChatSession.user_id == user.id
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Not found")

    backend_id = session.backend_session_id
    await db.delete(session)
    await db.commit()
    return {"backendSessionId": backend_id}


@router.get("/{session_id}/messages")
async def get_messages(
    session_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChatSession).where(
        ChatSession.id == session_id, ChatSession.user_id == user.id
    )
    session = (await db.execute(stmt)).scalar_one_or_none()
    if not session:
        return []

    stmt = (
        select(ChatMessage)
        .where(ChatMessage.chat_session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    msgs = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "toolCalls": m.tool_calls,
            "parts": (m.metadata_ or {}).get("parts"),
            "status": (m.metadata_ or {}).get("status"),
            "thinkingEntries": (m.metadata_ or {}).get("thinkingEntries"),
            "sources": (m.metadata_ or {}).get("sources"),
            "metadata": m.metadata_,
            "agentName": (m.metadata_ or {}).get("agentName"),
            "createdAt": m.created_at.isoformat(),
        }
        for m in msgs
    ]


@router.get("/{session_id}/export")
async def export_session(
    session_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == user.id,
    )
    session = (await db.execute(stmt)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages_stmt = (
        select(ChatMessage)
        .where(ChatMessage.chat_session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = (await db.execute(messages_stmt)).scalars().all()

    markdown = _render_markdown_export(session, messages)
    filename = _export_filename(session.title)
    return Response(
        content=markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{session_id}/messages")
async def save_messages(
    session_id: str,
    messages: List[MessageCreate],
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChatSession).where(
        ChatSession.id == session_id, ChatSession.user_id == user.id
    )
    session = (await db.execute(stmt)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Not found")

    import uuid

    new_msgs = []
    for msg in messages:
        metadata = dict(msg.metadata or {})
        if msg.parts is not None:
            metadata["parts"] = msg.parts
        if msg.status is not None:
            metadata["status"] = msg.status
        if msg.thinkingEntries is not None:
            metadata["thinkingEntries"] = msg.thinkingEntries
        if msg.sources is not None:
            metadata["sources"] = msg.sources
        if msg.agentName is not None:
            metadata["agentName"] = msg.agentName

        cm = ChatMessage(
            id=str(uuid.uuid4()),
            chat_session_id=session_id,
            role=msg.role,
            content=msg.content,
            tool_calls=msg.toolCalls or [],
            metadata_=metadata,
        )
        db.add(cm)
        new_msgs.append({"id": cm.id, "role": cm.role})

    await db.commit()
    return {"messages": new_msgs}


@messages_router.patch("/{message_id}")
async def update_message(
    message_id: str,
    data: MessageUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ChatMessage)
        .join(ChatSession, ChatSession.id == ChatMessage.chat_session_id)
        .where(
            ChatMessage.id == message_id,
            ChatSession.user_id == user.id,
        )
    )
    message = (await db.execute(stmt)).scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if data.metadata is not None:
        message.metadata_ = {**(message.metadata_ or {}), **data.metadata}

    await db.commit()
    return {"status": "ok", "metadata": message.metadata_}
