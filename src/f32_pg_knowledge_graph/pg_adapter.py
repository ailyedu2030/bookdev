"""
F32: PostgreSQL 适配器

提供对 PostgreSQL 数据库的底层操作，包括：
- 节点的 CRUD 操作
- 边的 CRUD 操作
- 图遍历查询
- 事务管理

此适配器现已更新为使用 SQLAlchemy 2.0 异步模型。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
from contextlib import contextmanager, asynccontextmanager

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db_session
from db.models import GraphNode as DBGraphNode, GraphEdge as DBGraphEdge

logger = logging.getLogger(__name__)


class PGAdapter:
    """PostgreSQL 数据库适配器（底层 SQL 操作）"""

    def __init__(self, pool=None, connection_string: Optional[str] = None):
        self._pool = pool
        self._connection_string = connection_string
        self._session: Optional[AsyncSession] = None
        self._own_session = False

    async def connect(self) -> None:
        """建立数据库连接"""
        if self._session:
            return
        if self._connection_string:
            from sqlalchemy.ext.asyncio import create_async_engine
            engine = create_async_engine(self._connection_string, echo=False)
            self._session = AsyncSession(engine)
            self._own_session = True

    async def disconnect(self) -> None:
        """断开数据库连接"""
        if self._own_session and self._session:
            await self._session.close()
            self._session = None

    async def _ensure_session(self) -> AsyncSession:
        """确保有可用的会话"""
        if self._session is None:
            await self.connect()
        return self._session

    async def create_tables(self) -> None:
        """创建图谱所需的数据库表"""
        session = await self._ensure_session()

        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS graph_nodes (
                id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                properties JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        await session.execute(text("""
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
            )
        """))

        await session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_nodes_type ON graph_nodes(node_type)")
        )
        await session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source_id)")
        )
        await session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(target_id)")
        )
        await session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_edges_type ON graph_edges(edge_type)")
        )

        await session.commit()

    async def drop_tables(self) -> None:
        """删除图数据库表"""
        session = await self._ensure_session()
        await session.execute(text("DROP TABLE IF EXISTS graph_edges CASCADE"))
        await session.execute(text("DROP TABLE IF EXISTS graph_nodes CASCADE"))
        await session.commit()

    async def insert_node(
        self, node_id: str, node_type: str, properties: dict = None
    ) -> None:
        """插入节点"""
        props = json.dumps(properties or {})
        session = await self._ensure_session()

        await session.execute(
            text("""
                INSERT INTO graph_nodes (id, node_type, properties)
                VALUES (:id, :node_type, :properties::jsonb)
                ON CONFLICT (id) DO UPDATE SET
                    node_type = EXCLUDED.node_type,
                    properties = EXCLUDED.properties,
                    updated_at = NOW()
            """),
            {"id": node_id, "node_type": node_type, "properties": props}
        )
        await session.commit()

    async def get_node(self, node_id: str) -> Optional[dict]:
        """获取单个节点"""
        session = await self._ensure_session()
        result = await session.execute(
            text("""
                SELECT id, node_type, properties, created_at, updated_at
                FROM graph_nodes WHERE id = :id
            """),
            {"id": node_id}
        )
        row = result.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "node_type": row[1],
            "properties": row[2] if isinstance(row[2], dict) else json.loads(row[2]),
            "created_at": row[3],
            "updated_at": row[4],
        }

    async def get_all_nodes(self) -> list[dict]:
        """获取全部节点"""
        session = await self._ensure_session()
        result = await session.execute(
            text("""
                SELECT id, node_type, properties, created_at, updated_at
                FROM graph_nodes ORDER BY created_at
            """)
        )
        return [
            {
                "id": r[0],
                "node_type": r[1],
                "properties": r[2] if isinstance(r[2], dict) else json.loads(r[2]),
                "created_at": r[3],
                "updated_at": r[4],
            }
            for r in result.fetchall()
        ]

    async def query_nodes(
        self, node_type: Optional[str] = None, **filters
    ) -> list[dict]:
        """按类型和属性过滤查询节点"""
        session = await self._ensure_session()

        if node_type:
            result = await session.execute(
                text("""
                    SELECT id, node_type, properties, created_at, updated_at
                    FROM graph_nodes WHERE node_type = :node_type ORDER BY created_at
                """),
                {"node_type": node_type}
            )
        else:
            result = await session.execute(
                text("""
                    SELECT id, node_type, properties, created_at, updated_at
                    FROM graph_nodes ORDER BY created_at
                """)
            )

        results = [
            {
                "id": r[0],
                "node_type": r[1],
                "properties": r[2] if isinstance(r[2], dict) else json.loads(r[2]),
                "created_at": r[3],
                "updated_at": r[4],
            }
            for r in result.fetchall()
        ]

        if filters:
            filtered = []
            for node in results:
                props = node["properties"]
                match = True
                for key, value in filters.items():
                    if props.get(key) != value:
                        match = False
                        break
                if match:
                    filtered.append(node)
            return filtered
        return results

    async def update_node(self, node_id: str, properties: dict) -> bool:
        """更新节点属性（合并）"""
        session = await self._ensure_session()

        result = await session.execute(
            text("SELECT properties FROM graph_nodes WHERE id = :id"),
            {"id": node_id}
        )
        row = result.fetchone()
        if row is None:
            return False

        existing = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        existing.update(properties)

        await session.execute(
            text("""
                UPDATE graph_nodes SET properties = :properties::jsonb, updated_at = NOW()
                WHERE id = :id
            """),
            {"id": node_id, "properties": json.dumps(existing)}
        )
        await session.commit()
        return True

    async def delete_node(self, node_id: str) -> bool:
        """删除节点（级联删除关联边）"""
        session = await self._ensure_session()
        result = await session.execute(
            text("DELETE FROM graph_nodes WHERE id = :id"),
            {"id": node_id}
        )
        deleted = result.rowcount > 0
        await session.commit()
        return deleted

    async def insert_edge(
        self, source_id: str, target_id: str, edge_type: str, properties: dict = None
    ) -> Optional[int]:
        """插入边"""
        props = json.dumps(properties or {})
        session = await self._ensure_session()

        try:
            result = await session.execute(
                text("""
                    INSERT INTO graph_edges (source_id, target_id, edge_type, properties)
                    VALUES (:source_id, :target_id, :edge_type, :properties::jsonb)
                    RETURNING id
                """),
                {
                    "source_id": source_id,
                    "target_id": target_id,
                    "edge_type": edge_type,
                    "properties": props,
                }
            )
            edge_id = result.fetchone()[0]
            await session.commit()
            return edge_id
        except Exception as e:
            logger.warning("Failed to insert edge: %s", e)
            await session.rollback()
            return None

    async def get_edge(self, edge_id: int) -> Optional[dict]:
        """获取单条边"""
        session = await self._ensure_session()
        result = await session.execute(
            text("""
                SELECT id, source_id, target_id, edge_type, properties, created_at
                FROM graph_edges WHERE id = :id
            """),
            {"id": edge_id}
        )
        row = result.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "source_id": row[1],
            "target_id": row[2],
            "edge_type": row[3],
            "properties": row[4] if isinstance(row[4], dict) else json.loads(row[4]),
            "created_at": row[5],
        }

    async def get_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        edge_type: Optional[str] = None,
    ) -> list[dict]:
        """查询边"""
        session = await self._ensure_session()
        conditions = []
        params = {}

        if source_id:
            conditions.append("source_id = :source_id")
            params["source_id"] = source_id
        if target_id:
            conditions.append("target_id = :target_id")
            params["target_id"] = target_id
        if edge_type:
            conditions.append("edge_type = :edge_type")
            params["edge_type"] = edge_type

        query = "SELECT id, source_id, target_id, edge_type, properties, created_at FROM graph_edges"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at"

        result = await session.execute(text(query), params)
        return [
            {
                "id": r[0],
                "source_id": r[1],
                "target_id": r[2],
                "edge_type": r[3],
                "properties": r[4] if isinstance(r[4], dict) else json.loads(r[4]),
                "created_at": r[5],
            }
            for r in result.fetchall()
        ]

    async def delete_edge(self, edge_id: int) -> bool:
        """删除边"""
        session = await self._ensure_session()
        result = await session.execute(
            text("DELETE FROM graph_edges WHERE id = :id"),
            {"id": edge_id}
        )
        deleted = result.rowcount > 0
        await session.commit()
        return deleted

    async def get_neighbors(self, node_id: str, depth: int = 1) -> list[dict]:
        """获取邻居节点"""
        session = await self._ensure_session()
        result = await session.execute(
            text("""
                WITH RECURSIVE neighbors AS (
                    SELECT
                        CASE WHEN e.source_id = :node_id THEN e.target_id ELSE e.source_id END AS neighbor_id,
                        e.edge_type,
                        e.properties,
                        1 AS depth
                    FROM graph_edges e
                    WHERE e.source_id = :node_id OR e.target_id = :node_id

                    UNION ALL

                    SELECT
                        CASE WHEN e2.source_id = n.neighbor_id THEN e2.target_id ELSE e2.source_id END,
                        e2.edge_type,
                        e2.properties,
                        n.depth + 1
                    FROM graph_edges e2
                    INNER JOIN neighbors n ON (
                        e2.source_id = n.neighbor_id OR e2.target_id = n.neighbor_id
                    )
                    WHERE n.depth < :depth
                )
                SELECT DISTINCT neighbor_id, edge_type, properties, depth
                FROM neighbors
                ORDER BY depth, neighbor_id
            """),
            {"node_id": node_id, "depth": depth}
        )
        return [
            {
                "neighbor_id": r[0],
                "edge_type": r[1],
                "properties": r[2] if isinstance(r[2], dict) else json.loads(r[2]),
                "depth": r[3],
            }
            for r in result.fetchall()
        ]

    async def find_path(
        self, start_id: str, end_id: str, max_depth: int = 10
    ) -> Optional[list[str]]:
        """使用 BFS 在图中查找路径"""
        session = await self._ensure_session()
        result = await session.execute(
            text("""
                WITH RECURSIVE path_search AS (
                    SELECT
                        source_id AS node_id,
                        ARRAY[source_id] AS path,
                        1 AS depth
                    FROM graph_edges
                    WHERE source_id = :start_id

                    UNION ALL

                    SELECT
                        e.target_id,
                        ps.path || e.target_id,
                        ps.depth + 1
                    FROM graph_edges e
                    INNER JOIN path_search ps ON e.source_id = ps.node_id
                    WHERE ps.depth < :max_depth
                    AND NOT (e.target_id = ANY(ps.path))
                )
                SELECT path FROM path_search
                WHERE node_id = :end_id
                ORDER BY depth
                LIMIT 1
            """),
            {"start_id": start_id, "end_id": end_id, "max_depth": max_depth}
        )
        row = result.fetchone()
        if row is None:
            return None
        return list(row[0])

    async def bfs_traverse(self, start_id: str) -> list[str]:
        """BFS 遍历"""
        session = await self._ensure_session()
        result = await session.execute(
            text("""
                WITH RECURSIVE bfs AS (
                    SELECT source_id AS node_id, 1 AS depth
                    FROM graph_edges WHERE source_id = :start_id
                    UNION
                    SELECT target_id, 1
                    FROM graph_edges WHERE source_id = :start_id

                    UNION ALL

                    SELECT
                        CASE WHEN e.source_id = b.node_id THEN e.target_id ELSE e.source_id END,
                        b.depth + 1
                    FROM graph_edges e
                    INNER JOIN bfs b ON (e.source_id = b.node_id OR e.target_id = b.node_id)
                    WHERE b.depth < 50
                )
                SELECT DISTINCT node_id, depth FROM bfs WHERE node_id != :start_id ORDER BY depth
            """),
            {"start_id": start_id}
        )
        result_list = [start_id]
        for row in result.fetchall():
            if row[0] not in result_list:
                result_list.append(row[0])
        return result_list

    async def dfs_traverse(self, start_id: str) -> list[str]:
        """DFS 遍历"""
        session = await self._ensure_session()
        result = await session.execute(
            text("""
                WITH RECURSIVE dfs AS (
                    SELECT source_id AS node_id,
                           ARRAY[source_id] AS visited,
                           1 AS depth
                    FROM graph_edges WHERE source_id = :start_id
                    UNION
                    SELECT target_id, ARRAY[target_id], 1
                    FROM graph_edges WHERE source_id = :start_id

                    UNION ALL

                    SELECT
                        CASE WHEN e.source_id = d.node_id THEN e.target_id ELSE e.source_id END,
                        d.visited || CASE WHEN e.source_id = d.node_id THEN e.target_id ELSE e.source_id END,
                        d.depth + 1
                    FROM graph_edges e
                    INNER JOIN dfs d ON (e.source_id = d.node_id OR e.target_id = d.node_id)
                    WHERE d.depth < 50
                    AND NOT (
                        CASE WHEN e.source_id = d.node_id THEN e.target_id ELSE e.source_id END = ANY(d.visited)
                    )
                )
                SELECT DISTINCT node_id FROM dfs WHERE node_id != :start_id ORDER BY depth
            """),
            {"start_id": start_id}
        )
        result_list = [start_id]
        for row in result.fetchall():
            if row[0] not in result_list:
                result_list.append(row[0])
        return result_list

    async def batch_insert_nodes(self, nodes: list[dict]) -> int:
        """批量插入节点"""
        count = 0
        session = await self._ensure_session()

        for node in nodes:
            props = json.dumps(node.get("properties", {}))
            await session.execute(
                text("""
                    INSERT INTO graph_nodes (id, node_type, properties)
                    VALUES (:id, :node_type, :properties::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                        node_type = EXCLUDED.node_type,
                        properties = EXCLUDED.properties,
                        updated_at = NOW()
                """),
                {
                    "id": node["id"],
                    "node_type": node["node_type"],
                    "properties": props,
                }
            )
            count += 1
        await session.commit()
        return count

    async def batch_insert_edges(self, edges: list[dict]) -> int:
        """批量插入边"""
        count = 0
        session = await self._ensure_session()

        for edge in edges:
            props = json.dumps(edge.get("properties", {}))
            try:
                await session.execute(
                    text("""
                        INSERT INTO graph_edges (source_id, target_id, edge_type, properties)
                        VALUES (:source_id, :target_id, :edge_type, :properties::jsonb)
                    """),
                    {
                        "source_id": edge["source_id"],
                        "target_id": edge["target_id"],
                        "edge_type": edge["edge_type"],
                        "properties": props,
                    }
                )
                count += 1
            except Exception as e:
                logger.warning("Batch edge insert failed: %s", e)
        await session.commit()
        return count

    def transaction(self):
        """返回事务上下文管理器"""
        return _TransactionContext(self)

    async def count_nodes(self, node_type: Optional[str] = None) -> int:
        """统计节点数量"""
        session = await self._ensure_session()
        if node_type:
            result = await session.execute(
                text("SELECT COUNT(*) FROM graph_nodes WHERE node_type = :node_type"),
                {"node_type": node_type}
            )
        else:
            result = await session.execute(
                text("SELECT COUNT(*) FROM graph_nodes")
            )
        return result.fetchone()[0]

    async def count_edges(self, edge_type: Optional[str] = None) -> int:
        """统计边数量"""
        session = await self._ensure_session()
        if edge_type:
            result = await session.execute(
                text("SELECT COUNT(*) FROM graph_edges WHERE edge_type = :edge_type"),
                {"edge_type": edge_type}
            )
        else:
            result = await session.execute(
                text("SELECT COUNT(*) FROM graph_edges")
            )
        return result.fetchone()[0]


class _TransactionContext:
    """事务上下文管理器"""

    def __init__(self, adapter: PGAdapter):
        self._adapter = adapter

    async def __aenter__(self):
        return self._adapter

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._adapter._session:
            if exc_type:
                await self._adapter._session.rollback()
            else:
                await self._adapter._session.commit()


class MockPGAdapter:
    """Mock PostgreSQL 适配器（用于无 PostgreSQL 环境下的测试）"""

    def __init__(self):
        self._nodes: dict[str, dict] = {}
        self._edges: dict[int, dict] = {}
        self._next_edge_id = 1
        self._transaction_active = False
        self._rollback_data: dict = {}

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def create_tables(self) -> None:
        self._nodes.clear()
        self._edges.clear()
        self._next_edge_id = 1

    def drop_tables(self) -> None:
        self.create_tables()

    def insert_node(
        self, node_id: str, node_type: str, properties: dict = None
    ) -> None:
        props = dict(properties or {})
        if node_id in self._nodes:
            self._nodes[node_id]["node_type"] = node_type
            self._nodes[node_id]["properties"].update(props)
        else:
            self._nodes[node_id] = {
                "id": node_id,
                "node_type": node_type,
                "properties": props,
                "created_at": None,
                "updated_at": None,
            }

    def get_node(self, node_id: str) -> Optional[dict]:
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> list[dict]:
        return list(self._nodes.values())

    def query_nodes(
        self, node_type: Optional[str] = None, **filters
    ) -> list[dict]:
        results = list(self._nodes.values())
        if node_type:
            results = [n for n in results if n["node_type"] == node_type]
        if filters:
            filtered = []
            for node in results:
                props = node["properties"]
                match = True
                for key, value in filters.items():
                    if props.get(key) != value:
                        match = False
                        break
                if match:
                    filtered.append(node)
            return filtered
        return results

    def update_node(self, node_id: str, properties: dict) -> bool:
        if node_id not in self._nodes:
            return False
        self._nodes[node_id]["properties"].update(properties)
        return True

    def delete_node(self, node_id: str) -> bool:
        if node_id in self._nodes:
            del self._nodes[node_id]
            self._edges = {
                eid: e for eid, e in self._edges.items()
                if e["source_id"] != node_id and e["target_id"] != node_id
            }
            return True
        return False

    def insert_edge(
        self, source_id: str, target_id: str, edge_type: str, properties: dict = None
    ) -> Optional[int]:
        edge_id = self._next_edge_id
        self._next_edge_id += 1
        self._edges[edge_id] = {
            "id": edge_id,
            "source_id": source_id,
            "target_id": target_id,
            "edge_type": edge_type,
            "properties": dict(properties or {}),
            "created_at": None,
        }
        return edge_id

    def get_edge(self, edge_id: int) -> Optional[dict]:
        return self._edges.get(edge_id)

    def get_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        edge_type: Optional[str] = None,
    ) -> list[dict]:
        results = list(self._edges.values())
        if source_id:
            results = [
                e for e in results
                if e["source_id"] == source_id or e["target_id"] == source_id
            ]
        if target_id:
            results = [e for e in results if e["target_id"] == target_id]
        if edge_type:
            results = [e for e in results if e["edge_type"] == edge_type]
        return results

    def delete_edge(self, edge_id: int) -> bool:
        if edge_id in self._edges:
            del self._edges[edge_id]
            return True
        return False

    def get_neighbors(self, node_id: str, depth: int = 1) -> list[dict]:
        visited = set()
        result = []
        queue = [(node_id, 0)]
        while queue:
            current, d = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for edge in self._edges.values():
                if edge["source_id"] == current:
                    neighbor = edge["target_id"]
                elif edge["target_id"] == current:
                    neighbor = edge["source_id"]
                else:
                    continue
                if neighbor not in visited and d < depth:
                    result.append({
                        "neighbor_id": neighbor,
                        "edge_type": edge["edge_type"],
                        "properties": edge["properties"],
                        "depth": d + 1,
                    })
                    queue.append((neighbor, d + 1))
        return result

    def find_path(
        self, start_id: str, end_id: str, max_depth: int = 10
    ) -> Optional[list[str]]:
        if start_id not in self._nodes:
            return None
        visited = {start_id}
        queue = [(start_id, [start_id])]
        while queue:
            node_id, path = queue.pop(0)
            if len(path) > max_depth:
                continue
            for edge in self._edges.values():
                neighbor = None
                if edge["source_id"] == node_id:
                    neighbor = edge["target_id"]
                elif edge["target_id"] == node_id:
                    neighbor = edge["source_id"]
                if neighbor:
                    if neighbor == end_id:
                        return path + [neighbor]
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
        return None

    def bfs_traverse(self, start_id: str) -> list[str]:
        if start_id not in self._nodes:
            return [start_id]
        visited = set()
        queue = [start_id]
        result = []
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            result.append(node_id)
            for edge in self._edges.values():
                if edge["source_id"] == node_id and edge["target_id"] not in visited:
                    queue.append(edge["target_id"])
                elif edge["target_id"] == node_id and edge["source_id"] not in visited:
                    queue.append(edge["source_id"])
        return result

    def dfs_traverse(self, start_id: str) -> list[str]:
        if start_id not in self._nodes:
            return [start_id]
        visited = set()
        result = []

        def _dfs(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            result.append(node_id)
            for edge in self._edges.values():
                if edge["source_id"] == node_id:
                    _dfs(edge["target_id"])
                elif edge["target_id"] == node_id:
                    _dfs(edge["source_id"])

        _dfs(start_id)
        return result

    def batch_insert_nodes(self, nodes: list[dict]) -> int:
        for node in nodes:
            self.insert_node(
                node["id"], node["node_type"], node.get("properties", {})
            )
        return len(nodes)

    def batch_insert_edges(self, edges: list[dict]) -> int:
        for edge in edges:
            self.insert_edge(
                edge["source_id"], edge["target_id"],
                edge["edge_type"], edge.get("properties", {}),
            )
        return len(edges)

    def transaction(self):
        return _MockTransactionContext(self)

    def count_nodes(self, node_type: Optional[str] = None) -> int:
        if node_type:
            return sum(1 for n in self._nodes.values() if n["node_type"] == node_type)
        return len(self._nodes)

    def count_edges(self, edge_type: Optional[str] = None) -> int:
        if edge_type:
            return sum(1 for e in self._edges.values() if e["edge_type"] == edge_type)
        return len(self._edges)


class _MockTransactionContext:
    """事务上下文管理器（Mock）"""

    def __init__(self, adapter: MockPGAdapter):
        self._adapter = adapter
        self._snapshot: dict = {}

    def __enter__(self):
        self._snapshot = {
            "nodes": dict(self._adapter._nodes),
            "edges": dict(self._adapter._edges),
            "next_edge_id": self._adapter._next_edge_id,
        }
        return self._adapter

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self._adapter._nodes = self._snapshot["nodes"]
            self._adapter._edges = self._snapshot["edges"]
            self._adapter._next_edge_id = self._snapshot["next_edge_id"]
