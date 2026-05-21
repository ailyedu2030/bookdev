"""
ProjectRepository - 项目仓储

提供项目相关的数据库操作。
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from db.models import Project, ProjectMember
from db.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """项目仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(Project, session)

    async def get_with_owner(self, project_id: uuid.UUID) -> Project | None:
        """获取项目及其所有者信息"""
        stmt = (
            select(Project)
            .options(joinedload(Project.owner))
            .where(Project.id == project_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_members(self, project_id: uuid.UUID) -> Project | None:
        """获取项目及其成员信息"""
        stmt = (
            select(Project)
            .options(selectinload(Project.members).selectinload(ProjectMember.user))
            .where(Project.id == project_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_chapters(self, project_id: uuid.UUID) -> Project | None:
        """获取项目及其章节列表"""
        stmt = (
            select(Project)
            .options(selectinload(Project.chapters))
            .where(Project.id == project_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_full_project(self, project_id: uuid.UUID) -> Project | None:
        """获取完整项目信息（包含所有者、成员、章节）"""
        stmt = (
            select(Project)
            .options(
                joinedload(Project.owner),
                selectinload(Project.members).selectinload(ProjectMember.user),
                selectinload(Project.chapters),
            )
            .where(Project.id == project_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_owner(
        self, owner_id: uuid.UUID, *, status: str | None = None
    ) -> Sequence[Project]:
        """获取用户拥有的项目"""
        filters = {"owner_id": owner_id}
        if status:
            filters["status"] = status
        return await self.find_all(filters=filters, order_by="created_at")

    async def get_by_status(
        self, status: str, *, limit: int | None = None
    ) -> Sequence[Project]:
        """根据状态获取项目"""
        return await self.find_all(
            filters={"status": status},
            order_by="created_at",
            limit=limit,
        )

    async def create_project(
        self,
        name: str,
        owner_id: uuid.UUID,
        description: str | None = None,
        **kwargs,
    ) -> Project:
        """创建项目的便捷方法"""
        return await self.create(
            name=name,
            owner_id=owner_id,
            description=description,
            **kwargs,
        )

    async def update_progress(
        self, project_id: uuid.UUID, current_progress: int
    ) -> Project | None:
        """更新项目进度"""
        return await self.update(project_id, current_progress=current_progress)

    async def update_status(
        self, project_id: uuid.UUID, status: str
    ) -> Project | None:
        """更新项目状态"""
        return await self.update(project_id, status=status)

    async def increment_chapter_count(
        self, project_id: uuid.UUID
    ) -> Project | None:
        """增加章节计数"""
        project = await self.get_by_id(project_id)
        if project:
            return await self.update(
                project_id,
                total_chapters=project.total_chapters + 1,
            )
        return None

    async def decrement_chapter_count(
        self, project_id: uuid.UUID
    ) -> Project | None:
        """减少章节计数"""
        project = await self.get_by_id(project_id)
        if project and project.total_chapters > 0:
            return await self.update(
                project_id,
                total_chapters=project.total_chapters - 1,
            )
        return None

    async def search_by_name(
        self, name_query: str, *, limit: int = 20
    ) -> Sequence[Project]:
        """根据名称搜索项目"""
        stmt = (
            select(Project)
            .where(Project.name.ilike(f"%{name_query}%"))
            .order_by(Project.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()


class ProjectMemberRepository(BaseRepository[ProjectMember]):
    """项目成员仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(ProjectMember, session)

    async def get_members_of_project(
        self, project_id: uuid.UUID
    ) -> Sequence[ProjectMember]:
        """获取项目的所有成员"""
        stmt = (
            select(ProjectMember)
            .options(joinedload(ProjectMember.user))
            .where(ProjectMember.project_id == project_id)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_projects_of_user(
        self, user_id: uuid.UUID
    ) -> Sequence[ProjectMember]:
        """获取用户参与的所有项目"""
        stmt = (
            select(ProjectMember)
            .options(joinedload(ProjectMember.project))
            .where(ProjectMember.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def add_member(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
    ) -> ProjectMember:
        """添加项目成员"""
        return await self.create(
            project_id=project_id,
            user_id=user_id,
            role=role,
        )

    async def is_member(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """检查用户是否为项目成员"""
        return await self.exists(project_id=project_id, user_id=user_id)

    async def get_member_role(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> str | None:
        """获取用户在项目中的角色"""
        stmt = select(ProjectMember.role).where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_member_role(
        self, project_id: uuid.UUID, user_id: uuid.UUID, role: str
    ) -> ProjectMember | None:
        """更新成员角色"""
        member = await self.get_one(project_id=project_id, user_id=user_id)
        if member:
            member.role = role
            await self._session.flush()
            await self._session.refresh(member)
            return member
        return None

    async def remove_member(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """移除项目成员"""
        stmt = select(ProjectMember).where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        result = await self._session.execute(stmt)
        member = result.scalar_one_or_none()
        if member:
            await self._session.delete(member)
            await self._session.flush()
            return True
        return False
