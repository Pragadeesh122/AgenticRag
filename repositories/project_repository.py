import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from repositories.base import BaseRepository
from database.models import Project

class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session):
        super().__init__(Project, session)

    async def get_all_for_user(self, user_id: uuid.UUID) -> List[Project]:
        stmt = select(Project).where(Project.user_id == user_id).options(selectinload(Project.documents)).order_by(Project.updated_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_for_user(self, project_id: str, user_id: uuid.UUID) -> Project | None:
        stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id).options(selectinload(Project.documents))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
