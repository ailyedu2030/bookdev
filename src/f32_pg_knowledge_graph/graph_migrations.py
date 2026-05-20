"""
F32: 图数据库迁移工具

提供数据库迁移、数据导入导出和 Schema 版本管理功能。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

MIGRATION_TABLE = """
CREATE TABLE IF NOT EXISTS graph_migrations (
    id SERIAL PRIMARY KEY,
    version TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT NOW()
)
"""


class GraphMigration:
    """图数据库迁移管理器"""

    def __init__(self, adapter):
        self._adapter = adapter
        self._migrations: list[dict] = []

    def register(self, version: str, description: str, up_sql: str, down_sql: str = "") -> None:
        """注册一个迁移"""
        self._migrations.append({
            "version": version,
            "description": description,
            "up": up_sql,
            "down": down_sql,
        })

    def migrate(self) -> int:
        """执行所有未应用的迁移"""
        self._ensure_migration_table()
        applied = self._get_applied_versions()
        count = 0

        for migration in self._migrations:
            if migration["version"] in applied:
                continue
            logger.info("Applying migration %s: %s", migration["version"], migration["description"])
            try:
                with self._adapter.transaction():
                    self._execute_sql(migration["up"])
                    self._record_migration(migration["version"], migration["description"])
                count += 1
            except Exception as e:
                logger.error("Migration %s failed: %s", migration["version"], e)
                raise

        return count

    def rollback(self, target_version: str) -> int:
        """回滚到指定版本"""
        self._ensure_migration_table()
        applied = self._get_applied_versions()
        count = 0

        migrations_map = {m["version"]: m for m in self._migrations}

        for version in reversed(applied):
            if version == target_version:
                break
            if version not in migrations_map:
                continue
            migration = migrations_map[version]
            logger.info("Rolling back %s: %s", version, migration["description"])
            try:
                with self._adapter.transaction():
                    self._execute_sql(migration["down"])
                    self._remove_migration(version)
                count += 1
            except Exception as e:
                logger.error("Rollback %s failed: %s", version, e)
                raise

        return count

    def status(self) -> list[dict]:
        """获取迁移状态"""
        self._ensure_migration_table()
        applied = set(self._get_applied_versions())
        result = []
        for migration in self._migrations:
            result.append({
                "version": migration["version"],
                "description": migration["description"],
                "applied": migration["version"] in applied,
            })
        return result

    def _ensure_migration_table(self) -> None:
        self._execute_sql(MIGRATION_TABLE)

    def _get_applied_versions(self) -> list[str]:
        rows = self._execute_sql(
            "SELECT version FROM graph_migrations ORDER BY id"
        )
        return [r[0] for r in rows]

    def _record_migration(self, version: str, description: str) -> None:
        self._execute_sql(
            "INSERT INTO graph_migrations (version, description) VALUES (%s, %s)",
            (version, description),
        )

    def _remove_migration(self, version: str) -> None:
        self._execute_sql(
            "DELETE FROM graph_migrations WHERE version = %s",
            (version,),
        )

    def _execute_sql(self, sql: str, params=None):
        """在适配器上执行 SQL"""
        sql_upper = sql.strip().upper()

        if hasattr(self._adapter, '_get_cursor'):
            with self._adapter._get_cursor() as (cursor, conn):
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                if sql_upper.startswith("SELECT"):
                    return cursor.fetchall()
                conn.commit()
                return None
        elif hasattr(self._adapter, '_conn') and self._adapter._conn:
            cursor = self._adapter._conn.cursor()
            try:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                if sql_upper.startswith("SELECT"):
                    return cursor.fetchall()
                self._adapter._conn.commit()
                return None
            finally:
                cursor.close()
        elif hasattr(self._adapter, '_nodes') and hasattr(self._adapter, '_edges'):
            return self._execute_sql_mock(sql, params)
        else:
            return None

    def _execute_sql_mock(self, sql: str, params=None):
        """在 Mock 适配器上模拟 SQL 执行"""
        sql_upper = sql.strip().upper()

        if "CREATE TABLE IF NOT EXISTS" in sql_upper:
            return None
        if sql_upper.startswith("SELECT") and "GRAPH_MIGRATIONS" in sql_upper:
            if not hasattr(self._adapter, '_migrations'):
                self._adapter._migrations = []
            return [(m["version"],) for m in self._adapter._migrations]
        if sql_upper.startswith("INSERT") and "GRAPH_MIGRATIONS" in sql_upper:
            if not hasattr(self._adapter, '_migrations'):
                self._adapter._migrations = []
            version = params[0] if params else "unknown"
            description = params[1] if params and len(params) > 1 else ""
            import time
            self._adapter._migrations.append({
                "version": version,
                "description": description,
                "applied_at": time.time(),
            })
            return None
        if sql_upper.startswith("DELETE") and "GRAPH_MIGRATIONS" in sql_upper:
            if hasattr(self._adapter, '_migrations'):
                self._adapter._migrations = [
                    m for m in self._adapter._migrations
                    if params is None or m["version"] != params[0]
                ]
            return None
        return None


def create_default_migrations(migration: GraphMigration) -> None:
    """注册默认迁移"""

    migration.register(
        version="001",
        description="Create graph_nodes and graph_edges tables",
        up_sql="""
            CREATE TABLE IF NOT EXISTS graph_nodes (
                id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                properties JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS graph_edges (
                id SERIAL PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                edge_type TEXT NOT NULL,
                properties JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                CONSTRAINT fk_edges_source FOREIGN KEY (source_id)
                    REFERENCES graph_nodes(id) ON DELETE CASCADE,
                CONSTRAINT fk_edges_target FOREIGN KEY (target_id)
                    REFERENCES graph_nodes(id) ON DELETE CASCADE
            );
        """,
        down_sql="""
            DROP TABLE IF EXISTS graph_edges CASCADE;
            DROP TABLE IF EXISTS graph_nodes CASCADE;
        """,
    )

    migration.register(
        version="002",
        description="Add indexes for graph query performance",
        up_sql="""
            CREATE INDEX IF NOT EXISTS idx_nodes_type ON graph_nodes(node_type);
            CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source_id);
            CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(target_id);
            CREATE INDEX IF NOT EXISTS idx_edges_type ON graph_edges(edge_type);
            CREATE INDEX IF NOT EXISTS idx_edges_source_target ON graph_edges(source_id, target_id);
        """,
        down_sql="""
            DROP INDEX IF EXISTS idx_nodes_type;
            DROP INDEX IF EXISTS idx_edges_source;
            DROP INDEX IF EXISTS idx_edges_target;
            DROP INDEX IF EXISTS idx_edges_type;
            DROP INDEX IF EXISTS idx_edges_source_target;
        """,
    )

    migration.register(
        version="003",
        description="Add JSONB GIN indexes for property queries",
        up_sql="""
            CREATE INDEX IF NOT EXISTS idx_nodes_properties ON graph_nodes USING GIN (properties);
            CREATE INDEX IF NOT EXISTS idx_edges_properties ON graph_edges USING GIN (properties);
        """,
        down_sql="""
            DROP INDEX IF EXISTS idx_nodes_properties;
            DROP INDEX IF EXISTS idx_edges_properties;
        """,
    )

    migration.register(
        version="004",
        description="Add updated_at trigger on graph_nodes",
        up_sql="""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trigger_nodes_updated_at ON graph_nodes;
            CREATE TRIGGER trigger_nodes_updated_at
                BEFORE UPDATE ON graph_nodes
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """,
        down_sql="""
            DROP TRIGGER IF EXISTS trigger_nodes_updated_at ON graph_nodes;
            DROP FUNCTION IF EXISTS update_updated_at_column();
        """,
    )
