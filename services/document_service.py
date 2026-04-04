import uuid
import os
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.document_repository import DocumentRepository
from repositories.project_repository import ProjectRepository

class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.proj_repo = ProjectRepository(session)

    async def get_project_documents(self, project_id: str, user_id: uuid.UUID):
        project = await self.proj_repo.get_by_id_for_user(project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return await self.doc_repo.get_all_for_project(project_id)

    async def create_document_record(self, project_id: str, user_id: uuid.UUID, filename: str, file_type: str, file_size: int):
        project = await self.proj_repo.get_by_id_for_user(project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        doc = await self.doc_repo.create({
            "project_id": project_id,
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "status": "uploading"
        })
        await self.session.commit()
        return doc

    async def mark_processing(self, doc_id: str):
        doc = await self.doc_repo.update_status(doc_id, "processing")
        await self.session.commit()
        return doc
        
    async def mark_ready(self, doc_id: str, count: int):
        doc = await self.doc_repo.update_status(doc_id, "ready", chunk_count=count)
        await self.session.commit()
        return doc
        
    async def mark_failed(self, doc_id: str, err: str):
        doc = await self.doc_repo.update_status(doc_id, "failed", error_message=err)
        await self.session.commit()
        return doc
