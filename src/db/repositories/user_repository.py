"""
UserRepository - 用户仓储

提供用户相关的数据库操作。
"""

from __future__ import annotations

import uuid
from typing import Any, Optional, Sequence

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from db.models import User, Role, Permission, UserRole, RolePermission
from db.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """用户仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return await self.get_one(username=username)

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return await self.get_one(email=email)

    async def get_with_roles(self, user_id: uuid.UUID) -> Optional[User]:
        """获取用户及其角色信息"""
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_permissions(self, user_id: uuid.UUID) -> Optional[User]:
        """获取用户及其所有权限"""
        user = await self.get_with_roles(user_id)
        if user is None:
            return None

        all_permissions = []
        for role in user.roles:
            stmt = (
                select(Permission)
                .join(RolePermission)
                .where(RolePermission.role_id == role.id)
            )
            result = await self._session.execute(stmt)
            permissions = result.scalars().all()
            all_permissions.extend(permissions)

        return user

    async def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        role: str = "viewer",
        **kwargs,
    ) -> User:
        """创建用户的便捷方法"""
        return await self.create(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            **kwargs,
        )

    async def update_password(
        self, user_id: uuid.UUID, password_hash: str
    ) -> Optional[User]:
        """更新密码"""
        return await self.update(user_id, password_hash=password_hash)

    async def update_email(
        self, user_id: uuid.UUID, email: str
    ) -> Optional[User]:
        """更新邮箱"""
        return await self.update(user_id, email=email)

    async def assign_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> UserRole:
        """为用户分配角色"""
        user_role = UserRole(user_id=user_id, role_id=role_id)
        self._session.add(user_role)
        await self._session.flush()
        return user_role

    async def remove_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        """移除用户角色"""
        stmt = select(UserRole).where(
            and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
        )
        result = await self._session.execute(stmt)
        user_role = result.scalar_one_or_none()
        if user_role:
            await self._session.delete(user_role)
            await self._session.flush()
            return True
        return False

    async def has_permission(
        self, user_id: uuid.UUID, resource: str, action: str
    ) -> bool:
        """检查用户是否具有特定权限"""
        stmt = (
            select(func.count())
            .select_from(Permission)
            .join(RolePermission)
            .join(Role)
            .join(UserRole)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    Permission.resource == resource,
                    Permission.action == action,
                )
            )
        )
        result = await self._session.execute(stmt)
        count = result.scalar_one()
        return count > 0

    async def search_by_username(
        self, username_query: str, *, limit: int = 20
    ) -> Sequence[User]:
        """根据用户名搜索用户"""
        stmt = (
            select(User)
            .where(User.username.ilike(f"%{username_query}%"))
            .order_by(User.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def search_by_email(
        self, email_query: str, *, limit: int = 20
    ) -> Sequence[User]:
        """根据邮箱搜索用户"""
        stmt = (
            select(User)
            .where(User.email.ilike(f"%{email_query}%"))
            .order_by(User.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()


class RoleRepository(BaseRepository[Role]):
    """角色仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)

    async def get_by_name(self, name: str) -> Optional[Role]:
        """根据名称获取角色"""
        return await self.get_one(name=name)

    async def get_with_permissions(self, role_id: uuid.UUID) -> Optional[Role]:
        """获取角色及其权限"""
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_user_count(self) -> Sequence[Role]:
        """获取所有角色及每个角色的用户数量"""
        stmt = (
            select(Role)
            .options(selectinload(Role.users))
            .order_by(Role.name)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def assign_permission(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> RolePermission:
        """为角色分配权限"""
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        self._session.add(role_permission)
        await self._session.flush()
        return role_permission

    async def remove_permission(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> bool:
        """移除角色权限"""
        stmt = select(RolePermission).where(
            and_(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )
        result = await self._session.execute(stmt)
        role_permission = result.scalar_one_or_none()
        if role_permission:
            await self._session.delete(role_permission)
            await self._session.flush()
            return True
        return False


class PermissionRepository(BaseRepository[Permission]):
    """权限仓储类"""

    def __init__(self, session: AsyncSession):
        super().__init__(Permission, session)

    async def get_by_resource_action(
        self, resource: str, action: str
    ) -> Optional[Permission]:
        """根据资源和动作获取权限"""
        return await self.get_one(resource=resource, action=action)

    async def get_by_resource(self, resource: str) -> Sequence[Permission]:
        """根据资源获取所有权限"""
        return await self.find_all(filters={"resource": resource}, order_by="action")

    async def get_all_grouped_by_resource(self) -> dict[str, Sequence[Permission]]:
        """获取所有权限，按资源分组"""
        stmt = select(Permission).order_by(Permission.resource, Permission.action)
        result = await self._session.execute(stmt)
        permissions = result.scalars().all()

        grouped = {}
        for perm in permissions:
            if perm.resource not in grouped:
                grouped[perm.resource] = []
            grouped[perm.resource].append(perm)

        return grouped
