"""
KnowledgeGraphRepository - 知识图谱仓储

提供 F32 图谱节点和边相关的数据库操作。
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import GraphNode, GraphEdge
from db.repositories.base_repository import BaseRepository


class KnowledgeGraphRepository:
    """知识图谱仓储类"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_node(
        self,
        node_id: str,
        node_type: str,
        properties: Optional[dict[str, Any]] = None,
    ) -> GraphNode:
        """创建图谱节点"""
        node = GraphNode(
            id=node_id,
            node_type=node_type,
            properties=properties or {},
        )
        self._session.add(node)
        await self._session.flush()
        await self._session.refresh(node)
        return node

    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        """获取节点"""
        stmt = select(GraphNode).where(GraphNode.id == node_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_nodes(
        self,
        *,
        node_type: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Sequence[GraphNode]:
        """获取所有节点"""
        stmt = select(GraphNode)
        if node_type:
            stmt = stmt.where(GraphNode.node_type == node_type)
        stmt = stmt.order_by(GraphNode.created_at).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update_node(
        self, node_id: str, properties: dict[str, Any]
    ) -> Optional[GraphNode]:
        """更新节点属性（合并）"""
        node = await self.get_node(node_id)
        if node is None:
            return None

        node.properties.update(properties)
        await self._session.flush()
        await self._session.refresh(node)
        return node

    async def delete_node(self, node_id: str) -> bool:
        """删除节点（级联删除关联边）"""
        node = await self.get_node(node_id)
        if node is None:
            return False

        await self._session.delete(node)
        await self._session.flush()
        return True

    async def query_nodes(
        self,
        node_type: Optional[str] = None,
        **property_filters,
    ) -> Sequence[GraphNode]:
        """按类型和属性过滤查询节点"""
        conditions = []

        if node_type:
            conditions.append(GraphNode.node_type == node_type)

        for key, value in property_filters.items():
            conditions.append(
                text(f"properties->>'{key}' = :value")
            )

        stmt = select(GraphNode)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        if property_filters:
            params = {"value": str(value)}
            stmt = stmt.params(**params)

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        properties: Optional[dict[str, Any]] = None,
    ) -> Optional[GraphEdge]:
        """创建边"""
        source = await self.get_node(source_id)
        target = await self.get_node(target_id)
        if source is None or target is None:
            return None

        edge = GraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            properties=properties or {},
        )
        self._session.add(edge)
        await self._session.flush()
        await self._session.refresh(edge)
        return edge

    async def get_edge(self, edge_id: int) -> Optional[GraphEdge]:
        """获取边"""
        stmt = select(GraphEdge).where(GraphEdge.id == edge_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_edges(
        self,
        *,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        edge_type: Optional[str] = None,
        limit: int = 1000,
    ) -> Sequence[GraphEdge]:
        """查询边"""
        conditions = []

        if source_id:
            conditions.append(GraphEdge.source_id == source_id)
        if target_id:
            conditions.append(GraphEdge.target_id == target_id)
        if edge_type:
            conditions.append(GraphEdge.edge_type == edge_type)

        stmt = select(GraphEdge)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(GraphEdge.created_at).limit(limit)

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_outgoing_edges(self, node_id: str) -> Sequence[GraphEdge]:
        """获取节点的所有出边"""
        return await self.get_edges(source_id=node_id)

    async def get_incoming_edges(self, node_id: str) -> Sequence[GraphEdge]:
        """获取节点的所有入边"""
        return await self.get_edges(target_id=node_id)

    async def delete_edge(self, edge_id: int) -> bool:
        """删除边"""
        edge = await self.get_edge(edge_id)
        if edge is None:
            return False

        await self._session.delete(edge)
        await self._session.flush()
        return True

    async def get_neighbors(
        self, node_id: str, depth: int = 1
    ) -> list[dict[str, Any]]:
        """获取邻居节点（支持深度）"""
        if depth == 1:
            edges = await self.get_edges(source_id=node_id)
            neighbors = []
            for edge in edges:
                neighbors.append({
                    "neighbor_id": edge.target_id,
                    "edge_type": edge.edge_type,
                    "properties": edge.properties,
                    "depth": 1,
                })
            return neighbors

        stmt = text("""
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
        """)

        result = await self._session.execute(
            stmt,
            {"node_id": node_id, "depth": depth}
        )
        rows = result.fetchall()

        return [
            {
                "neighbor_id": row[0],
                "edge_type": row[1],
                "properties": row[2] if isinstance(row[2], dict) else {},
                "depth": row[3],
            }
            for row in rows
        ]

    async def find_path(
        self, start_id: str, end_id: str, max_depth: int = 10
    ) -> Optional[list[str]]:
        """使用 BFS 查找路径"""
        if start_id == end_id:
            return [start_id]

        stmt = text("""
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
        """)

        result = await self._session.execute(
            stmt,
            {"start_id": start_id, "end_id": end_id, "max_depth": max_depth}
        )
        row = result.fetchone()

        if row is None:
            return None
        return list(row[0])

    async def bfs_traverse(self, start_id: str) -> list[str]:
        """BFS 遍历"""
        stmt = text("""
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
        """)

        result = await self._session.execute(
            stmt,
            {"start_id": start_id}
        )
        rows = result.fetchall()

        result_list = [start_id]
        for row in rows:
            if row[0] not in result_list:
                result_list.append(row[0])
        return result_list

    async def dfs_traverse(self, start_id: str) -> list[str]:
        """DFS 遍历"""
        visited = set()
        result = []

        async def dfs(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            result.append(node_id)

            edges = await self.get_edges(source_id=node_id)
            for edge in edges:
                if edge.target_id not in visited:
                    await dfs(edge.target_id)

            incoming = await self.get_edges(target_id=node_id)
            for edge in incoming:
                if edge.source_id not in visited:
                    await dfs(edge.source_id)

        await dfs(start_id)
        return result

    async def batch_insert_nodes(
        self, nodes: list[dict[str, Any]]
    ) -> int:
        """批量插入节点"""
        count = 0
        for node_data in nodes:
            node = GraphNode(
                id=node_data["id"],
                node_type=node_data["node_type"],
                properties=node_data.get("properties", {}),
            )
            self._session.add(node)
            count += 1
        await self._session.flush()
        return count

    async def batch_insert_edges(
        self, edges: list[dict[str, Any]]
    ) -> int:
        """批量插入边"""
        count = 0
        for edge_data in edges:
            edge = GraphEdge(
                source_id=edge_data["source_id"],
                target_id=edge_data["target_id"],
                edge_type=edge_data["edge_type"],
                properties=edge_data.get("properties", {}),
            )
            self._session.add(edge)
            count += 1
        await self._session.flush()
        return count

    async def count_nodes(self, node_type: Optional[str] = None) -> int:
        """统计节点数量"""
        stmt = select(func.count()).select_from(GraphNode)
        if node_type:
            stmt = stmt.where(GraphNode.node_type == node_type)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_edges(self, edge_type: Optional[str] = None) -> int:
        """统计边数量"""
        stmt = select(func.count()).select_from(GraphEdge)
        if edge_type:
            stmt = stmt.where(GraphEdge.edge_type == edge_type)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def node_exists(self, node_id: str) -> bool:
        """检查节点是否存在"""
        stmt = select(func.count()).select_from(GraphNode).where(
            GraphNode.id == node_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def edge_exists(
        self, source_id: str, target_id: str, edge_type: str
    ) -> bool:
        """检查边是否存在"""
        stmt = select(func.count()).select_from(GraphEdge).where(
            and_(
                GraphEdge.source_id == source_id,
                GraphEdge.target_id == target_id,
                GraphEdge.edge_type == edge_type,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0
