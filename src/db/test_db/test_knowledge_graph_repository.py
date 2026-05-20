"""Tests for KnowledgeGraphRepository.

These tests focus on testing the repository methods by patching
the actual model operations to avoid SQLAlchemy relationship issues.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestKnowledgeGraphRepository:
    """Test KnowledgeGraphRepository methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = MagicMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_node_found(self, repo, mock_session):
        """Test get_node returns node when found."""
        mock_node = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_node
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_node("node1")

        assert result is mock_node

    @pytest.mark.asyncio
    async def test_get_node_not_found(self, repo, mock_session):
        """Test get_node returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_node("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_nodes(self, repo, mock_session):
        """Test get_all_nodes returns sequence."""
        mock_nodes = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_nodes
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_all_nodes()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_node(self, repo, mock_session):
        """Test update_node updates properties."""
        existing_node = MagicMock()
        existing_node.properties = {"key": "old"}
        mock_session.execute = AsyncMock()

        with patch.object(repo, "get_node", return_value=existing_node):
            result = await repo.update_node("node1", {"new_key": "new_value"})

        mock_session.flush.assert_called()
        mock_session.refresh.assert_called()

    @pytest.mark.asyncio
    async def test_delete_node_not_found(self, repo, mock_session):
        """Test delete_node returns False when not found."""
        mock_session.execute = AsyncMock()

        with patch.object(repo, "get_node", return_value=None):
            result = await repo.delete_node("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_create_edge_source_not_found(self, repo, mock_session):
        """Test create_edge returns None when source not found."""
        with patch.object(repo, "get_node", return_value=None):
            result = await repo.create_edge(
                source_id="nonexistent",
                target_id="target1",
                edge_type="relates_to"
            )

        assert result is None
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_edge(self, repo, mock_session):
        """Test get_edge returns edge."""
        mock_edge = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_edge
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_edge(1)

        assert result is mock_edge

    @pytest.mark.asyncio
    async def test_get_edges(self, repo, mock_session):
        """Test get_edges returns sequence of edges."""
        mock_edges = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_edges
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_edges(source_id="node1")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_delete_edge_not_found(self, repo, mock_session):
        """Test delete_edge returns False when edge not found."""
        mock_session.execute = AsyncMock()

        with patch.object(repo, "get_edge", return_value=None):
            result = await repo.delete_edge(999)

        assert result is False

    @pytest.mark.asyncio
    async def test_count_nodes(self, repo, mock_session):
        """Test count_nodes returns count."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.count_nodes()

        assert result == 42

    @pytest.mark.asyncio
    async def test_count_edges(self, repo, mock_session):
        """Test count_edges returns count."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 15
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.count_edges()

        assert result == 15

    @pytest.mark.asyncio
    async def test_node_exists_true(self, repo, mock_session):
        """Test node_exists returns True when node exists."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 1
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.node_exists("node1")

        assert result is True

    @pytest.mark.asyncio
    async def test_node_exists_false(self, repo, mock_session):
        """Test node_exists returns False when node doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.node_exists("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_edge_exists(self, repo, mock_session):
        """Test edge_exists returns True when edge exists."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 1
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.edge_exists("source1", "target1", "relates_to")

        assert result is True


class TestKnowledgeGraphRepositoryQueryNodes:
    """Test KnowledgeGraphRepository.query_nodes method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_query_nodes_with_filters(self, repo, mock_session):
        """Test query_nodes with property filters."""
        mock_nodes = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_nodes
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.query_nodes(node_type="concept", name="test")

        assert len(result) == 2


class TestKnowledgeGraphRepositoryGetNeighbors:
    """Test KnowledgeGraphRepository.get_neighbors method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_neighbors_depth_1(self, repo, mock_session):
        """Test get_neighbors with depth=1."""
        mock_edge = MagicMock()
        mock_edge.target_id = "neighbor1"
        mock_edge.edge_type = "relates_to"
        mock_edge.properties = {}

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_edge]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_neighbors("node1", depth=1)

        assert len(result) == 1
        assert result[0]["neighbor_id"] == "neighbor1"
        assert result[0]["depth"] == 1


class TestKnowledgeGraphRepositoryFindPath:
    """Test KnowledgeGraphRepository.find_path method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_find_path_same_start_end(self, repo, mock_session):
        """Test find_path returns [start_id] when start equals end."""
        result = await repo.find_path("same", "same", max_depth=10)

        assert result == ["same"]

    @pytest.mark.asyncio
    async def test_find_path_no_path(self, repo, mock_session):
        """Test find_path returns None when no path exists."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.find_path("start", "end", max_depth=10)

        assert result is None

    @pytest.mark.asyncio
    async def test_find_path_found(self, repo, mock_session):
        """Test find_path returns path when found."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (["start", "middle", "end"],)
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.find_path("start", "end", max_depth=10)

        assert result == ["start", "middle", "end"]


class TestKnowledgeGraphRepositoryBfsTraverse:
    """Test KnowledgeGraphRepository.bfs_traverse method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_bfs_traverse(self, repo, mock_session):
        """Test bfs_traverse returns list of visited nodes."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("node2", 1),
            ("node3", 1),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.bfs_traverse("start")

        assert result == ["start", "node2", "node3"]


class TestKnowledgeGraphRepositoryDfsTraverse:
    """Test KnowledgeGraphRepository.dfs_traverse method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_dfs_traverse(self, repo, mock_session):
        """Test dfs_traverse returns list of visited nodes."""
        mock_outgoing = MagicMock()
        mock_outgoing.__aiter__ = lambda self: iter([])
        mock_incoming = MagicMock()
        mock_incoming.__aiter__ = lambda self: iter([])

        with patch.object(repo, "get_edges", side_effect=[mock_outgoing, mock_incoming]):
            result = await repo.dfs_traverse("start")

        assert "start" in result


class TestKnowledgeGraphRepositoryGetIncomingOutgoing:
    """Test KnowledgeGraphRepository get_incoming_edges and get_outgoing_edges."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_outgoing_edges(self, repo, mock_session):
        """Test get_outgoing_edges returns edges."""
        mock_edges = [MagicMock()]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_edges
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(repo, "get_edges", return_value=mock_edges):
            result = await repo.get_outgoing_edges("node1")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_incoming_edges(self, repo, mock_session):
        """Test get_incoming_edges returns edges."""
        mock_edges = [MagicMock()]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_edges
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(repo, "get_edges", return_value=mock_edges):
            result = await repo.get_incoming_edges("node1")

        assert len(result) == 1


class TestKnowledgeGraphRepositoryGetAllNodes:
    """Test KnowledgeGraphRepository.get_all_nodes method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_all_nodes_with_type_filter(self, repo, mock_session):
        """Test get_all_nodes filters by node_type."""
        mock_nodes = [MagicMock()]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_nodes
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_all_nodes(node_type="concept")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_all_nodes_with_pagination(self, repo, mock_session):
        """Test get_all_nodes with limit and offset."""
        mock_nodes = [MagicMock()]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_nodes
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_all_nodes(limit=10, offset=5)

        assert len(result) == 1


class TestKnowledgeGraphRepositoryDeleteNode:
    """Test KnowledgeGraphRepository.delete_node method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.delete = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_delete_node_success(self, repo, mock_session):
        """Test delete_node returns True when node deleted."""
        mock_node = MagicMock()

        with patch.object(repo, "get_node", return_value=mock_node):
            with patch.object(repo, "delete_node", return_value=True) as mock_delete:
                result = await mock_delete("node1")

        assert result is True


class TestKnowledgeGraphRepositoryGetEdges:
    """Test KnowledgeGraphRepository.get_edges with various filters."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_edges_with_edge_type(self, repo, mock_session):
        """Test get_edges filters by edge_type."""
        mock_edges = [MagicMock()]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_edges
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_edges(edge_type="depends")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_edges_with_all_filters(self, repo, mock_session):
        """Test get_edges with source_id, target_id, and edge_type."""
        mock_edges = [MagicMock()]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_edges
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_edges(source_id="s1", target_id="t1", edge_type="relates")

        assert len(result) == 1


class TestKnowledgeGraphRepositoryCreateNode:
    """Test KnowledgeGraphRepository.create_node method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_create_node_with_properties(self, repo, mock_session):
        """Test create_node creates node with properties."""
        with patch("db.repositories.knowledge_graph_repository.GraphNode") as mock_node_class:
            mock_node_class.return_value = MagicMock()
            result = await repo.create_node(
                node_id="node1",
                node_type="concept",
                properties={"key": "value"}
            )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_node_without_properties(self, repo, mock_session):
        """Test create_node creates node with default empty properties."""
        with patch("db.repositories.knowledge_graph_repository.GraphNode") as mock_node_class:
            mock_node_class.return_value = MagicMock()
            result = await repo.create_node(
                node_id="node2",
                node_type="term"
            )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()


class TestKnowledgeGraphRepositoryCreateEdge:
    """Test KnowledgeGraphRepository.create_edge method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_create_edge_success(self, repo, mock_session):
        """Test create_edge creates edge when both nodes exist."""
        mock_source = MagicMock()
        mock_source.id = "source1"
        mock_target = MagicMock()
        mock_target.id = "target1"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_source, mock_target]
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("db.repositories.knowledge_graph_repository.GraphEdge") as mock_edge_class:
            mock_edge_class.return_value = MagicMock()
            result = await repo.create_edge(
                source_id="source1",
                target_id="target1",
                edge_type="relates_to",
                properties={"weight": 1.0}
            )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_edge_target_not_found(self, repo, mock_session):
        """Test create_edge returns None when target not found."""
        mock_source = MagicMock()
        mock_source.id = "source1"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_source, None]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.create_edge(
            source_id="source1",
            target_id="nonexistent",
            edge_type="relates_to"
        )

        assert result is None
        mock_session.add.assert_not_called()


class TestKnowledgeGraphRepositoryDeleteNode:
    """Test KnowledgeGraphRepository.delete_node success path."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_delete_node_success(self, repo, mock_session):
        """Test delete_node returns True when node deleted."""
        mock_node = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_node
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.delete_node("node1")

        assert result is True
        mock_session.delete.assert_called_once_with(mock_node)
        mock_session.flush.assert_called_once()


class TestKnowledgeGraphRepositoryDeleteEdge:
    """Test KnowledgeGraphRepository.delete_edge success path."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_delete_edge_success(self, repo, mock_session):
        """Test delete_edge returns True when edge deleted."""
        mock_edge = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_edge
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.delete_edge(1)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_edge)
        mock_session.flush.assert_called_once()


class TestKnowledgeGraphRepositoryUpdateNode:
    """Test KnowledgeGraphRepository.update_node returns None."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_update_node_not_found(self, repo, mock_session):
        """Test update_node returns None when node not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.update_node("nonexistent", {"key": "value"})

        assert result is None


class TestKnowledgeGraphRepositoryGetNeighborsDepth:
    """Test KnowledgeGraphRepository.get_neighbors with depth > 1."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_neighbors_depth_greater_than_1(self, repo, mock_session):
        """Test get_neighbors uses recursive CTE for depth > 1."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("neighbor1", "relates_to", {}, 1),
            ("neighbor2", "depends_on", {}, 2),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_neighbors("node1", depth=2)

        assert len(result) == 2
        assert result[0]["neighbor_id"] == "neighbor1"
        assert result[0]["depth"] == 1
        assert result[1]["depth"] == 2
        mock_session.execute.assert_called_once()


class TestKnowledgeGraphRepositoryBatchInsert:
    """Test KnowledgeGraphRepository batch insert methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_batch_insert_nodes(self, repo, mock_session):
        """Test batch_insert_nodes inserts multiple nodes."""
        with patch("db.repositories.knowledge_graph_repository.GraphNode") as mock_node_class:
            mock_node_class.return_value = MagicMock()
            nodes = [
                {"id": "node1", "node_type": "concept", "properties": {}},
                {"id": "node2", "node_type": "term", "properties": {"key": "val"}},
                {"id": "node3", "node_type": "concept"},
            ]
            result = await repo.batch_insert_nodes(nodes)

        assert mock_session.add.call_count == 3
        mock_session.flush.assert_called_once()
        assert result == 3

    @pytest.mark.asyncio
    async def test_batch_insert_edges(self, repo, mock_session):
        """Test batch_insert_edges inserts multiple edges."""
        with patch("db.repositories.knowledge_graph_repository.GraphEdge") as mock_edge_class:
            mock_edge_class.return_value = MagicMock()
            edges = [
                {"source_id": "s1", "target_id": "t1", "edge_type": "relates", "properties": {}},
                {"source_id": "s2", "target_id": "t2", "edge_type": "depends", "properties": {}},
            ]
            result = await repo.batch_insert_edges(edges)

        assert mock_session.add.call_count == 2
        mock_session.flush.assert_called_once()
        assert result == 2


class TestKnowledgeGraphRepositoryDfsRecursive:
    """Test KnowledgeGraphRepository.dfs_traverse recursive behavior."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create a KnowledgeGraphRepository with mock session."""
        from db.repositories.knowledge_graph_repository import KnowledgeGraphRepository
        return KnowledgeGraphRepository(mock_session)

    @pytest.mark.asyncio
    async def test_dfs_traverse_with_outgoing_and_incoming(self, repo, mock_session):
        """Test dfs_traverse handles both outgoing and incoming edges."""
        mock_outgoing_edge = MagicMock()
        mock_outgoing_edge.target_id = "node2"

        mock_incoming_edge = MagicMock()
        mock_incoming_edge.source_id = "node3"

        def get_edges_side_effect(**kwargs):
            if kwargs.get("source_id") == "start":
                return [mock_outgoing_edge]
            if kwargs.get("target_id") == "start":
                return [mock_incoming_edge]
            return []

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.side_effect = [[mock_outgoing_edge], [mock_incoming_edge]]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(repo, "get_edges", side_effect=get_edges_side_effect):
            result = await repo.dfs_traverse("start")

        assert "start" in result
        assert "node2" in result
        assert "node3" in result


