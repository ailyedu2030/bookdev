"""
ChapterRepository - 章节仓储

提供章节相关的数据库操作。
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from db.models import Chapter, ChapterContent, Review, Section
from db.repositories.base_repository import BaseRepository


class ChapterRepository(BaseRepository[Chapter]):
    """章节仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(Chapter, session)

    async def get_by_project(
        self,
        project_id: uuid.UUID,
        *,
        status: str | None = None,
        order_by: str = "order_num",
    ) -> Sequence[Chapter]:
        """获取项目下的所有章节"""
        filters = {"project_id": project_id}
        if status:
            filters["status"] = status
        return await self.find_all(filters=filters, order_by=order_by)

    async def get_with_contents(self, chapter_id: uuid.UUID) -> Chapter | None:
        """获取章节及其内容"""
        stmt = (
            select(Chapter)
            .options(selectinload(Chapter.contents))
            .where(Chapter.id == chapter_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_sections(self, chapter_id: uuid.UUID) -> Chapter | None:
        """获取章节及其小节"""
        stmt = (
            select(Chapter)
            .options(selectinload(Chapter.sections))
            .where(Chapter.id == chapter_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_reviews(self, chapter_id: uuid.UUID) -> Chapter | None:
        """获取章节及其审核记录"""
        stmt = (
            select(Chapter)
            .options(selectinload(Chapter.reviews))
            .where(Chapter.id == chapter_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_full_chapter(self, chapter_id: uuid.UUID) -> Chapter | None:
        """获取完整的章节信息（包含内容、小节、审核记录）"""
        stmt = (
            select(Chapter)
            .options(
                selectinload(Chapter.contents),
                selectinload(Chapter.sections),
                selectinload(Chapter.reviews).selectinload(Review.reviewer),
            )
            .where(Chapter.id == chapter_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_chapter(
        self,
        project_id: uuid.UUID,
        title: str,
        order_num: int,
        version: str,
        **kwargs,
    ) -> Chapter:
        """创建章节的便捷方法"""
        return await self.create(
            project_id=project_id,
            title=title,
            order_num=order_num,
            version=version,
            **kwargs,
        )

    async def update_status(self, chapter_id: uuid.UUID, status: str) -> Chapter | None:
        """更新章节状态"""
        return await self.update(chapter_id, status=status)

    async def update_content_hash(
        self, chapter_id: uuid.UUID, content_hash: str
    ) -> Chapter | None:
        """更新内容哈希"""
        return await self.update(chapter_id, content_hash=content_hash)

    async def update_word_count(
        self, chapter_id: uuid.UUID, word_count: int
    ) -> Chapter | None:
        """更新字数统计"""
        return await self.update(chapter_id, word_count=word_count)

    async def get_by_parent(
        self, parent_chapter_id: uuid.UUID
    ) -> Sequence[Chapter]:
        """获取子章节"""
        return await self.find_all(
            filters={"parent_chapter_id": parent_chapter_id},
            order_by="order_num",
        )

    async def get_next_order_num(self, project_id: uuid.UUID) -> int:
        """获取项目下一个可用的章节序号"""
        stmt = select(func.max(Chapter.order_num)).where(
            Chapter.project_id == project_id
        )
        result = await self._session.execute(stmt)
        max_order = result.scalar_one_or_none()
        return (max_order or 0) + 1

    async def reorder_chapters(
        self, project_id: uuid.UUID, chapter_orders: list[dict[str, Any]]
    ) -> None:
        """批量重排章节顺序 - 使用事务包装"""
        async with self._session.begin():
            for item in chapter_orders:
                chapter_id = item.get("id")
                order_num = item.get("order_num")
                if chapter_id and order_num is not None:
                    await self.update(chapter_id, order_num=order_num)


class ChapterContentRepository(BaseRepository[ChapterContent]):
    """章节内容仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(ChapterContent, session)

    async def get_by_chapter(
        self, chapter_id: uuid.UUID
    ) -> Sequence[ChapterContent]:
        """获取章节的所有内容版本"""
        return await self.find_all(
            filters={"chapter_id": chapter_id},
            order_by="created_at",
        )

    async def get_latest(self, chapter_id: uuid.UUID) -> ChapterContent | None:
        """获取章节的最新内容"""
        stmt = (
            select(ChapterContent)
            .where(ChapterContent.chapter_id == chapter_id)
            .order_by(ChapterContent.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_content(
        self,
        chapter_id: uuid.UUID,
        content: str,
        version: str,
        content_hash: str,
        created_by: uuid.UUID | None = None,
    ) -> ChapterContent:
        """创建新的章节内容版本"""
        return await self.create(
            chapter_id=chapter_id,
            content=content,
            version=version,
            content_hash=content_hash,
            created_by=created_by,
        )

    async def get_by_hash(
        self, chapter_id: uuid.UUID, content_hash: str
    ) -> ChapterContent | None:
        """根据内容哈希获取内容"""
        return await self.get_one(chapter_id=chapter_id, content_hash=content_hash)


class SectionRepository(BaseRepository[Section]):
    """小节仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(Section, session)

    async def get_by_chapter(
        self, chapter_id: uuid.UUID, *, status: str | None = None
    ) -> Sequence[Section]:
        """获取章节下的所有小节"""
        filters = {"chapter_id": chapter_id}
        if status:
            filters["status"] = status
        return await self.find_all(filters=filters, order_by="order_num")

    async def get_with_parent(self, section_id: uuid.UUID) -> Section | None:
        """获取小节及其父小节"""
        stmt = (
            select(Section)
            .options(joinedload(Section.parent_section))
            .where(Section.id == section_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_child_sections(
        self, parent_section_id: uuid.UUID
    ) -> Sequence[Section]:
        """获取子小节"""
        return await self.find_all(
            filters={"parent_section_id": parent_section_id},
            order_by="order_num",
        )

    async def create_section(
        self,
        chapter_id: uuid.UUID,
        title: str,
        order_num: int,
        **kwargs,
    ) -> Section:
        """创建小节的便捷方法"""
        return await self.create(
            chapter_id=chapter_id,
            title=title,
            order_num=order_num,
            **kwargs,
        )

    async def get_next_order_num(self, chapter_id: uuid.UUID) -> int:
        """获取章节下一个小节的序号"""
        stmt = select(func.max(Section.order_num)).where(
            Section.chapter_id == chapter_id
        )
        result = await self._session.execute(stmt)
        max_order = result.scalar_one_or_none()
        return (max_order or 0) + 1
