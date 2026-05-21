"""
F32: PostgreSQL 连接池管理

提供线程安全的连接池，支持自动重连、连接验证和优雅关闭。
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ConnectionPool:
    """简单的 PostgreSQL 连接池"""

    def __init__(
        self,
        dsn: str,
        min_connections: int = 2,
        max_connections: int = 10,
        max_idle_time: float = 300.0,
        connection_timeout: float = 30.0,
    ):
        self._dsn = dsn
        self._min_connections = min_connections
        self._max_connections = max_connections
        self._max_idle_time = max_idle_time
        self._connection_timeout = connection_timeout
        self._pool: list[_PooledConnection] = []
        self._in_use: set[int] = set()
        self._lock = threading.RLock()
        self._closed = False
        self._total_created = 0

    @property
    def dsn(self) -> str:
        return self._dsn

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._pool)

    @property
    def in_use(self) -> int:
        with self._lock:
            return len(self._in_use)

    @property
    def available(self) -> int:
        with self._lock:
            return len(self._pool) - len(self._in_use)

    def initialize(self) -> None:
        """初始化连接池，创建最小数量的连接"""
        import psycopg2
        with self._lock:
            for _ in range(self._min_connections):
                conn = psycopg2.connect(self._dsn, connect_timeout=int(self._connection_timeout))
                conn.autocommit = False
                self._pool.append(_PooledConnection(
                    conn=conn,
                    created_at=time.time(),
                    last_used=time.time(),
                    conn_id=self._total_created,
                ))
                self._total_created += 1
        logger.info("Connection pool initialized with %d connections", self._min_connections)

    def get_connection(self):
        """
        从池中获取一个连接

        KG-014: Fixed thread-safety issue - entire connection acquisition
        is now within the lock to prevent race conditions.
        """
        import psycopg2
        with self._lock:
            if self._closed:
                raise RuntimeError("Connection pool is closed")

            for i, pooled in enumerate(self._pool):
                if i not in self._in_use:
                    if self._validate_connection(pooled):
                        self._in_use.add(i)
                        pooled.last_used = time.time()
                        return pooled.conn
                    else:
                        # KG-014: Replace connection INSIDE the lock
                        self._replace_connection_unlocked(i, pooled)

            if len(self._pool) < self._max_connections:
                # KG-014: Create new connection INSIDE the lock
                conn = psycopg2.connect(self._dsn, connect_timeout=int(self._connection_timeout))
                conn.autocommit = False
                idx = len(self._pool)
                self._pool.append(_PooledConnection(
                    conn=conn,
                    created_at=time.time(),
                    last_used=time.time(),
                    conn_id=self._total_created,
                ))
                self._total_created += 1
                self._in_use.add(idx)
                return conn

        raise RuntimeError("Connection pool exhausted, no available connections")

    def return_connection(self, conn) -> None:
        """将连接归还到池中"""
        with self._lock:
            for i, pooled in enumerate(self._pool):
                if pooled.conn is conn:
                    pooled.last_used = time.time()
                    self._in_use.discard(i)
                    return

    def close_stale_connections(self) -> int:
        """关闭空闲超时的连接"""
        now = time.time()
        closed = 0
        with self._lock:
            remaining = []
            for i, pooled in enumerate(self._pool):
                if i not in self._in_use:
                    if now - pooled.last_used > self._max_idle_time:
                        if len(self._pool) - closed > self._min_connections:
                            try:
                                pooled.conn.close()
                            except Exception:
                                pass
                            closed += 1
                            continue
                remaining.append(pooled)
            self._pool = remaining
            self._in_use = {i for i in self._in_use if i < len(remaining)}
        return closed

    def close_all(self) -> None:
        """关闭所有连接"""
        with self._lock:
            self._closed = True
            for pooled in self._pool:
                try:
                    pooled.conn.close()
                except Exception:
                    pass
            self._pool.clear()
            self._in_use.clear()
        logger.info("Connection pool closed, all connections released")

    def get_stats(self) -> dict:
        """获取连接池统计信息"""
        with self._lock:
            return {
                "total_connections": len(self._pool),
                "in_use": len(self._in_use),
                "available": len(self._pool) - len(self._in_use),
                "max_connections": self._max_connections,
                "min_connections": self._min_connections,
                "total_created": self._total_created,
                "closed": self._closed,
            }

    @contextmanager
    def connection(self):
        """上下文管理器：自动获取和归还连接"""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            self.return_connection(conn)

    def _validate_connection(self, pooled: _PooledConnection) -> bool:
        """验证连接是否有效"""
        try:
            cursor = pooled.conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception:
            return False

    def _replace_connection_unlocked(self, index: int, pooled: _PooledConnection) -> None:
        """
        替换失效连接（内部方法，假设调用者已经持有锁）

        KG-014: This method must be called while holding the lock.
        """
        import psycopg2
        try:
            pooled.conn.close()
        except Exception:
            pass
        new_conn = psycopg2.connect(self._dsn, connect_timeout=int(self._connection_timeout))
        new_conn.autocommit = False
        self._pool[index] = _PooledConnection(
            conn=new_conn,
            created_at=time.time(),
            last_used=time.time(),
            conn_id=self._total_created,
        )
        self._total_created += 1


class _PooledConnection:
    """池中的单个连接"""
    __slots__ = ("conn", "created_at", "last_used", "conn_id")

    def __init__(self, conn, created_at: float, last_used: float, conn_id: int):
        self.conn = conn
        self.created_at = created_at
        self.last_used = last_used
        self.conn_id = conn_id
