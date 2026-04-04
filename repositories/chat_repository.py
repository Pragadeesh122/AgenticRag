import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from repositories.base import BaseRepository
from database.models import ChatSession, ChatMessage

class ChatSessionRepository(BaseRepository[ChatSession]):
    def __init__(self, session):
        super().__init__(ChatSession, session)

    async def get_all_for_user(self, user_id: uuid.UUID, project_id: str | None = None) -> List[ChatSession]:
        stmt = select(ChatSession).where(ChatSession.user_id == user_id)
        if project_id:
            stmt = stmt.where(ChatSession.project_id == project_id)
        else:
            # We want general chats only if project_id not provided implicitly, or maybe user wants all?
            # Standard: if no project ID requested, fetch general chats.
            stmt = stmt.where(ChatSession.project_id == None)
        stmt = stmt.order_by(ChatSession.updated_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_messages(self, session_id: str, user_id: uuid.UUID) -> ChatSession | None:
        stmt = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ChatMessageRepository(BaseRepository[ChatMessage]):
    def __init__(self, session):
        super().__init__(ChatMessage, session)

    async def get_all_for_session(self, session_id: str) -> List[ChatMessage]:
        stmt = select(ChatMessage).where(ChatMessage.chat_session_id == session_id).order_by(ChatMessage.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
