"""
BaseRepository - 通用 CRUD 仓储基类

提供基于 SQLAlchemy 2.0 异步的通用增删改查操作。
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Generic, TypeVar, Optional, Type, Sequence

from sqlalchemy import select, update, delete, func, Select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Base

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """通用 CRUD 仓储基类"""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self._model = model
        self._session = session

    async def create(self, **kwargs) -> ModelType:
        """创建新记录"""
        try:
            instance = self._model(**kwargs)
            self._session.add(instance)
            await self._session.flush()
            await self._session.refresh(instance)
            return instance
        except Exception as e:
            logger.error(f"Failed to create {self._model.__name__}: {e}")
            raise

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        """根据 ID 获取单条记录"""
        try:
            stmt = select(self._model).where(self._model.id == id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get {self._model.__name__} by id {id}: {e}")
            raise

    async def get_one(self, **filters) -> Optional[ModelType]:
        """根据条件获取单条记录"""
        try:
            stmt = select(self._model)
            for key, value in filters.items():
                if hasattr(self._model, key):
                    stmt = stmt.where(getattr(self._model, key) == value)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get {self._model.__name__} with filters {filters}: {e}")
            raise

    async def find_all(
        self,
        *,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        offset_with_row_number: bool = False,
    ) -> Sequence[ModelType]:
        """获取所有匹配的记录"""
        stmt: Select = select(self._model)

        if filters:
            for key, value in filters.items():
                if hasattr(self._model, key):
                    if value is None:
                        stmt = stmt.where(getattr(self._model, key).is_(None))
                    else:
                        stmt = stmt.where(getattr(self._model, key) == value)

        if order_by and hasattr(self._model, order_by):
            order_col = getattr(self._model, order_by)
            if order_desc:
                stmt = stmt.order_by(order_col.desc())
            else:
                stmt = stmt.order_by(order_col)

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def count(self, *, filters: Optional[dict[str, Any]] = None) -> int:
        """统计匹配记录的总数"""
        stmt = select(func.count()).select_from(self._model)

        if filters:
            for key, value in filters.items():
                if hasattr(self._model, key):
                    if value is None:
                        stmt = stmt.where(getattr(self._model, key).is_(None))
                    else:
                        stmt = stmt.where(getattr(self._model, key) == value)

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def update(self, id: uuid.UUID, **kwargs) -> Optional[ModelType]:
        """根据 ID 更新记录"""
        try:
            instance = await self.get_by_id(id)
            if instance is None:
                return None

            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            await self._session.flush()
            await self._session.refresh(instance)
            return instance
        except Exception as e:
            logger.error(f"Failed to update {self._model.__name__} id {id}: {e}")
            raise

    async def delete(self, id: uuid.UUID) -> bool:
        """根据 ID 删除记录"""
        try:
            instance = await self.get_by_id(id)
            if instance is None:
                return False

            await self._session.delete(instance)
            await self._session.flush()
            return True
        except Exception as e:
            logger.error(f"Failed to delete {self._model.__name__} id {id}: {e}")
            raise

    async def exists(self, **filters) -> bool:
        """检查是否存在匹配条件的记录"""
        stmt = select(exists()).select_from(self._model)
        for key, value in filters.items():
            if hasattr(self._model, key):
                if value is None:
                    stmt = stmt.where(getattr(self._model, key).is_(None))
                else:
                    stmt = stmt.where(getattr(self._model, key) == value)

        result = await self._session.execute(stmt)
        return bool(result.scalar_one())

    async def bulk_create(self, instances: list[dict[str, Any]]) -> list[ModelType]:
        """批量创建记录"""
        try:
            created = []
            for kwargs in instances:
                instance = self._model(**kwargs)
                self._session.add(instance)
                created.append(instance)
            await self._session.flush()
            for instance in created:
                await self._session.refresh(instance)
            return created
        except Exception as e:
            logger.error(f"Failed to bulk create {self._model.__name__}: {e}")
            raise

    async def bulk_update(self, ids: list[uuid.UUID], **kwargs) -> int:
        """批量更新记录"""
        if not ids:
            return 0

        try:
            stmt = (
                update(self._model)
                .where(self._model.id.in_(ids))
                .values(**kwargs)
                .execution_params(synchronize_session=False)
            )
            result = await self._session.execute(stmt)
            await self._session.flush()
            return result.rowcount
        except Exception as e:
            logger.error(f"Failed to bulk update {self._model.__name__}: {e}")
            raise

    async def bulk_delete(self, ids: list[uuid.UUID]) -> int:
        """批量删除记录"""
        if not ids:
            return 0

        try:
            stmt = delete(self._model).where(self._model.id.in_(ids))
            result = await self._session.execute(stmt)
            await self._session.flush()
            return result.rowcount
        except Exception as e:
            logger.error(f"Failed to bulk delete {self._model.__name__}: {e}")
            raise

    async def get_by_ids(self, ids: list[uuid.UUID]) -> Sequence[ModelType]:
        """根据多个 ID 获取记录"""
        if not ids:
            return []
        stmt = select(self._model).where(self._model.id.in_(ids))
        result = await self._session.execute(stmt)
        return result.scalars().all()
