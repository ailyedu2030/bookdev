"""
F05: PostgreSQL + APOC 图数据库适配器

提供与PostgreSQL + apoc扩展的适配，支持图数据的持久化和查询。
委托给F32的PGAdapter实现。
"""

from typing import Any, Optional


class PGGraphAdapter:
    """PostgreSQL + APOC 图数据库适配器 - 委托给F32的PGAdapter"""

    def __init__(self, backend=None, connection_string: str = None):
        self._backend = backend
        self.connection_string = connection_string

    def connect(self):
        """建立数据库连接"""
        if self._backend is None:
            raise NotImplementedError("Backend not configured")
        return self._backend.connect()

    def disconnect(self):
        """断开数据库连接"""
        if self._backend is None:
            raise NotImplementedError("Backend not configured")
        return self._backend.disconnect()

    def create_tables(self):
        """创建图谱所需的数据库表"""
        if self._backend is None:
            raise NotImplementedError("Backend not configured")
        return self._backend.create_tables()

    def insert_node(self, node: Any):
        """插入节点"""
        if self._backend is None:
            raise NotImplementedError("Backend not configured")
        return self._backend.insert_node(node)

    def insert_edge(self, edge: Any):
        """插入边"""
        if self._backend is None:
            raise NotImplementedError("Backend not configured")
        return self._backend.insert_edge(edge)

    def query_nodes(self, node_type: str = None, **filters):
        """查询节点"""
        if self._backend is None:
            raise NotImplementedError("Backend not configured")
        return self._backend.query_nodes(node_type=node_type, **filters)

    def query_edges(self, edge_type: str = None, **filters):
        """查询边"""
        if self._backend is None:
            raise NotImplementedError("Backend not configured")
        return self._backend.query_edges(edge_type=edge_type, **filters)

    def execute_cypher(self, cypher_query: str):
        """执行Cypher查询 (通过APOC)"""
        if self._backend is None:
            raise NotImplementedError("Backend not configured")
        return self._backend.execute_cypher(cypher_query)

    def find_path(self, start_id: str, end_id: str, edge_types: list[str] = None, depth: int = None):
        """使用APOC查找路径"""
        if self._backend is None:
            raise NotImplementedError("Backend not configured")
        return self._backend.find_path(start_id, end_id, edge_types=edge_types, depth=depth)

    def get_neighbors(self, node_id: str, depth: int = 1):
        """获取邻居节点"""
        if self._backend is None:
            raise NotImplementedError("Backend not configured")
        return self._backend.get_neighbors(node_id, depth=depth)

    def batch_import(self, nodes: list[Any], edges: list[Any]):
        """批量导入"""
        if self._backend is None:
            raise NotImplementedError("Backend not configured")
        return self._backend.batch_import(nodes, edges)

    def export_to_cypher(self):
        """导出为Cypher语句"""
        if self._backend is None:
            raise NotImplementedError("Backend not configured")
        return self._backend.export_to_cypher()
