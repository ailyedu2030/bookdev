"""
AuditLogRepository - 审计日志仓储

提供审计日志相关的数据库操作。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional, Sequence

from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AuditLog
from db.repositories.base_repository import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """审计日志仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AuditLog]:
        """获取用户的审计日志"""
        return await self.find_all(
            filters={"user_id": user_id},
            order_by="created_at",
            order_desc=True,
            limit=limit,
            offset=offset,
        )

    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AuditLog]:
        """获取特定资源的审计日志"""
        return await self.find_all(
            filters={"resource_type": resource_type, "resource_id": resource_id},
            order_by="created_at",
            order_desc=True,
            limit=limit,
            offset=offset,
        )

    async def get_by_event_type(
        self,
        event_type: str,
        *,
        since: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AuditLog]:
        """获取特定事件类型的审计日志"""
        filters = {"event_type": event_type}
        if since:
            stmt = (
                select(AuditLog)
                .where(
                    and_(
                        AuditLog.event_type == event_type,
                        AuditLog.created_at >= since,
                    )
                )
                .order_by(AuditLog.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            return result.scalars().all()
        return await self.find_all(
            filters=filters,
            order_by="created_at",
            order_desc=True,
            limit=limit,
            offset=offset,
        )

    async def get_recent_logs(
        self,
        *,
        hours: int = 24,
        limit: int = 1000,
    ) -> Sequence[AuditLog]:
        """获取最近N小时的审计日志"""
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            select(AuditLog)
            .where(AuditLog.created_at >= since)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def search_logs(
        self,
        *,
        event_type: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        result: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AuditLog]:
        """多条件搜索审计日志"""
        conditions = []

        if event_type:
            conditions.append(AuditLog.event_type == event_type)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if action:
            conditions.append(AuditLog.action == action)
        if result:
            conditions.append(AuditLog.result == result)
        if since:
            conditions.append(AuditLog.created_at >= since)
        if until:
            conditions.append(AuditLog.created_at <= until)

        stmt = select(AuditLog)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create_log(
        self,
        event_type: str,
        action: Optional[str] = None,
        result: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[uuid.UUID] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        signature: Optional[str] = None,
    ) -> AuditLog:
        """创建审计日志的便捷方法"""
        return await self.create(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            signature=signature,
        )

    async def count_by_event_type(
        self, event_type: str, *, since: Optional[datetime] = None
    ) -> int:
        """统计特定事件类型的日志数量"""
        if since:
            stmt = (
                select(func.count())
                .select_from(AuditLog)
                .where(
                    and_(
                        AuditLog.event_type == event_type,
                        AuditLog.created_at >= since,
                    )
                )
            )
            result = await self._session.execute(stmt)
            return result.scalar_one()
        return await self.count(filters={"event_type": event_type})

    async def count_by_user(
        self, user_id: uuid.UUID, *, since: Optional[datetime] = None
    ) -> int:
        """统计用户的日志数量"""
        if since:
            stmt = (
                select(func.count())
                .select_from(AuditLog)
                .where(
                    and_(
                        AuditLog.user_id == user_id,
                        AuditLog.created_at >= since,
                    )
                )
            )
            result = await self._session.execute(stmt)
            return result.scalar_one()
        return await self.count(filters={"user_id": user_id})

    async def get_failed_actions(
        self,
        *,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> Sequence[AuditLog]:
        """获取失败的操作日志"""
        conditions = [AuditLog.result == "failure"]

        if since:
            conditions.append(AuditLog.created_at >= since)

        stmt = (
            select(AuditLog)
            .where(and_(*conditions))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_ip_address(
        self,
        ip_address: str,
        *,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> Sequence[AuditLog]:
        """根据 IP 地址获取日志"""
        conditions = [AuditLog.ip_address == ip_address]
        if since:
            conditions.append(AuditLog.created_at >= since)

        stmt = (
            select(AuditLog)
            .where(and_(*conditions))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def verify_signature(self, log_id: uuid.UUID, signature: str) -> bool:
        """验证审计日志签名"""
        stmt = select(AuditLog.signature).where(AuditLog.id == log_id)
        result = await self._session.execute(stmt)
        stored_signature = result.scalar_one_or_none()
        return stored_signature == signature if stored_signature else False
