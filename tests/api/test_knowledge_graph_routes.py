"""
Additional Knowledge Graph API Tests for Higher Coverage

Tests additional endpoints and edge cases for knowledge graph routes.
"""


from api.deps import generate_uuid


class TestKnowledgeGraphNodesAdditional:
    """Additional tests for knowledge graph node endpoints"""

    def test_list_nodes_empty(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test listing nodes when none exist"""
        token = content_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/knowledge-graph/nodes",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_nodes_pagination(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test listing nodes with pagination"""
        token = content_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/knowledge-graph/nodes?page=1&per_page=10",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_nodes_filter_by_type(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test listing nodes filtered by type"""
        token = content_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/knowledge-graph/nodes?node_type=chapter",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_node_full(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test creating node with all fields"""
        token = content_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={
                "node_type": "concept",
                "properties": {
                    "name": "Test Concept",
                    "description": "A test concept",
                },
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["node_type"] == "concept"
        assert data["properties"]["name"] == "Test Concept"

    def test_get_node_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test getting non-existent node"""
        token = content_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.get(
            f"/api/knowledge-graph/nodes/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_update_node_success(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test updating node properties"""
        token = content_admin_authenticated["access_token"]

        create_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={
                "node_type": "term",
                "properties": {"name": "Original"},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        node_id = create_response.json()["id"]

        response = test_client.put(
            f"/api/knowledge-graph/nodes/{node_id}",
            json={"updated_field": "new_value"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["properties"]["updated_field"] == "new_value"

    def test_update_node_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test updating non-existent node"""
        token = content_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.put(
            f"/api/knowledge-graph/nodes/{fake_id}",
            json={"field": "value"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_delete_node_success(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test deleting a node"""
        token = content_admin_authenticated["access_token"]

        create_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={
                "node_type": "chapter",
                "properties": {"title": "To Delete"},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        node_id = create_response.json()["id"]

        response = test_client.delete(
            f"/api/knowledge-graph/nodes/{node_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_node_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test deleting non-existent node"""
        token = content_admin_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.delete(
            f"/api/knowledge-graph/nodes/{fake_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404


class TestKnowledgeGraphEdgesMore:
    """More tests for knowledge graph edge endpoints"""

    def test_list_edges_empty(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test listing edges when none exist"""
        token = content_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/knowledge-graph/edges",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_edges_filter_by_type(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test listing edges filtered by type"""
        token = content_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/knowledge-graph/edges?edge_type=CONTAINS",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_edge_source_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test creating edge with non-existent source node"""
        token = content_admin_authenticated["access_token"]

        target_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "term", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        target_id = target_response.json()["id"]

        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": generate_uuid(),
                "target_id": target_id,
                "edge_type": "DEFINES",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404
        assert "SOURCE_NODE_NOT_FOUND" in str(response.json())

    def test_create_edge_target_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test creating edge with non-existent target node"""
        token = content_admin_authenticated["access_token"]

        source_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        source_id = source_response.json()["id"]

        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_id,
                "target_id": generate_uuid(),
                "edge_type": "DEFINES",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404
        assert "TARGET_NODE_NOT_FOUND" in str(response.json())

    def test_create_edge_success(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test successfully creating an edge"""
        token = content_admin_authenticated["access_token"]

        source_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {"title": "Chapter 1"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        source_id = source_response.json()["id"]

        target_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "section", "properties": {"title": "Section 1"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        target_id = target_response.json()["id"]

        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_id,
                "target_id": target_id,
                "edge_type": "CONTAINS",
                "properties": {"weight": 1.0},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["source_id"] == source_id
        assert data["target_id"] == target_id
        assert data["edge_type"] == "CONTAINS"

    def test_delete_edge_success(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test deleting an edge"""
        token = content_admin_authenticated["access_token"]

        source_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "a", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        source_id = source_response.json()["id"]

        target_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "b", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        target_id = target_response.json()["id"]

        edge_response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_id,
                "target_id": target_id,
                "edge_type": "FOLLOWS",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        edge_id = edge_response.json()["id"]

        response = test_client.delete(
            f"/api/knowledge-graph/edges/{edge_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_edge_not_found(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test deleting non-existent edge"""
        token = content_admin_authenticated["access_token"]

        response = test_client.delete(
            "/api/knowledge-graph/edges/99999",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_update_node_success(
        self, test_client, test_db, editor_authenticated
    ):
        """Test updating node properties"""
        token = editor_authenticated["access_token"]

        create_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={
                "node_type": "term",
                "properties": {"name": "Original"},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        node_id = create_response.json()["id"]

        response = test_client.put(
            f"/api/knowledge-graph/nodes/{node_id}",
            json={"updated_field": "new_value"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["properties"]["updated_field"] == "new_value"

    def test_update_node_not_found(
        self, test_client, test_db, editor_authenticated
    ):
        """Test updating non-existent node"""
        token = editor_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.put(
            f"/api/knowledge-graph/nodes/{fake_id}",
            json={"field": "value"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404

    def test_delete_node_success(
        self, test_client, test_db, editor_authenticated
    ):
        """Test deleting a node"""
        token = editor_authenticated["access_token"]

        create_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={
                "node_type": "chapter",
                "properties": {"title": "To Delete"},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        node_id = create_response.json()["id"]

        response = test_client.delete(
            f"/api/knowledge-graph/nodes/{node_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_node_not_found(
        self, test_client, test_db, editor_authenticated
    ):
        """Test deleting non-existent node"""
        token = editor_authenticated["access_token"]
        fake_id = generate_uuid()

        response = test_client.delete(
            f"/api/knowledge-graph/nodes/{fake_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404


class TestKnowledgeGraphEdgesAdditional:
    """Additional tests for knowledge graph edge endpoints"""

    def test_list_edges_empty(
        self, test_client, test_db, editor_authenticated
    ):
        """Test listing edges when none exist"""
        token = editor_authenticated["access_token"]

        response = test_client.get(
            "/api/knowledge-graph/edges",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_edges_filter_by_type(
        self, test_client, test_db, editor_authenticated
    ):
        """Test listing edges filtered by type"""
        token = editor_authenticated["access_token"]

        response = test_client.get(
            "/api/knowledge-graph/edges?edge_type=CONTAINS",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_edge_source_not_found(
        self, test_client, test_db, editor_authenticated
    ):
        """Test creating edge with non-existent source node"""
        token = editor_authenticated["access_token"]

        target_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "term", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        target_id = target_response.json()["id"]

        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": generate_uuid(),
                "target_id": target_id,
                "edge_type": "DEFINES",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404
        assert "SOURCE_NODE_NOT_FOUND" in str(response.json())

    def test_create_edge_target_not_found(
        self, test_client, test_db, editor_authenticated
    ):
        """Test creating edge with non-existent target node"""
        token = editor_authenticated["access_token"]

        source_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        source_id = source_response.json()["id"]

        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_id,
                "target_id": generate_uuid(),
                "edge_type": "DEFINES",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404
        assert "TARGET_NODE_NOT_FOUND" in str(response.json())

    def test_create_edge_success(
        self, test_client, test_db, editor_authenticated
    ):
        """Test successfully creating an edge"""
        token = editor_authenticated["access_token"]

        source_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {"title": "Chapter 1"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        source_id = source_response.json()["id"]

        target_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "section", "properties": {"title": "Section 1"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        target_id = target_response.json()["id"]

        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_id,
                "target_id": target_id,
                "edge_type": "CONTAINS",
                "properties": {"weight": 1.0},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["source_id"] == source_id
        assert data["target_id"] == target_id
        assert data["edge_type"] == "CONTAINS"

    def test_delete_edge_success(
        self, test_client, test_db, editor_authenticated
    ):
        """Test deleting an edge"""
        token = editor_authenticated["access_token"]

        source_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "a", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        source_id = source_response.json()["id"]

        target_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "b", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        target_id = target_response.json()["id"]

        edge_response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_id,
                "target_id": target_id,
                "edge_type": "FOLLOWS",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        edge_id = edge_response.json()["id"]

        response = test_client.delete(
            f"/api/knowledge-graph/edges/{edge_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_edge_not_found(
        self, test_client, test_db, editor_authenticated
    ):
        """Test deleting non-existent edge"""
        token = editor_authenticated["access_token"]

        response = test_client.delete(
            "/api/knowledge-graph/edges/99999",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404


class TestKnowledgeGraphQuery:
    """Tests for graph query endpoint"""

    def test_query_graph_empty_results(
        self, test_client, test_db, editor_authenticated
    ):
        """Test querying graph with no matches"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/knowledge-graph/query",
            json={"query": "nonexistent"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_nodes"] == 0
        assert data["total_edges"] == 0

    def test_query_graph_with_filters(
        self, test_client, test_db, editor_authenticated
    ):
        """Test querying graph with node type filter"""
        token = editor_authenticated["access_token"]

        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {"name": "Python"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        response = test_client.post(
            "/api/knowledge-graph/query",
            json={
                "query": "Python",
                "node_types": ["concept"],
                "max_depth": 3,
                "limit": 10,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_query_graph_limit(
        self, test_client, test_db, editor_authenticated
    ):
        """Test querying graph with limit parameter"""
        token = editor_authenticated["access_token"]

        for i in range(5):
            test_client.post(
                "/api/knowledge-graph/nodes",
                json={"node_type": "term", "properties": {"name": f"Term {i}"}},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        response = test_client.post(
            "/api/knowledge-graph/query",
            json={"query": "Term", "limit": 2},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) <= 2


class TestKnowledgeGraphStats:
    """Tests for graph statistics endpoint"""

    def test_get_graph_stats_empty(
        self, test_client, test_db, editor_authenticated
    ):
        """Test getting stats when graph is empty"""
        token = editor_authenticated["access_token"]

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

    def test_get_graph_stats_with_data(
        self, test_client, test_db, editor_authenticated
    ):
        """Test getting stats with nodes and edges"""
        token = editor_authenticated["access_token"]

        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        response = test_client.get(
            "/api/knowledge-graph/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_nodes"] == 1
        assert "chapter" in data["node_types"]


class TestKnowledgeGraphInitialize:
    """Tests for graph initialization endpoint"""

    def test_initialize_graph(
        self, test_client, test_db, content_admin_authenticated
    ):
        """Test initializing graph with sample data"""
        token = content_admin_authenticated["access_token"]
        user = content_admin_authenticated["user"]

        from tests.api.conftest import create_test_chapter, create_test_project
        project = create_test_project(test_db, owner_id=user.id, name="Demo Project")
        create_test_chapter(test_db, project_id=project["id"], title="Chapter 1")

        response = test_client.post(
            "/api/knowledge-graph/initialize",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_initialize_graph_viewer_forbidden(
        self, test_client, test_db, test_user_authenticated
    ):
        """Test viewer cannot initialize graph"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/knowledge-graph/initialize",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestKnowledgeGraphEdgeCases:
    """Edge case tests for knowledge graph"""

    def test_list_nodes_unauthorized(self, test_client):
        """Test listing nodes without authentication"""
        response = test_client.get("/api/knowledge-graph/nodes")

        assert response.status_code == 401

    def test_create_node_unauthorized(self, test_client):
        """Test creating node without authentication"""
        response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "test", "properties": {}},
        )

        assert response.status_code == 401

    def test_update_node_unauthorized(self, test_client):
        """Test updating node without authentication"""
        response = test_client.put(
            "/api/knowledge-graph/nodes/some-id",
            json={"field": "value"},
        )

        assert response.status_code == 401

    def test_delete_node_unauthorized(self, test_client):
        """Test deleting node without authentication"""
        response = test_client.delete("/api/knowledge-graph/nodes/some-id")

        assert response.status_code == 401

    def test_list_edges_unauthorized(self, test_client):
        """Test listing edges without authentication"""
        response = test_client.get("/api/knowledge-graph/edges")

        assert response.status_code == 401

    def test_create_edge_unauthorized(self, test_client):
        """Test creating edge without authentication"""
        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": "a",
                "target_id": "b",
                "edge_type": "TEST",
            },
        )

        assert response.status_code == 401

    def test_delete_edge_unauthorized(self, test_client):
        """Test deleting edge without authentication"""
        response = test_client.delete("/api/knowledge-graph/edges/1")

        assert response.status_code == 401

    def test_query_graph_unauthorized(self, test_client):
        """Test querying graph without authentication"""
        response = test_client.post(
            "/api/knowledge-graph/query",
            json={"query": "test"},
        )

        assert response.status_code == 401

    def test_get_stats_unauthorized(self, test_client):
        """Test getting stats without authentication"""
        response = test_client.get("/api/knowledge-graph/stats")

        assert response.status_code == 401

    def test_initialize_unauthorized(self, test_client):
        """Test initializing graph without authentication"""
        response = test_client.post("/api/knowledge-graph/initialize")

        assert response.status_code == 401

    def test_delete_node_cascades_edges(
        self, test_client, test_db, editor_authenticated
    ):
        """Test that deleting a node also deletes connected edges"""
        token = editor_authenticated["access_token"]

        source_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "a", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        source_id = source_response.json()["id"]

        target_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "b", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        target_id = target_response.json()["id"]

        test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": source_id,
                "target_id": target_id,
                "edge_type": "CONNECTS",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        test_client.delete(
            f"/api/knowledge-graph/nodes/{source_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        stats_response = test_client.get(
            "/api/knowledge-graph/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert stats_response.json()["total_edges"] == 0
