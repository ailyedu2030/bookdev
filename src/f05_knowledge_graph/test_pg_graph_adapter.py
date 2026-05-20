"""
F05: PostgreSQL Graph Adapter Tests

TDD Phase RED: Tests for PGGraphAdapter persistence layer
These tests verify that PGGraphAdapter properly delegates to F32's PGAdapter
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass


@dataclass
class MockNode:
    """Mock node for testing"""
    id: str
    node_type: str
    properties: dict = None


@dataclass
class MockEdge:
    """Mock edge for testing"""
    id: str
    source_id: str
    target_id: str
    edge_type: str
    properties: dict = None


class TestPGGraphAdapterDelegation:
    """PGGraphAdapter 委托测试 - 验证委托给F32的PGAdapter"""

    def test_init_with_f32_adapter(self):
        """F05-T050: 可以使用F32的PGAdapter作为后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_f32_adapter = MagicMock()
        adapter = PGGraphAdapter(backend=mock_f32_adapter)
        assert adapter._backend is mock_f32_adapter

    def test_connect_calls_backend_connect(self):
        """F05-T051: connect委托给后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        adapter = PGGraphAdapter(backend=mock_backend)

        import asyncio
        asyncio.run(adapter.connect())

        mock_backend.connect.assert_called_once()

    def test_disconnect_calls_backend_disconnect(self):
        """F05-T052: disconnect委托给后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        adapter = PGGraphAdapter(backend=mock_backend)

        import asyncio
        asyncio.run(adapter.disconnect())

        mock_backend.disconnect.assert_called_once()

    def test_create_tables_calls_backend(self):
        """F05-T053: create_tables委托给后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        adapter = PGGraphAdapter(backend=mock_backend)

        import asyncio
        asyncio.run(adapter.create_tables())

        mock_backend.create_tables.assert_called_once()

    def test_insert_node_delegates_to_backend(self):
        """F05-T054: insert_node委托给后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        adapter = PGGraphAdapter(backend=mock_backend)
        mock_node = MockNode(id="n-001", node_type="chapter", properties={"title": "Test"})

        import asyncio
        asyncio.run(adapter.insert_node(mock_node))

        mock_backend.insert_node.assert_called_once_with(mock_node)

    def test_insert_edge_delegates_to_backend(self):
        """F05-T055: insert_edge委托给后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        adapter = PGGraphAdapter(backend=mock_backend)
        mock_edge = MockEdge(id="e-001", source_id="n-001", target_id="n-002", edge_type="CONTAINS")

        import asyncio
        asyncio.run(adapter.insert_edge(mock_edge))

        mock_backend.insert_edge.assert_called_once_with(mock_edge)

    def test_query_nodes_delegates_to_backend(self):
        """F05-T056: query_nodes委托给后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        mock_backend.query_nodes = AsyncMock(return_value=[{"id": "n-001"}])
        adapter = PGGraphAdapter(backend=mock_backend)

        import asyncio
        result = asyncio.run(adapter.query_nodes(node_type="chapter"))

        mock_backend.query_nodes.assert_called_once_with(node_type="chapter")
        assert len(result) == 1

    def test_query_edges_delegates_to_backend(self):
        """F05-T057: query_edges委托给后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        mock_backend.query_edges = AsyncMock(return_value=[{"id": "e-001"}])
        adapter = PGGraphAdapter(backend=mock_backend)

        import asyncio
        result = asyncio.run(adapter.query_edges(edge_type="CONTAINS"))

        mock_backend.query_edges.assert_called_once_with(edge_type="CONTAINS")
        assert len(result) == 1

    def test_execute_cypher_delegates_to_backend(self):
        """F05-T058: execute_cypher委托给后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        mock_backend.execute_cypher = AsyncMock(return_value=[{"n": {"id": "n-001"}}])
        adapter = PGGraphAdapter(backend=mock_backend)

        import asyncio
        result = asyncio.run(adapter.execute_cypher("MATCH (n) RETURN n"))

        mock_backend.execute_cypher.assert_called_once_with("MATCH (n) RETURN n")
        assert len(result) == 1

    def test_find_path_delegates_to_backend(self):
        """F05-T059: find_path委托给后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        mock_backend.find_path = AsyncMock(return_value=["n-001", "n-002", "n-003"])
        adapter = PGGraphAdapter(backend=mock_backend)

        import asyncio
        result = asyncio.run(adapter.find_path("n-001", "n-003"))

        mock_backend.find_path.assert_called_once_with("n-001", "n-003", edge_types=None, depth=None)
        assert result == ["n-001", "n-002", "n-003"]

    def test_find_path_with_depth(self):
        """F05-T060: find_path支持depth参数"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        mock_backend.find_path = AsyncMock(return_value=["n-001", "n-002"])
        adapter = PGGraphAdapter(backend=mock_backend)

        import asyncio
        result = asyncio.run(adapter.find_path("n-001", "n-002", depth=2))

        mock_backend.find_path.assert_called_once_with("n-001", "n-002", edge_types=None, depth=2)

    def test_get_neighbors_delegates_to_backend(self):
        """F05-T061: get_neighbors委托给后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        mock_backend.get_neighbors = AsyncMock(return_value=[{"id": "n-002"}])
        adapter = PGGraphAdapter(backend=mock_backend)

        import asyncio
        result = asyncio.run(adapter.get_neighbors("n-001"))

        mock_backend.get_neighbors.assert_called_once_with("n-001", depth=1)
        assert len(result) == 1

    def test_get_neighbors_with_depth(self):
        """F05-T062: get_neighbors支持depth参数"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        mock_backend.get_neighbors = AsyncMock(return_value=[{"id": "n-002"}, {"id": "n-003"}])
        adapter = PGGraphAdapter(backend=mock_backend)

        import asyncio
        result = asyncio.run(adapter.get_neighbors("n-001", depth=2))

        mock_backend.get_neighbors.assert_called_once_with("n-001", depth=2)
        assert len(result) == 2

    def test_batch_import_delegates_to_backend(self):
        """F05-T063: batch_import委托给后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        adapter = PGGraphAdapter(backend=mock_backend)
        nodes = [MockNode(id="n-001", node_type="chapter")]
        edges = [MockEdge(id="e-001", source_id="n-001", target_id="n-002", edge_type="CONTAINS")]

        import asyncio
        asyncio.run(adapter.batch_import(nodes, edges))

        mock_backend.batch_import.assert_called_once_with(nodes, edges)

    def test_export_to_cypher_delegates_to_backend(self):
        """F05-T064: export_to_cypher委托给后端"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        mock_backend = AsyncMock()
        mock_backend.export_to_cypher = MagicMock(return_value="CREATE (n:Chapter {id: 'n-001'})")
        adapter = PGGraphAdapter(backend=mock_backend)

        result = adapter.export_to_cypher()

        mock_backend.export_to_cypher.assert_called_once()
        assert "CREATE" in result


class TestPGGraphAdapterStandalone:
    """独立使用PGGraphAdapter测试（不委托）"""

    def test_adapter_can_be_used_without_backend(self):
        """F05-T065: Adapter可以没有后端（用于创建后端）"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        adapter = PGGraphAdapter()
        assert adapter._backend is None

    def test_adapter_can_be_initialized_with_connection_string(self):
        """F05-T066: 使用连接字符串初始化"""
        from f05_knowledge_graph.pg_graph_adapter import PGGraphAdapter

        conn_str = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        adapter = PGGraphAdapter(connection_string=conn_str)
        assert adapter.connection_string == conn_str
