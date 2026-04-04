import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.project_repository import ProjectRepository

class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ProjectRepository(session)

    async def get_user_projects(self, user_id: uuid.UUID):
        return await self.repo.get_all_for_user(user_id)

    async def get_project(self, project_id: str, user_id: uuid.UUID):
        project = await self.repo.get_by_id_for_user(project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    async def create_project(self, user_id: uuid.UUID, name: str, description: str = None):
        project = await self.repo.create({
            "user_id": user_id,
            "name": name,
            "description": description,
        })
        project.documents = []
        await self.session.commit()
        return project

    async def delete_project(self, project_id: str, user_id: uuid.UUID):
        project = await self.get_project(project_id, user_id)
        await self.repo.delete(project)
        await self.session.commit()
