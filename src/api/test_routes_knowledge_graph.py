"""Comprehensive tests for api/routes/knowledge_graph.py"""

import os
import sys
import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import api.routes.knowledge_graph as kg_module
from api.deps import User
from api.routes.knowledge_graph import EdgeCreate, GraphQueryRequest, NodeCreate


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    """Reset in-memory state before each test."""
    kg_module._in_memory_nodes.clear()
    kg_module._in_memory_edges.clear()
    kg_module._edge_id_counter = 0
    yield


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return User(
        id="test-user-123",
        username="testuser",
        email="test@example.com",
        role="content_admin"
    )


@pytest.fixture
def mock_system_admin():
    """Create a mock system admin user."""
    return User(
        id="admin-user-456",
        username="adminuser",
        email="admin@example.com",
        role="system_admin"
    )


@pytest.fixture
def sample_node():
    """Create a sample node in memory."""
    node_id = str(uuid.uuid4())
    node = {
        "id": node_id,
        "node_type": "chapter",
        "properties": {"title": "Test Chapter", "order": 1},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    kg_module._in_memory_nodes[node_id] = node
    return node


@pytest.fixture
def sample_edge(sample_node):
    """Create a sample edge in memory."""
    kg_module._edge_id_counter += 1
    edge_id = kg_module._edge_id_counter
    edge = {
        "id": edge_id,
        "source_id": sample_node["id"],
        "target_id": str(uuid.uuid4()),
        "edge_type": "CONTAINS",
        "properties": {},
        "created_at": datetime.utcnow().isoformat(),
    }
    kg_module._in_memory_edges[edge_id] = edge
    return edge


class TestListNodes:
    """Tests for GET /api/knowledge-graph/nodes"""

    @pytest.mark.asyncio
    async def test_list_nodes_empty(self, mock_user):
        result = await kg_module.list_nodes(
            node_type=None, page=1, per_page=50,
            user=mock_user, db=AsyncMock()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_nodes_with_data(self, mock_user, sample_node):
        result = await kg_module.list_nodes(
            node_type=None, page=1, per_page=50,
            user=mock_user, db=AsyncMock()
        )
        assert len(result) == 1
        assert result[0].id == sample_node["id"]

    @pytest.mark.asyncio
    async def test_list_nodes_filter_by_type(self, mock_user):
        node_id = str(uuid.uuid4())
        kg_module._in_memory_nodes[node_id] = {
            "id": node_id,
            "node_type": "concept",
            "properties": {"name": "Test Concept"},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        result = await kg_module.list_nodes(
            node_type="concept", page=1, per_page=50,
            user=mock_user, db=AsyncMock()
        )
        assert len(result) == 1
        assert result[0].node_type == "concept"

    @pytest.mark.asyncio
    async def test_list_nodes_pagination(self, mock_user):
        for i in range(10):
            node_id = str(uuid.uuid4())
            kg_module._in_memory_nodes[node_id] = {
                "id": node_id, "node_type": "chapter",
                "properties": {"title": f"Chapter {i}"},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        result_page1 = await kg_module.list_nodes(
            node_type=None, page=1, per_page=5,
            user=mock_user, db=AsyncMock()
        )
        result_page2 = await kg_module.list_nodes(
            node_type=None, page=2, per_page=5,
            user=mock_user, db=AsyncMock()
        )
        assert len(result_page1) == 5
        assert len(result_page2) == 5

    @pytest.mark.asyncio
    async def test_list_nodes_type_no_match(self, mock_user):
        result = await kg_module.list_nodes(
            node_type="nonexistent_type", page=1, per_page=50,
            user=mock_user, db=AsyncMock()
        )
        assert result == []


class TestCreateNode:
    """Tests for POST /api/knowledge-graph/nodes"""

    @pytest.mark.asyncio
    async def test_create_node_success(self, mock_user):
        node_data = NodeCreate(
            node_type="chapter",
            properties={"title": "New Chapter", "order": 1}
        )
        result = await kg_module.create_node(
            node_data=node_data,
            user=mock_user, db=AsyncMock()
        )
        assert result.id is not None
        assert result.node_type == "chapter"
        assert str(result.id) in kg_module._in_memory_nodes

    @pytest.mark.asyncio
    async def test_create_node_different_types(self, mock_user):
        for node_type in ["chapter", "section", "concept", "term"]:
            node_data = NodeCreate(
                node_type=node_type,
                properties={"name": f"Test {node_type}"}
            )
            result = await kg_module.create_node(
                node_data=node_data,
                user=mock_user, db=AsyncMock()
            )
            assert result.node_type == node_type


class TestGetNode:
    """Tests for GET /api/knowledge-graph/nodes/{node_id}"""

    @pytest.mark.asyncio
    async def test_get_node_success(self, mock_user, sample_node):
        result = await kg_module.get_node(
            node_id=sample_node["id"],
            user=mock_user, db=AsyncMock()
        )
        assert result.id == sample_node["id"]

    @pytest.mark.asyncio
    async def test_get_node_not_found(self, mock_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await kg_module.get_node(
                node_id=str(uuid.uuid4()),
                user=mock_user, db=AsyncMock()
            )
        assert exc_info.value.status_code == 404
        assert "NODE_NOT_FOUND" in str(exc_info.value.detail)


class TestUpdateNode:
    """Tests for PUT /api/knowledge-graph/nodes/{node_id}"""

    @pytest.mark.asyncio
    async def test_update_node_success(self, mock_user, sample_node):
        result = await kg_module.update_node(
            node_id=sample_node["id"],
            properties={"title": "Updated Title", "author": "Test Author"},
            user=mock_user, db=AsyncMock()
        )
        assert result.properties["title"] == "Updated Title"
        assert result.properties["author"] == "Test Author"

    @pytest.mark.asyncio
    async def test_update_node_not_found(self, mock_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await kg_module.update_node(
                node_id=str(uuid.uuid4()),
                properties={"title": "Updated"},
                user=mock_user, db=AsyncMock()
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_node_preserves_existing_properties(self, mock_user):
        node_id = str(uuid.uuid4())
        kg_module._in_memory_nodes[node_id] = {
            "id": node_id, "node_type": "chapter",
            "properties": {"title": "Original Title", "order": 1},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        result = await kg_module.update_node(
            node_id=node_id,
            properties={"author": "New Author"},
            user=mock_user, db=AsyncMock()
        )
        assert result.properties["title"] == "Original Title"
        assert result.properties["order"] == 1
        assert result.properties["author"] == "New Author"


class TestDeleteNode:
    """Tests for DELETE /api/knowledge-graph/nodes/{node_id}"""

    @pytest.mark.asyncio
    async def test_delete_node_success(self, mock_user, sample_node):
        result = await kg_module.delete_node(
            node_id=sample_node["id"],
            user=mock_user, db=AsyncMock()
        )
        assert result.success is True
        assert sample_node["id"] not in kg_module._in_memory_nodes

    @pytest.mark.asyncio
    async def test_delete_node_also_deletes_connected_edges(self, mock_user, sample_node):
        kg_module._edge_id_counter += 1
        edge_id = kg_module._edge_id_counter
        kg_module._in_memory_edges[edge_id] = {
            "id": edge_id, "source_id": sample_node["id"],
            "target_id": str(uuid.uuid4()), "edge_type": "CONTAINS",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
        }
        kg_module._edge_id_counter += 1
        edge_id2 = kg_module._edge_id_counter
        kg_module._in_memory_edges[edge_id2] = {
            "id": edge_id2, "source_id": str(uuid.uuid4()),
            "target_id": sample_node["id"], "edge_type": "REFERENCES",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
        }
        initial_edge_count = len(kg_module._in_memory_edges)
        await kg_module.delete_node(
            node_id=sample_node["id"],
            user=mock_user, db=AsyncMock()
        )
        assert len(kg_module._in_memory_edges) == initial_edge_count - 2

    @pytest.mark.asyncio
    async def test_delete_node_not_found(self, mock_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await kg_module.delete_node(
                node_id=str(uuid.uuid4()),
                user=mock_user, db=AsyncMock()
            )
        assert exc_info.value.status_code == 404


class TestListEdges:
    """Tests for GET /api/knowledge-graph/edges"""

    @pytest.mark.asyncio
    async def test_list_edges_empty(self, mock_user):
        result = await kg_module.list_edges(
            edge_type=None, source_id=None, target_id=None,
            page=1, per_page=50, user=mock_user, db=AsyncMock()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_edges_with_data(self, mock_user, sample_edge):
        result = await kg_module.list_edges(
            edge_type=None, source_id=None, target_id=None,
            page=1, per_page=50, user=mock_user, db=AsyncMock()
        )
        assert len(result) == 1
        assert result[0].id == sample_edge["id"]

    @pytest.mark.asyncio
    async def test_list_edges_filter_by_type(self, mock_user):
        kg_module._edge_id_counter += 1
        edge_id = kg_module._edge_id_counter
        kg_module._in_memory_edges[edge_id] = {
            "id": edge_id, "source_id": str(uuid.uuid4()),
            "target_id": str(uuid.uuid4()), "edge_type": "DEFINES",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
        }
        result = await kg_module.list_edges(
            edge_type="DEFINES", source_id=None, target_id=None,
            page=1, per_page=50, user=mock_user, db=AsyncMock()
        )
        assert len(result) == 1
        assert result[0].edge_type == "DEFINES"

    @pytest.mark.asyncio
    async def test_list_edges_filter_by_source_id(self, mock_user, sample_node):
        kg_module._edge_id_counter += 1
        edge_id = kg_module._edge_id_counter
        kg_module._in_memory_edges[edge_id] = {
            "id": edge_id, "source_id": sample_node["id"],
            "target_id": str(uuid.uuid4()), "edge_type": "CONTAINS",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
        }
        result = await kg_module.list_edges(
            edge_type=None, source_id=sample_node["id"], target_id=None,
            page=1, per_page=50, user=mock_user, db=AsyncMock()
        )
        assert len(result) == 1
        assert result[0].source_id == sample_node["id"]

    @pytest.mark.asyncio
    async def test_list_edges_filter_by_target_id(self, mock_user, sample_node):
        kg_module._edge_id_counter += 1
        edge_id = kg_module._edge_id_counter
        kg_module._in_memory_edges[edge_id] = {
            "id": edge_id, "source_id": str(uuid.uuid4()),
            "target_id": sample_node["id"], "edge_type": "REFERENCES",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
        }
        result = await kg_module.list_edges(
            edge_type=None, source_id=None, target_id=sample_node["id"],
            page=1, per_page=50, user=mock_user, db=AsyncMock()
        )
        assert len(result) == 1
        assert result[0].target_id == sample_node["id"]

    @pytest.mark.asyncio
    async def test_list_edges_pagination(self, mock_user):
        source_node_id = str(uuid.uuid4())
        target_node_id = str(uuid.uuid4())
        kg_module._in_memory_nodes[source_node_id] = {
            "id": source_node_id, "node_type": "chapter",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        kg_module._in_memory_nodes[target_node_id] = {
            "id": target_node_id, "node_type": "chapter",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        for _i in range(10):
            kg_module._edge_id_counter += 1
            edge_id = kg_module._edge_id_counter
            kg_module._in_memory_edges[edge_id] = {
                "id": edge_id, "source_id": source_node_id,
                "target_id": target_node_id, "edge_type": "CONTAINS",
                "properties": {}, "created_at": datetime.utcnow().isoformat(),
            }
        result_page1 = await kg_module.list_edges(
            edge_type=None, source_id=None, target_id=None,
            page=1, per_page=5, user=mock_user, db=AsyncMock()
        )
        result_page2 = await kg_module.list_edges(
            edge_type=None, source_id=None, target_id=None,
            page=2, per_page=5, user=mock_user, db=AsyncMock()
        )
        assert len(result_page1) == 5
        assert len(result_page2) == 5


class TestCreateEdge:
    """Tests for POST /api/knowledge-graph/edges"""

    @pytest.mark.asyncio
    async def test_create_edge_success(self, mock_user):
        source_node_id = str(uuid.uuid4())
        target_node_id = str(uuid.uuid4())
        kg_module._in_memory_nodes[source_node_id] = {
            "id": source_node_id, "node_type": "chapter",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        kg_module._in_memory_nodes[target_node_id] = {
            "id": target_node_id, "node_type": "section",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        edge_data = EdgeCreate(
            source_id=source_node_id, target_id=target_node_id,
            edge_type="CONTAINS", properties={"weight": 1.0}
        )
        result = await kg_module.create_edge(
            edge_data=edge_data, user=mock_user, db=AsyncMock()
        )
        assert result.source_id == source_node_id
        assert result.target_id == target_node_id
        assert result.edge_type == "CONTAINS"

    @pytest.mark.asyncio
    async def test_create_edge_source_not_found(self, mock_user):
        from fastapi import HTTPException
        edge_data = EdgeCreate(
            source_id=str(uuid.uuid4()), target_id=str(uuid.uuid4()),
            edge_type="CONTAINS"
        )
        with pytest.raises(HTTPException) as exc_info:
            await kg_module.create_edge(
                edge_data=edge_data, user=mock_user, db=AsyncMock()
            )
        assert exc_info.value.status_code == 404
        assert "SOURCE_NODE_NOT_FOUND" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_edge_target_not_found(self, mock_user):
        from fastapi import HTTPException
        source_node_id = str(uuid.uuid4())
        kg_module._in_memory_nodes[source_node_id] = {
            "id": source_node_id, "node_type": "chapter",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        edge_data = EdgeCreate(
            source_id=source_node_id, target_id=str(uuid.uuid4()),
            edge_type="CONTAINS"
        )
        with pytest.raises(HTTPException) as exc_info:
            await kg_module.create_edge(
                edge_data=edge_data, user=mock_user, db=AsyncMock()
            )
        assert exc_info.value.status_code == 404
        assert "TARGET_NODE_NOT_FOUND" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_edge_without_properties(self, mock_user):
        source_node_id = str(uuid.uuid4())
        target_node_id = str(uuid.uuid4())
        kg_module._in_memory_nodes[source_node_id] = {
            "id": source_node_id, "node_type": "chapter",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        kg_module._in_memory_nodes[target_node_id] = {
            "id": target_node_id, "node_type": "section",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        edge_data = EdgeCreate(
            source_id=source_node_id, target_id=target_node_id, edge_type="FOLLOWS"
        )
        result = await kg_module.create_edge(
            edge_data=edge_data, user=mock_user, db=AsyncMock()
        )
        assert result.properties == {}


class TestDeleteEdge:
    """Tests for DELETE /api/knowledge-graph/edges/{edge_id}"""

    @pytest.mark.asyncio
    async def test_delete_edge_success(self, mock_user, sample_edge):
        result = await kg_module.delete_edge(
            edge_id=sample_edge["id"], user=mock_user, db=AsyncMock()
        )
        assert result.success is True
        assert sample_edge["id"] not in kg_module._in_memory_edges

    @pytest.mark.asyncio
    async def test_delete_edge_not_found(self, mock_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await kg_module.delete_edge(
                edge_id=99999, user=mock_user, db=AsyncMock()
            )
        assert exc_info.value.status_code == 404
        assert "EDGE_NOT_FOUND" in str(exc_info.value.detail)


class TestQueryGraph:
    """Tests for POST /api/knowledge-graph/query"""

    @pytest.mark.asyncio
    async def test_query_graph_by_node_type(self, mock_user):
        node_id = str(uuid.uuid4())
        kg_module._in_memory_nodes[node_id] = {
            "id": node_id, "node_type": "concept",
            "properties": {"name": "Test Concept"},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        query_request = GraphQueryRequest(
            query="concept", node_types=["concept"],
            max_depth=3, limit=100
        )
        result = await kg_module.query_graph(
            query_request=query_request, user=mock_user, db=AsyncMock()
        )
        assert result.success is True
        assert result.total_nodes == 1

    @pytest.mark.asyncio
    async def test_query_graph_by_property(self, mock_user):
        node_id = str(uuid.uuid4())
        kg_module._in_memory_nodes[node_id] = {
            "id": node_id, "node_type": "chapter",
            "properties": {"title": "Introduction to Python", "pages": 42},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        query_request = GraphQueryRequest(
            query="Python", max_depth=3, limit=100
        )
        result = await kg_module.query_graph(
            query_request=query_request, user=mock_user, db=AsyncMock()
        )
        assert result.success is True
        assert result.total_nodes == 1

    @pytest.mark.asyncio
    async def test_query_graph_by_edge_type(self, mock_user):
        kg_module._edge_id_counter += 1
        edge_id = kg_module._edge_id_counter
        kg_module._in_memory_edges[edge_id] = {
            "id": edge_id, "source_id": str(uuid.uuid4()),
            "target_id": str(uuid.uuid4()), "edge_type": "DEFINES",
            "properties": {}, "created_at": datetime.utcnow().isoformat(),
        }
        query_request = GraphQueryRequest(
            query="DEFINES", max_depth=3, limit=100
        )
        result = await kg_module.query_graph(
            query_request=query_request, user=mock_user, db=AsyncMock()
        )
        assert result.success is True
        assert result.total_edges == 1

    @pytest.mark.asyncio
    async def test_query_graph_with_node_types_filter(self, mock_user):
        for node_type in ["chapter", "concept", "term"]:
            node_id = str(uuid.uuid4())
            kg_module._in_memory_nodes[node_id] = {
                "id": node_id, "node_type": node_type,
                "properties": {"name": f"Test {node_type}"},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        query_request = GraphQueryRequest(
            query="test", node_types=["chapter", "term"],
            max_depth=3, limit=100
        )
        result = await kg_module.query_graph(
            query_request=query_request, user=mock_user, db=AsyncMock()
        )
        assert result.success is True
        assert result.total_nodes == 2

    @pytest.mark.asyncio
    async def test_query_graph_respects_limit(self, mock_user):
        for i in range(20):
            node_id = str(uuid.uuid4())
            kg_module._in_memory_nodes[node_id] = {
                "id": node_id, "node_type": "concept",
                "properties": {"name": f"Concept {i}"},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        query_request = GraphQueryRequest(
            query="concept", max_depth=3, limit=5
        )
        result = await kg_module.query_graph(
            query_request=query_request, user=mock_user, db=AsyncMock()
        )
        assert len(result.nodes) == 5
        assert result.total_nodes == 20

    @pytest.mark.asyncio
    async def test_query_graph_no_matches(self, mock_user):
        query_request = GraphQueryRequest(
            query="nonexistent_query_term_xyz", max_depth=3, limit=100
        )
        result = await kg_module.query_graph(
            query_request=query_request, user=mock_user, db=AsyncMock()
        )
        assert result.success is True
        assert result.total_nodes == 0
        assert result.total_edges == 0


class TestGetGraphStats:
    """Tests for GET /api/knowledge-graph/stats"""

    @pytest.mark.asyncio
    async def test_get_graph_stats_empty(self, mock_user):
        result = await kg_module.get_graph_stats(
            user=mock_user, db=AsyncMock()
        )
        assert result["total_nodes"] == 0
        assert result["total_edges"] == 0
        assert result["node_types"] == {}
        assert result["edge_types"] == {}

    @pytest.mark.asyncio
    async def test_get_graph_stats_with_data(self, mock_user, sample_node, sample_edge):
        result = await kg_module.get_graph_stats(
            user=mock_user, db=AsyncMock()
        )
        assert result["total_nodes"] == 1
        assert result["total_edges"] == 1
        assert result["node_types"]["chapter"] == 1
        assert result["edge_types"]["CONTAINS"] == 1

    @pytest.mark.asyncio
    async def test_get_graph_stats_multiple_types(self, mock_user):
        for node_type in ["chapter", "chapter", "concept", "term"]:
            node_id = str(uuid.uuid4())
            kg_module._in_memory_nodes[node_id] = {
                "id": node_id, "node_type": node_type,
                "properties": {}, "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        for edge_type in ["CONTAINS", "CONTAINS", "DEFINES"]:
            kg_module._edge_id_counter += 1
            edge_id = kg_module._edge_id_counter
            kg_module._in_memory_edges[edge_id] = {
                "id": edge_id, "source_id": str(uuid.uuid4()),
                "target_id": str(uuid.uuid4()), "edge_type": edge_type,
                "properties": {}, "created_at": datetime.utcnow().isoformat(),
            }
        result = await kg_module.get_graph_stats(
            user=mock_user, db=AsyncMock()
        )
        assert result["total_nodes"] == 4
        assert result["total_edges"] == 3
        assert result["node_types"]["chapter"] == 2
        assert result["edge_types"]["CONTAINS"] == 2


class TestInitializeGraph:
    """Tests for POST /api/knowledge-graph/initialize"""

    @pytest.mark.asyncio
    async def test_initialize_graph_empty_chapters(self, mock_system_admin):
        from unittest.mock import MagicMock
        mock_db = MagicMock()
        mock_db.list_chapters_by_project.return_value = []
        result = await kg_module.initialize_graph_sample_data(
            user=mock_system_admin, db=mock_db
        )
        assert result.success is True
        assert len(kg_module._in_memory_nodes) == 0

    @pytest.mark.asyncio
    async def test_initialize_graph_with_chapters(self, mock_system_admin):
        from unittest.mock import MagicMock
        mock_chapters = [
            {"id": "ch-1", "title": "Chapter 1", "order_num": 1},
            {"id": "ch-2", "title": "Chapter 2", "order_num": 2},
            {"id": "ch-3", "title": "Chapter 3", "order_num": 3},
        ]
        mock_db = MagicMock()
        mock_db.list_chapters_by_project.return_value = mock_chapters
        result = await kg_module.initialize_graph_sample_data(
            user=mock_system_admin, db=mock_db
        )
        assert result.success is True
        assert len(kg_module._in_memory_nodes) == 3
        assert "ch-1" in kg_module._in_memory_nodes
        assert kg_module._in_memory_nodes["ch-1"]["node_type"] == "chapter"
        assert kg_module._in_memory_nodes["ch-1"]["properties"]["title"] == "Chapter 1"
