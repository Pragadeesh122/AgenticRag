from sqlalchemy import select
from typing import List
from repositories.base import BaseRepository
from database.models import Document

class DocumentRepository(BaseRepository[Document]):
    def __init__(self, session):
        super().__init__(Document, session)

    async def get_all_for_project(self, project_id: str) -> List[Document]:
        stmt = select(Document).where(Document.project_id == project_id).order_by(Document.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, document_id: str, status: str, chunk_count: int = 0, error_message: str | None = None) -> Document:
        doc = await self.get_by_id(document_id)
        if doc:
            doc.status = status
            doc.chunk_count = chunk_count
            if error_message:
                doc.error_message = error_message
            await self.session.flush()
        return doc
