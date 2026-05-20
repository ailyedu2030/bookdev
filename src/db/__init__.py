"""
数据库模块初始化

提供数据库会话管理、连接池配置和异步 SQLAlchemy 引擎。
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/textbook_db",
)

_engine = None
_async_session_maker = None


def _get_engine():
    """懒加载引擎，避免模块导入时失败"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            DATABASE_URL,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            poolclass=NullPool,
            future=True,
        )
    return _engine


def _get_session_maker():
    """懒加载会话工厂"""
    global _async_session_maker
    if _async_session_maker is None:
        engine = _get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_maker


class Base(DeclarativeBase):
    """SQLAlchemy 声明性基类"""
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入函数"""
    session_maker = _get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """上下文管理器形式的数据库会话"""
    session_maker = _get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库连接"""
    engine = _get_engine()
    async with engine.begin() as conn:
        pass


async def close_db() -> None:
    """关闭数据库连接"""
    global _engine, _async_session_maker
    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None


def get_engine():
    """获取引擎实例（供外部使用）"""
    return _get_engine()


__all__ = [
    "Base",
    "get_engine",
    "get_session",
    "get_db_session",
    "init_db",
    "close_db",
]
