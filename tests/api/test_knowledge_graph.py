"""
Knowledge Graph API Integration Tests

Tests for knowledge graph endpoints:
- GET /api/knowledge-graph/nodes - List nodes
- POST /api/knowledge-graph/nodes - Create node
- GET /api/knowledge-graph/nodes/{id} - Get node details
- PUT /api/knowledge-graph/nodes/{id} - Update node
- DELETE /api/knowledge-graph/nodes/{id} - Delete node
- GET /api/knowledge-graph/edges - List edges
- POST /api/knowledge-graph/edges - Create edge
- POST /api/knowledge-graph/query - Query graph
- GET /api/knowledge-graph/stats - Graph statistics
"""


_in_memory_nodes = {}
_in_memory_edges = {}
_edge_id_counter = 0


class TestListNodes:
    """Tests for listing knowledge graph nodes"""

    def test_list_nodes_empty(self, test_client, test_db, test_user_authenticated):
        """Test listing nodes when none exist"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/knowledge-graph/nodes",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_nodes_with_data(self, test_client, test_db, editor_authenticated, test_app):
        """Test listing nodes with existing data"""
        token = editor_authenticated["access_token"]

        response1 = test_client.post(
            "/api/knowledge-graph/nodes",
            json={
                "node_type": "concept",
                "properties": {"name": "Machine Learning", "definition": "AI subset"},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        assert response1.status_code == 201

        response2 = test_client.get(
            "/api/knowledge-graph/nodes",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response2.status_code == 200
        data = response2.json()
        assert len(data) >= 1

    def test_list_nodes_filter_by_type(self, test_client, test_db, editor_authenticated):
        """Test listing nodes filtered by type"""
        token = editor_authenticated["access_token"]

        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {"title": "Chapter 1"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {"name": "Concept 1"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        response = test_client.get(
            "/api/knowledge-graph/nodes?node_type=chapter",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        for node in data:
            assert node["node_type"] == "chapter"

    def test_list_nodes_pagination(self, test_client, test_db, editor_authenticated):
        """Test node listing with pagination"""
        token = editor_authenticated["access_token"]

        for i in range(5):
            test_client.post(
                "/api/knowledge-graph/nodes",
                json={
                    "node_type": "concept",
                    "properties": {"name": f"Concept {i}"},
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

        response = test_client.get(
            "/api/knowledge-graph/nodes?page=1&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_nodes_unauthorized(self, test_client):
        """Test listing nodes without authentication"""
        response = test_client.get("/api/knowledge-graph/nodes")

        assert response.status_code == 401

    def test_list_nodes_viewer_allowed(self, test_client, test_db, test_user_authenticated):
        """Test viewer can list nodes (has knowledge_graph:read permission)"""
        token = test_user_authenticated["access_token"]

        response = test_client.get(
            "/api/knowledge-graph/nodes",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200


class TestCreateNode:
    """Tests for creating knowledge graph nodes"""

    def test_create_node(self, test_client, test_db, editor_authenticated):
        """Test successful node creation"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={
                "node_type": "concept",
                "properties": {
                    "name": "Deep Learning",
                    "definition": "Neural networks with multiple layers",
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
        assert data["properties"]["name"] == "Deep Learning"
        assert "id" in data
        assert "created_at" in data

    def test_create_node_minimal(self, test_client, test_db, editor_authenticated):
        """Test node creation with minimal data"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "term", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201

    def test_create_node_viewer_forbidden(self, test_client, test_db, test_user_authenticated):
        """Test viewer cannot create nodes"""
        token = test_user_authenticated["access_token"]

        response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {"name": "Unauthorized"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 403


class TestGetNode:
    """Tests for getting node details"""

    def test_get_node(self, test_client, test_db, editor_authenticated):
        """Test getting node by ID"""
        token = editor_authenticated["access_token"]

        create_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={
                "node_type": "chapter",
                "properties": {"title": "Test Chapter"},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        node_id = create_response.json()["id"]

        response = test_client.get(
            f"/api/knowledge-graph/nodes/{node_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == node_id
        assert data["properties"]["title"] == "Test Chapter"

    def test_get_node_not_found(self, test_client, test_db, editor_authenticated):
        """Test getting non-existent node"""
        token = editor_authenticated["access_token"]

        response = test_client.get(
            "/api/knowledge-graph/nodes/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestUpdateNode:
    """Tests for updating nodes"""

    def test_update_node(self, test_client, test_db, content_admin_authenticated):
        """Test updating node properties"""
        token = content_admin_authenticated["access_token"]

        create_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={
                "node_type": "concept",
                "properties": {"name": "Original Name"},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        node_id = create_response.json()["id"]

        response = test_client.put(
            f"/api/knowledge-graph/nodes/{node_id}",
            json={"updated_prop": "new_value"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "updated_prop" in data["properties"]


class TestDeleteNode:
    """Tests for deleting nodes"""

    def test_delete_node(self, test_client, test_db, content_admin_authenticated):
        """Test deleting node"""
        token = content_admin_authenticated["access_token"]

        create_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {"name": "To Delete"}},
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

    def test_delete_node_not_found(self, test_client, test_db, content_admin_authenticated):
        """Test deleting non-existent node"""
        token = content_admin_authenticated["access_token"]

        response = test_client.delete(
            "/api/knowledge-graph/nodes/nonexistent-id",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404


class TestListEdges:
    """Tests for listing knowledge graph edges"""

    def test_list_edges_empty(self, test_client, test_db, editor_authenticated):
        """Test listing edges when none exist"""
        token = editor_authenticated["access_token"]

        response = test_client.get(
            "/api/knowledge-graph/edges",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_edges_filter_by_type(self, test_client, test_db, editor_authenticated):
        """Test listing edges filtered by edge type"""
        token = editor_authenticated["access_token"]

        response = test_client.get(
            "/api/knowledge-graph/edges?edge_type=CONTAINS",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200


class TestCreateEdge:
    """Tests for creating knowledge graph edges"""

    def test_create_edge(self, test_client, test_db, editor_authenticated):
        """Test successful edge creation"""
        token = editor_authenticated["access_token"]

        node1_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {"title": "Chapter 1"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        node1_id = node1_response.json()["id"]

        node2_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "section", "properties": {"title": "Section 1"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        node2_id = node2_response.json()["id"]

        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": node1_id,
                "target_id": node2_id,
                "edge_type": "CONTAINS",
                "properties": {"order": 1},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["source_id"] == node1_id
        assert data["target_id"] == node2_id
        assert data["edge_type"] == "CONTAINS"

    def test_create_edge_source_not_found(self, test_client, test_db, editor_authenticated):
        """Test creating edge with non-existent source node"""
        token = editor_authenticated["access_token"]

        node2_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        node2_id = node2_response.json()["id"]

        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": "nonexistent-source",
                "target_id": node2_id,
                "edge_type": "REFERENCES",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "SOURCE_NODE_NOT_FOUND"

    def test_create_edge_target_not_found(self, test_client, test_db, editor_authenticated):
        """Test creating edge with non-existent target node"""
        token = editor_authenticated["access_token"]

        node1_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "concept", "properties": {}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        node1_id = node1_response.json()["id"]

        response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": node1_id,
                "target_id": "nonexistent-target",
                "edge_type": "DEFINES",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "TARGET_NODE_NOT_FOUND"


class TestDeleteEdge:
    """Tests for deleting edges"""

    def test_delete_edge(self, test_client, test_db, content_admin_authenticated):
        """Test deleting edge"""
        token = content_admin_authenticated["access_token"]

        node1_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {"title": "C1"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        node1_id = node1_response.json()["id"]

        node2_response = test_client.post(
            "/api/knowledge-graph/nodes",
            json={"node_type": "chapter", "properties": {"title": "C2"}},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )
        node2_id = node2_response.json()["id"]

        edge_response = test_client.post(
            "/api/knowledge-graph/edges",
            json={
                "source_id": node1_id,
                "target_id": node2_id,
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


class TestQueryGraph:
    """Tests for querying the knowledge graph"""

    def test_query_graph(self, test_client, test_db, editor_authenticated):
        """Test querying the graph"""
        token = editor_authenticated["access_token"]

        test_client.post(
            "/api/knowledge-graph/nodes",
            json={
                "node_type": "concept",
                "properties": {"name": "Machine Learning"},
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        response = test_client.post(
            "/api/knowledge-graph/query",
            json={"query": "Machine", "node_types": ["concept"], "limit": 10},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "nodes" in data
        assert "edges" in data

    def test_query_graph_empty_query(self, test_client, test_db, editor_authenticated):
        """Test querying with no matches"""
        token = editor_authenticated["access_token"]

        response = test_client.post(
            "/api/knowledge-graph/query",
            json={"query": "Nonexistent", "limit": 10},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_nodes"] == 0


class TestGraphStats:
    """Tests for graph statistics"""

    def test_get_graph_stats(self, test_client, test_db, editor_authenticated):
        """Test getting graph statistics"""
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
        assert "total_nodes" in data
        assert "total_edges" in data
        assert "node_types" in data
        assert "edge_types" in data
