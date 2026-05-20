"""
Knowledge Graph API Route Tests - Full Coverage

Tests all endpoints with proper state isolation and permission coverage.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from api.deps import generate_uuid


@pytest.fixture(autouse=True)
def clear_knowledge_graph_state():
    """Clear in-memory knowledge graph state before each test"""
    from api.routes import knowledge_graph as kg_module
    kg_module._in_memory_nodes.clear()
    kg_module._in_memory_edges.clear()
    kg_module._edge_id_counter = 0
    yield
    kg_module._in_memory_nodes.clear()
    kg_module._in_memory_edges.clear()
    kg_module._edge_id_counter = 0


class TestListNodes:
    """Tests for GET /api/knowledge-graph/nodes"""

    def test_list_nodes_empty(self, test_client, test_db, content_admin_authenticated):
        """Test listing nodes when none exist"""
        token = content_admin_authenticated["access_token"]
        response = test_client.get(
            "/api/knowledge-graph/nodes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_nodes_with_data(self, test_client, test_db, content_admin_authenticated):
        """Test listing nodes with data"""
        token = content_admin_authenticated["access_token"]
        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {"title": "Test"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf",
            },
        )
        response = test_client.get(
            "/api/knowledge-graph/nodes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["node_type"] == "chapter"

    def test_list_nodes_filter_by_type(self, test_client, test_db, content_admin_authenticated):
        """Test filtering nodes by type"""
        token = content_admin_authenticated["access_token"]
        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.get(
            "/api/knowledge-graph/nodes?node_type=chapter",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["node_type"] == "chapter"

    def test_list_nodes_pagination(self, test_client, test_db, content_admin_authenticated):
        """Test pagination parameters"""
        token = content_admin_authenticated["access_token"]
        for i in range(3):
            test_client.post(
                "/api/knowledge-graph/nodes",
                json={"node_type": "term", "properties": {"name": f"Term {i}"}},
                headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
            )
        response = test_client.get(
            "/api/knowledge-graph/nodes?page=1&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestCreateNode:
    """Tests for POST /api/knowledge-graph/nodes"""

    def test_create_node_success(self, test_client, test_db, content_admin_authenticated):
        """Test creating a node"""
        token = content_admin_authenticated["access_token"]
        response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {"name": "Test"}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["node_type"] == "concept"
        assert data["properties"]["name"] == "Test"
        assert "id" in data
        assert "created_at" in data

    def test_create_node_with_all_properties(self, test_client, test_db, content_admin_authenticated):
        """Test creating node with all property fields"""
        token = content_admin_authenticated["access_token"]
        response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={
                "node_type": "term",
                "properties": {"name": "X", "definition": "Y", "domain": "Z"},
            },
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["node_type"] == "term"


class TestGetNode:
    """Tests for GET /api/knowledge-graph/nodes/{node_id}"""

    def test_get_node_success(self, test_client, test_db, content_admin_authenticated):
        """Test getting an existing node"""
        token = content_admin_authenticated["access_token"]
        create_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {"title": "Test"}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        node_id = create_resp.json()["id"]
        response = test_client.get(
            f"/api/knowledge-graph/nodes/{node_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["node_type"] == "chapter"

    def test_get_node_not_found(self, test_client, test_db, content_admin_authenticated):
        """Test getting non-existent node"""
        token = content_admin_authenticated["access_token"]
        response = test_client.get(
            f"/api/knowledge-graph/nodes/{generate_uuid()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


class TestUpdateNode:
    """Tests for PUT /api/knowledge-graph/nodes/{node_id}"""

    def test_update_node_success(self, test_client, test_db, content_admin_authenticated):
        """Test updating node properties"""
        token = content_admin_authenticated["access_token"]
        create_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "term", "properties": {"name": "Original"}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        node_id = create_resp.json()["id"]
        response = test_client.put(
            f"/api/knowledge-graph/nodes/{node_id}",
            json={"new_field": "new_value"},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 200
        assert response.json()["properties"]["new_field"] == "new_value"
        assert response.json()["properties"]["name"] == "Original"

    def test_update_node_not_found(self, test_client, test_db, content_admin_authenticated):
        """Test updating non-existent node"""
        token = content_admin_authenticated["access_token"]
        response = test_client.put(
            f"/api/knowledge-graph/nodes/{generate_uuid()}",
            json={"field": "value"},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 404


class TestDeleteNode:
    """Tests for DELETE /api/knowledge-graph/nodes/{node_id}"""

    def test_delete_node_success(self, test_client, test_db, content_admin_authenticated):
        """Test deleting a node"""
        token = content_admin_authenticated["access_token"]
        create_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        node_id = create_resp.json()["id"]
        response = test_client.delete(
            f"/api/knowledge-graph/nodes/{node_id}",
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_delete_node_not_found(self, test_client, test_db, content_admin_authenticated):
        """Test deleting non-existent node"""
        token = content_admin_authenticated["access_token"]
        response = test_client.delete(
            f"/api/knowledge-graph/nodes/{generate_uuid()}",
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 404

    def test_delete_node_cascades_edges(self, test_client, test_db, content_admin_authenticated):
        """Test that deleting a node removes connected edges"""
        token = content_admin_authenticated["access_token"]
        source_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "a", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        source_id = source_resp.json()["id"]
        target_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "b", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        target_id = target_resp.json()["id"]
        test_client.post(
            "/api/knowledge-graph/edges",
            json={"source_id": source_id, "target_id": target_id, "edge_type": "CONNECTS"},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        test_client.delete(
            f"/api/knowledge-graph/nodes/{source_id}",
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        edges_resp = test_client.get(
            "/api/knowledge-graph/edges",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert len(edges_resp.json()) == 0


class TestListEdges:
    """Tests for GET /api/knowledge-graph/edges"""

    def test_list_edges_empty(self, test_client, test_db, content_admin_authenticated):
        """Test listing edges when none exist"""
        token = content_admin_authenticated["access_token"]
        response = test_client.get(
            "/api/knowledge-graph/edges",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_edges_with_data(self, test_client, test_db, content_admin_authenticated):
        """Test listing edges with data"""
        token = content_admin_authenticated["access_token"]
        source_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "a", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        target_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "b", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_resp.json()["id"],
                "target_id": target_resp.json()["id"],
                "edge_type": "CONTAINS",
            },
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.get(
            "/api/knowledge-graph/edges",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_edges_filter_by_type(self, test_client, test_db, content_admin_authenticated):
        """Test filtering edges by type"""
        token = content_admin_authenticated["access_token"]
        source_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "a", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        target_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "b", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_resp.json()["id"],
                "target_id": target_resp.json()["id"],
                "edge_type": "CONTAINS",
            },
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.get(
            "/api/knowledge-graph/edges?edge_type=CONTAINS",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_edges_filter_by_source(self, test_client, test_db, content_admin_authenticated):
        """Test filtering edges by source_id"""
        token = content_admin_authenticated["access_token"]
        source_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "a", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        target_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "b", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_resp.json()["id"],
                "target_id": target_resp.json()["id"],
                "edge_type": "FOLLOWS",
            },
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.get(
            f"/api/knowledge-graph/edges?source_id={source_resp.json()['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_edges_filter_by_target(self, test_client, test_db, content_admin_authenticated):
        """Test filtering edges by target_id"""
        token = content_admin_authenticated["access_token"]
        source_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "a", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        target_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "b", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_resp.json()["id"],
                "target_id": target_resp.json()["id"],
                "edge_type": "DEFINES",
            },
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.get(
            f"/api/knowledge-graph/edges?target_id={target_resp.json()['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1


class TestCreateEdge:
    """Tests for POST /api/knowledge-graph/edges"""

    def test_create_edge_success(self, test_client, test_db, content_admin_authenticated):
        """Test creating an edge"""
        token = content_admin_authenticated["access_token"]
        source_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        target_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "section", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_resp.json()["id"],
                "target_id": target_resp.json()["id"],
                "edge_type": "CONTAINS",
                "properties": {"weight": 1.0},
            },
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["source_id"] == source_resp.json()["id"]
        assert data["target_id"] == target_resp.json()["id"]
        assert data["edge_type"] == "CONTAINS"
        assert data["properties"]["weight"] == 1.0

    def test_create_edge_source_not_found(self, test_client, test_db, content_admin_authenticated):
        """Test creating edge with non-existent source"""
        token = content_admin_authenticated["access_token"]
        target_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "term", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": generate_uuid(),
                "target_id": target_resp.json()["id"],
                "edge_type": "DEFINES",
            },
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 404
        assert "SOURCE_NODE_NOT_FOUND" in str(response.json())

    def test_create_edge_target_not_found(self, test_client, test_db, content_admin_authenticated):
        """Test creating edge with non-existent target"""
        token = content_admin_authenticated["access_token"]
        source_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_resp.json()["id"],
                "target_id": generate_uuid(),
                "edge_type": "DEFINES",
            },
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 404
        assert "TARGET_NODE_NOT_FOUND" in str(response.json())

    def test_create_edge_without_properties(self, test_client, test_db, content_admin_authenticated):
        """Test creating edge without optional properties"""
        token = content_admin_authenticated["access_token"]
        source_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "a", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        target_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "b", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_resp.json()["id"],
                "target_id": target_resp.json()["id"],
                "edge_type": "USES",
            },
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 201
        assert response.json()["properties"] == {}


class TestDeleteEdge:
    """Tests for DELETE /api/knowledge-graph/edges/{edge_id}"""

    def test_delete_edge_success(self, test_client, test_db, content_admin_authenticated):
        """Test deleting an edge"""
        token = content_admin_authenticated["access_token"]
        source_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "a", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        target_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "b", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        edge_resp = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_resp.json()["id"],
                "target_id": target_resp.json()["id"],
                "edge_type": "FOLLOWS",
            },
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        edge_id = edge_resp.json()["id"]
        response = test_client.delete(
            f"/api/knowledge-graph/edges/{edge_id}",
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_delete_edge_not_found(self, test_client, test_db, content_admin_authenticated):
        """Test deleting non-existent edge"""
        token = content_admin_authenticated["access_token"]
        response = test_client.delete(
            "/api/knowledge-graph/edges/99999",
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 404


class TestQueryGraph:
    """Tests for POST /api/knowledge-graph/query"""

    def test_query_graph_empty(self, test_client, test_db, content_admin_authenticated):
        """Test querying with no matches"""
        token = content_admin_authenticated["access_token"]
        response = test_client.post(
            "/api/knowledge-graph/query",
            json={"query": "nonexistent"},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_nodes"] == 0
        assert data["total_edges"] == 0

    def test_query_graph_match_nodes(self, test_client, test_db, content_admin_authenticated):
        """Test querying matches nodes"""
        token = content_admin_authenticated["access_token"]
        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {"name": "Python Programming"}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.post(
            "/api/knowledge-graph/query",
            json={"query": "Python"},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_nodes"] == 1
        assert data["nodes"][0]["node_type"] == "concept"

    def test_query_graph_match_edges(self, test_client, test_db, content_admin_authenticated):
        """Test querying matches edges"""
        token = content_admin_authenticated["access_token"]
        source_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "a", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        target_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "b", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_resp.json()["id"],
                "target_id": target_resp.json()["id"],
                "edge_type": "CONTAINS",
            },
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.post(
            "/api/knowledge-graph/query",
            json={"query": "CONTAINS"},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 200
        assert response.json()["total_edges"] == 1

    def test_query_graph_with_node_types_filter(self, test_client, test_db, content_admin_authenticated):
        """Test querying with node_types filter"""
        token = content_admin_authenticated["access_token"]
        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {"title": "Intro"}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "section", "properties": {"title": "Intro"}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.post(
            "/api/knowledge-graph/query",
            json={"query": "Intro", "node_types": ["chapter"]},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_nodes"] == 1
        assert data["nodes"][0]["node_type"] == "chapter"

    def test_query_graph_with_limit(self, test_client, test_db, content_admin_authenticated):
        """Test querying with limit"""
        token = content_admin_authenticated["access_token"]
        for i in range(5):
            test_client.post(
                "/api/knowledge-graph/nodes",
                json={"node_type": "term", "properties": {"name": f"Term {i}"}},
                headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
            )
        response = test_client.post(
            "/api/knowledge-graph/query",
            json={"query": "Term", "limit": 2},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) == 2
        assert data["total_nodes"] == 5

    def test_query_graph_with_max_depth(self, test_client, test_db, content_admin_authenticated):
        """Test querying with max_depth parameter"""
        token = content_admin_authenticated["access_token"]
        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {"name": "AI"}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.post(
            "/api/knowledge-graph/query",
            json={"query": "AI", "max_depth": 5},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestGraphStats:
    """Tests for GET /api/knowledge-graph/stats"""

    def test_get_stats_empty(self, test_client, test_db, content_admin_authenticated):
        """Test getting stats when graph is empty"""
        token = content_admin_authenticated["access_token"]
        response = test_client.get(
            "/api/knowledge-graph/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_nodes"] == 0
        assert data["total_edges"] == 0
        assert data["node_types"] == {}
        assert data["edge_types"] == {}

    def test_get_stats_with_nodes(self, test_client, test_db, content_admin_authenticated):
        """Test getting stats with nodes"""
        token = content_admin_authenticated["access_token"]
        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.get(
            "/api/knowledge-graph/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_nodes"] == 3
        assert data["node_types"]["chapter"] == 2
        assert data["node_types"]["concept"] == 1

    def test_get_stats_with_edges(self, test_client, test_db, content_admin_authenticated):
        """Test getting stats with edges"""
        token = content_admin_authenticated["access_token"]
        source_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "a", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        target_resp = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "b", "properties": {}},
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_resp.json()["id"],
                "target_id": target_resp.json()["id"],
                "edge_type": "CONTAINS",
            },
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        response = test_client.get(
            "/api/knowledge-graph/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_edges"] == 1
        assert data["edge_types"]["CONTAINS"] == 1


class TestInitializeGraph:
    """Tests for POST /api/knowledge-graph/initialize"""

    def test_initialize_graph_success(self, test_client, test_db, content_admin_authenticated):
        """Test initializing graph with sample data"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]
        from tests.api.conftest import create_test_project, create_test_chapter
        project = create_test_project(test_db, owner_id=user.id, name="Any Name")
        chapter1 = create_test_chapter(test_db, project_id="demo-project", title="Chapter 1")
        chapter2 = create_test_chapter(test_db, project_id="demo-project", title="Chapter 2")
        test_db._chapters[chapter1["id"]]["project_id"] = "demo-project"
        test_db._chapters[chapter2["id"]]["project_id"] = "demo-project"
        response = test_client.post(
            "/api/knowledge-graph/initialize",
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_initialize_graph_viewer_forbidden(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot initialize graph"""
        token = test_user_authenticated["access_token"]
        response = test_client.post(
            "/api/knowledge-graph/initialize",
            headers={"Authorization": f"Bearer {token}", "X-CSRF-Token": "test_csrf"},
        )
        assert response.status_code == 403


class TestUnauthorized:
    """Tests for unauthorized access"""

    def test_list_nodes_unauthorized(self, test_client):
        """Test listing nodes without auth"""
        response = test_client.get("/api/knowledge-graph/nodes")
        assert response.status_code == 401

    def test_create_node_unauthorized(self, test_client):
        """Test creating node without auth"""
        response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "test", "properties": {}},
        )
        assert response.status_code == 401

    def test_get_node_unauthorized(self, test_client):
        """Test getting node without auth"""
        response = test_client.get("/api/knowledge-graph/nodes/some-id")
        assert response.status_code == 401

    def test_update_node_unauthorized(self, test_client):
        """Test updating node without auth"""
        response = test_client.put(
            "/api/knowledge-graph/nodes/some-id",
            json={"field": "value"},
        )
        assert response.status_code == 401

    def test_delete_node_unauthorized(self, test_client):
        """Test deleting node without auth"""
        response = test_client.delete("/api/knowledge-graph/nodes/some-id")
        assert response.status_code == 401

    def test_list_edges_unauthorized(self, test_client):
        """Test listing edges without auth"""
        response = test_client.get("/api/knowledge-graph/edges")
        assert response.status_code == 401

    def test_create_edge_unauthorized(self, test_client):
        """Test creating edge without auth"""
        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={"source_id": "a", "target_id": "b", "edge_type": "TEST"},
        )
        assert response.status_code == 401

    def test_delete_edge_unauthorized(self, test_client):
        """Test deleting edge without auth"""
        response = test_client.delete("/api/knowledge-graph/edges/1")
        assert response.status_code == 401

    def test_query_graph_unauthorized(self, test_client):
        """Test querying graph without auth"""
        response = test_client.post(
            "/api/knowledge-graph/query",
            json={"query": "test"},
        )
        assert response.status_code == 401

    def test_get_stats_unauthorized(self, test_client):
        """Test getting stats without auth"""
        response = test_client.get("/api/knowledge-graph/stats")
        assert response.status_code == 401

    def test_initialize_unauthorized(self, test_client):
        """Test initializing without auth"""
        response = test_client.post("/api/knowledge-graph/initialize")
        assert response.status_code == 401