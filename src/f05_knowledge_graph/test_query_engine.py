"""
F05: QueryEngine Tests
"""

import pytest

from f05_knowledge_graph.edges import EdgeType
from f05_knowledge_graph.knowledge_graph import KnowledgeGraph
from f05_knowledge_graph.nodes import NodeStatus, NodeType
from f05_knowledge_graph.query_engine import QueryEngine


@pytest.fixture
def knowledge_graph():
    """Create a test knowledge graph with sample data"""
    kg = KnowledgeGraph()

    kg.create_chapter(
        chapter_id="chapter1",
        title="Introduction",
        order=1,
        status=NodeStatus.PUBLISHED,
    )

    kg.create_concept(
        concept_id="concept1",
        name="Machine Learning",
        definition="A subset of AI",
        domain="Computer Science",
        related_terms=["AI", "Neural Networks"],
        source_chapter_id="chapter1",
    )

    kg.create_concept(
        concept_id="concept2",
        name="Deep Learning",
        definition="Neural networks with multiple layers",
        domain="Computer Science",
        related_terms=["ML", "AI"],
        source_chapter_id="chapter1",
    )

    kg.create_concept(
        concept_id="concept3",
        name="Python",
        definition="A programming language",
        domain="Programming",
    )

    kg.add_edge("concept1", "concept2", edge_type=EdgeType.SIMILAR_TO.value, properties={"similarity_score": 0.9})
    kg.add_edge("concept2", "concept1", edge_type=EdgeType.SIMILAR_TO.value, properties={"similarity_score": 0.9})
    kg.add_edge("concept1", "chapter1", edge_type=EdgeType.CONTAINS.value)
    kg.add_edge("concept2", "chapter1", edge_type=EdgeType.CONTAINS.value)

    return kg


@pytest.fixture
def query_engine(knowledge_graph):
    """Create a QueryEngine instance"""
    return QueryEngine(knowledge_graph)


class TestMatchNodes:
    def test_match_nodes_returns_all_when_no_filters(self, query_engine):
        """No filters returns all nodes"""
        results = query_engine.match_nodes()
        assert len(results) == 4

    def test_match_nodes_filters_by_type(self, query_engine):
        """Filter by node_type works correctly"""
        results = query_engine.match_nodes(node_type=NodeType.CONCEPT.value)
        assert len(results) == 3
        for node in results:
            assert node.type == NodeType.CONCEPT.value

    def test_match_nodes_filters_by_predicate(self, query_engine):
        """Filter by predicate works correctly"""
        results = query_engine.match_nodes(predicate=lambda n: hasattr(n, "name") and n.name.startswith("M"))
        assert len(results) == 1
        assert results[0].name == "Machine Learning"

    def test_match_nodes_combines_filters(self, query_engine):
        """Both node_type and predicate filters work together"""
        results = query_engine.match_nodes(node_type=NodeType.CONCEPT.value, predicate=lambda n: "Learning" in n.name)
        assert len(results) == 2

    def test_match_nodes_returns_empty_when_no_match(self, query_engine):
        """Returns empty list when no nodes match"""
        results = query_engine.match_nodes(node_type="NonExistentType")
        assert len(results) == 0


class TestMatchEdges:
    def test_match_edges_returns_all_when_no_filters(self, query_engine):
        """No filters returns all edges"""
        results = query_engine.match_edges()
        assert len(results) == 4

    def test_match_edges_filters_by_type(self, query_engine):
        """Filter by edge_type works correctly"""
        results = query_engine.match_edges(edge_type=EdgeType.SIMILAR_TO.value)
        assert len(results) == 2
        for edge in results:
            assert edge.edge_type == EdgeType.SIMILAR_TO.value

    def test_match_edges_filters_by_source_predicate(self, query_engine):
        """Filter by source_predicate works correctly"""
        results = query_engine.match_edges(source_predicate=lambda s: s.startswith("concept1"))
        assert len(results) == 2
        for edge in results:
            assert edge.source == "concept1"

    def test_match_edges_filters_by_target_predicate(self, query_engine):
        """Filter by target_predicate works correctly"""
        results = query_engine.match_edges(target_predicate=lambda t: t.startswith("concept"))
        assert len(results) == 2

    def test_match_edges_combines_filters(self, query_engine):
        """Combines edge_type and source_predicate"""
        results = query_engine.match_edges(
            edge_type=EdgeType.SIMILAR_TO.value, source_predicate=lambda s: s == "concept1"
        )
        assert len(results) == 1
        assert results[0].source == "concept1"

    def test_match_edges_returns_empty_when_no_match(self, query_engine):
        """Returns empty list when no edges match"""
        results = query_engine.match_edges(edge_type="NONEXISTENT")
        assert len(results) == 0


class TestAggregateByType:
    def test_aggregate_by_type_counts_correctly(self, query_engine):
        """Aggregation counts nodes by type"""
        result = query_engine.aggregate_by_type()
        assert result[NodeType.CHAPTER.value] == 1
        assert result[NodeType.CONCEPT.value] == 3

    def test_aggregate_by_type_empty_graph(self):
        """Empty graph returns empty dict"""
        kg = KnowledgeGraph()
        qe = QueryEngine(kg)
        result = qe.aggregate_by_type()
        assert result == {}


class TestGetSubgraph:
    def test_get_subgraph_with_existing_nodes(self, query_engine):
        """Returns subgraph with specified nodes and their edges"""
        subgraph = query_engine.get_subgraph(["concept1", "concept2"])

        assert "nodes" in subgraph
        assert "edges" in subgraph
        assert "concept1" in subgraph["nodes"]
        assert "concept2" in subgraph["nodes"]

    def test_get_subgraph_includes_internal_edges(self, query_engine):
        """Subgraph includes edges between specified nodes"""
        subgraph = query_engine.get_subgraph(["concept1", "concept2"])

        edge_sources = [e.source for e in subgraph["edges"]]
        edge_targets = [e.target for e in subgraph["edges"]]
        assert "concept1" in edge_sources or "concept1" in edge_targets
        assert "concept2" in edge_sources or "concept2" in edge_targets

    def test_get_subgraph_excludes_external_edges(self, query_engine):
        """Subgraph excludes edges to nodes not in list"""
        subgraph = query_engine.get_subgraph(["concept1"])

        for edge in subgraph["edges"]:
            assert edge.source in ["concept1"] or edge.target in ["concept1"]

    def test_get_subgraph_with_nonexistent_nodes(self, query_engine):
        """Handles nonexistent node IDs gracefully"""
        subgraph = query_engine.get_subgraph(["nonexistent"])
        assert subgraph["nodes"] == {}
        assert subgraph["edges"] == []

    def test_get_subgraph_with_mixed_nodes(self, query_engine):
        """Handles mix of existing and nonexistent nodes"""
        subgraph = query_engine.get_subgraph(["concept1", "nonexistent"])
        assert "concept1" in subgraph["nodes"]
        assert "nonexistent" not in subgraph["nodes"]


class TestFindCliques:
    def test_find_cliques_finds_pairwise_cliques(self, query_engine):
        """Finds cliques (pairwise similar concepts)"""
        cliques = query_engine.find_cliques(min_size=2)
        assert len(cliques) >= 1

    def test_find_cliques_respects_min_size(self, query_engine):
        """Respects min_size parameter"""
        cliques = query_engine.find_cliques(min_size=3)
        for clique in cliques:
            assert len(clique) >= 3

    def test_find_cliques_empty_graph(self):
        """Empty graph returns empty list"""
        kg = KnowledgeGraph()
        qe = QueryEngine(kg)
        cliques = qe.find_cliques()
        assert cliques == []

    def test_find_cliques_no_concepts(self):
        """Graph with no concepts returns empty list"""
        kg = KnowledgeGraph()
        kg.create_chapter(
            chapter_id="chapter1",
            title="Test",
            order=1,
        )
        qe = QueryEngine(kg)
        cliques = qe.find_cliques()
        assert cliques == []


class TestGetStatistics:
    def test_get_statistics_returns_all_fields(self, query_engine):
        """Returns complete statistics"""
        stats = query_engine.get_statistics()

        assert "total_nodes" in stats
        assert "total_edges" in stats
        assert "nodes_by_type" in stats
        assert "edges_by_type" in stats

    def test_get_statistics_counts_correct(self, query_engine):
        """Node and edge counts are correct"""
        stats = query_engine.get_statistics()

        assert stats["total_nodes"] == 4
        assert stats["total_edges"] == 4

    def test_get_statistics_nodes_by_type(self, query_engine):
        """Nodes by type breakdown is correct"""
        stats = query_engine.get_statistics()

        assert stats["nodes_by_type"][NodeType.CHAPTER.value] == 1
        assert stats["nodes_by_type"][NodeType.CONCEPT.value] == 3

    def test_get_statistics_edges_by_type(self, query_engine):
        """Edges by type breakdown is correct"""
        stats = query_engine.get_statistics()

        assert stats["edges_by_type"][EdgeType.SIMILAR_TO.value] == 2
        assert stats["edges_by_type"][EdgeType.CONTAINS.value] == 2

    def test_get_statistics_empty_graph(self):
        """Empty graph returns zeros"""
        kg = KnowledgeGraph()
        qe = QueryEngine(kg)
        stats = qe.get_statistics()

        assert stats["total_nodes"] == 0
        assert stats["total_edges"] == 0
        assert stats["nodes_by_type"] == {}
        assert stats["edges_by_type"] == {}
