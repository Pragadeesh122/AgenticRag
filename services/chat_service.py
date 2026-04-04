import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.chat_repository import ChatSessionRepository, ChatMessageRepository

class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.chat_repo = ChatSessionRepository(session)
        self.msg_repo = ChatMessageRepository(session)

    async def get_user_sessions(self, user_id: uuid.UUID, project_id: str | None = None):
        return await self.chat_repo.get_all_for_user(user_id, project_id)

    async def get_session(self, session_id: str, user_id: uuid.UUID):
        chat_sess = await self.chat_repo.get_with_messages(session_id, user_id)
        if not chat_sess:
            raise HTTPException(status_code=404, detail="Chat Session not found")
        return chat_sess

    async def create_session(self, user_id: uuid.UUID, project_id: str | None = None, title: str = "New chat"):
        chat_sess = await self.chat_repo.create({
            "user_id": user_id,
            "project_id": project_id,
            "title": title
        })
        await self.session.commit()
        return chat_sess

    async def delete_session(self, session_id: str, user_id: uuid.UUID):
        chat_sess = await self.get_session(session_id, user_id)
        await self.chat_repo.delete(chat_sess)
        await self.session.commit()

    async def add_message(self, session_id: str, role: str, content: str, tool_calls: list = None, metadata: dict = None):
        if tool_calls is None: tool_calls = []
        if metadata is None: metadata = {}
        
        msg = await self.msg_repo.create({
            "chat_session_id": session_id,
            "role": role,
            "content": content,
            "tool_calls": tool_calls,
            "metadata_": metadata,
        })
        await self.session.commit()
        return msg
