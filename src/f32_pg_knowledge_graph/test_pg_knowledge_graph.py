"""
F32: PostgreSQL 知识图谱 - TDD 测试

测试覆盖：
- 节点 CRUD (T001-T005)
- 边 CRUD (T006-T009)
- 图遍历 BFS/DFS (T010-T011)
- 路径查找 (T012)
- 上下文查询 (T013-T014)
- 事务回滚 (T015)
- 批量操作 (T016)
- 连接池 (T017)
- 数据持久化 export/import (T018-T019)
- Mock 适配器 (T020-T021)
- 图迁移工具 (T022)

所有测试使用 MockPGAdapter，无需 PostgreSQL 环境。
"""

from enum import Enum

import pytest


class LogicalType(Enum):
    PREREQUISITE = "prerequisite"
    SEQUENTIAL = "sequential"
    OPTIONAL = "optional"


class ReferenceType(Enum):
    DEFINITION = "definition"
    APPLICATION = "application"
    EXAMPLE = "example"
    COMPARISON = "comparison"


# ── Fixture ──────────────────────────────────────────────

import pytest


@pytest.fixture
def pg_kg():
    """创建使用 Mock 适配器的 PGKnowledgeGraph"""
    from f32_pg_knowledge_graph.pg_adapter import MockPGAdapter
    from f32_pg_knowledge_graph.pg_knowledge_graph import PGKnowledgeGraph

    adapter = MockPGAdapter()
    kg = PGKnowledgeGraph(adapter=adapter)
    kg.initialize()
    return kg


@pytest.fixture
def mock_adapter():
    """创建独立的 Mock 适配器"""
    from f32_pg_knowledge_graph.pg_adapter import MockPGAdapter

    adapter = MockPGAdapter()
    adapter.create_tables()
    return adapter


# ── 节点 CRUD 测试 ──────────────────────────────────────

class TestNodeCRUD:
    """F32-T001 ~ F32-T005: 节点 CRUD 操作"""

    def test_create_chapter_node(self, pg_kg):
        """F32-T001: 创建章节点并持久化到 PostgreSQL"""
        from f05_knowledge_graph.nodes import NodeStatus

        node = pg_kg.create_chapter(
            chapter_id="ch-001",
            title="人工智能概述",
            order=1,
            status=NodeStatus.DRAFT,
        )

        assert node.type == "Chapter"
        assert node.id == "ch-001"
        assert node.title == "人工智能概述"

        retrieved = pg_kg.get_node("ch-001")
        assert retrieved is not None
        assert retrieved.title == "人工智能概述"

    def test_create_section_node(self, pg_kg):
        """F32-T002: 创建节节点"""
        pg_kg.create_chapter("ch-001", "第一章", 1)
        section = pg_kg.create_section(
            section_id="sec-001",
            title="人工智能的定义",
            parent_chapter_id="ch-001",
        )

        assert section.type == "Section"
        assert section.parent_chapter_id == "ch-001"

        retrieved = pg_kg.get_node("sec-001")
        assert retrieved.parent_chapter_id == "ch-001"

    def test_create_subsection_node(self, pg_kg):
        """F32-T003: 创建小节节点并验证内容"""
        pg_kg.create_chapter("ch-001", "第一章", 1)
        pg_kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")

        subsection = pg_kg.create_subsection(
            subsection_id="sub-001",
            title="AI的历史",
            parent_section_id="sec-001",
            content="人工智能起源于1956年达特茅斯会议...",
        )

        assert subsection.type == "Subsection"
        assert subsection.content == "人工智能起源于1956年达特茅斯会议..."

        retrieved = pg_kg.get_node("sub-001")
        assert retrieved.content == "人工智能起源于1956年达特茅斯会议..."

    def test_create_concept_node(self, pg_kg):
        """F32-T004: 创建概念节点，验证 definition_hash"""
        definition = "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论"
        concept = pg_kg.create_concept(
            concept_id="c-001",
            name="人工智能",
            definition=definition,
            domain="计算机科学",
            related_terms=["机器学习", "深度学习"],
        )

        assert concept.type == "Concept"
        assert concept.definition_hash is not None
        assert len(concept.definition_hash) == 64

        retrieved = pg_kg.get_node("c-001")
        assert retrieved.name == "人工智能"
        assert "机器学习" in retrieved.related_terms

    def test_create_term_node(self, pg_kg):
        """F32-T005: 创建术语节点，验证同义词"""
        term = pg_kg.create_term(
            term_id="t-001",
            term="机器学习",
            definition="使用数据提升性能的算法",
            domain="计算机科学",
            synonyms=["ML", "Machine Learning"],
        )

        assert term.type == "Term"
        assert "ML" in term.synonyms

        retrieved = pg_kg.get_term("t-001")
        assert retrieved.term == "机器学习"
        assert "Machine Learning" in retrieved.synonyms


# ── 边 CRUD 测试 ────────────────────────────────────────

class TestEdgeCRUD:
    """F32-T006 ~ F32-T009: 边 CRUD 操作"""

    def test_add_contains_edge(self, pg_kg):
        """F32-T006: 创建 CONTAINS 边 (Chapter → Section)"""
        pg_kg.create_chapter("ch-001", "第一章", 1)
        pg_kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")

        edge = pg_kg.add_edge("ch-001", "sec-001", "CONTAINS")

        assert edge.edge_type == "CONTAINS"
        assert edge.source == "ch-001"
        assert edge.target == "sec-001"

        edges = pg_kg.get_edges(node_id="ch-001")
        assert len(edges) >= 1
        assert edges[0]["edge_type"] == "CONTAINS"

    def test_add_follows_edge_with_properties(self, pg_kg):
        """F32-T007: 创建 FOLLOWS 边并持久化属性"""
        pg_kg.create_chapter("ch-001", "第一章", 1)
        pg_kg.create_chapter("ch-002", "第二章", 2)

        edge = pg_kg.add_edge(
            "ch-001", "ch-002",
            "FOLLOWS",
            logical_type=LogicalType.SEQUENTIAL,
        )

        assert edge.properties["logical_type"] == LogicalType.SEQUENTIAL

        edges = pg_kg.get_edges(edge_type="FOLLOWS")
        assert len(edges) == 1
        assert edges[0]["properties"]["logical_type"] == "sequential"

    def test_add_multiple_edge_types(self, pg_kg):
        """F32-T008: 创建多种类型的边"""
        pg_kg.create_chapter("ch-001", "第一章", 1)
        pg_kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        pg_kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        pg_kg.create_concept("c-001", "AI", "定义...", "CS")

        pg_kg.add_edge("ch-001", "sec-001", "CONTAINS")
        pg_kg.add_edge("ch-001", "sec-002", "CONTAINS")
        pg_kg.add_edge("sec-001", "sec-002", "FOLLOWS", logical_type=LogicalType.SEQUENTIAL)
        pg_kg.add_edge("sec-001", "c-001", "DEFINES", definition_text="定义了AI")
        pg_kg.add_edge("sec-002", "sec-001", "REFERENCES",
                       reference_type=ReferenceType.APPLICATION)

        all_edges = pg_kg.get_edges()
        assert len(all_edges) == 5

        contains_edges = pg_kg.get_edges(edge_type="CONTAINS")
        assert len(contains_edges) == 2

    def test_delete_edge(self, pg_kg):
        """F32-T009: 删除边"""
        pg_kg.create_chapter("ch-001", "第一章", 1)
        pg_kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")

        pg_kg.add_edge("ch-001", "sec-001", "CONTAINS")
        edges = pg_kg.get_edges()
        assert len(edges) == 1

        edge_id = edges[0]["id"]
        deleted = pg_kg.delete_edge(edge_id)
        assert deleted is True

        edges_after = pg_kg.get_edges()
        assert len(edges_after) == 0


# ── 图遍历测试 ──────────────────────────────────────────

class TestGraphTraversal:
    """F32-T010 ~ F32-T012: 图遍历"""

    def test_bfs_traversal(self, pg_kg):
        """F32-T010: BFS 遍历"""
        pg_kg.create_chapter("ch-001", "第一章", 1)
        pg_kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        pg_kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        pg_kg.create_section("sec-003", "第三节", parent_chapter_id="ch-001")

        pg_kg.add_edge("ch-001", "sec-001", "CONTAINS")
        pg_kg.add_edge("ch-001", "sec-002", "CONTAINS")
        pg_kg.add_edge("ch-001", "sec-003", "CONTAINS")

        traversal = pg_kg.bfs_traverse("ch-001")
        assert traversal[0] == "ch-001"
        assert "sec-001" in traversal
        assert "sec-002" in traversal
        assert "sec-003" in traversal

    def test_dfs_traversal(self, pg_kg):
        """F32-T011: DFS 遍历"""
        pg_kg.create_concept("c-001", "AI", "人工智能...", "CS")
        pg_kg.create_concept("c-002", "ML", "机器学习...", "CS")
        pg_kg.create_concept("c-003", "DL", "深度学习...", "CS")
        pg_kg.create_concept("c-004", "CNN", "卷积网络...", "CS")

        pg_kg.add_edge("c-001", "c-002", "SIMILAR_TO", similarity_score=0.9)
        pg_kg.add_edge("c-002", "c-003", "SIMILAR_TO", similarity_score=0.8)
        pg_kg.add_edge("c-003", "c-004", "SIMILAR_TO", similarity_score=0.7)

        traversal = pg_kg.dfs_traverse("c-001")
        assert "c-001" in traversal
        assert "c-002" in traversal

    def test_find_path(self, pg_kg):
        """F32-T012: 查找节点间路径"""
        pg_kg.create_chapter("ch-001", "第一章", 1)
        pg_kg.create_chapter("ch-002", "第二章", 2)
        pg_kg.create_chapter("ch-003", "第三章", 3)
        pg_kg.create_chapter("ch-004", "第四章", 4)

        pg_kg.add_edge("ch-001", "ch-002", "FOLLOWS")
        pg_kg.add_edge("ch-002", "ch-003", "FOLLOWS")
        pg_kg.add_edge("ch-003", "ch-004", "FOLLOWS")

        path = pg_kg.find_path("ch-001", "ch-004")
        assert path is not None
        assert path[0] == "ch-001"
        assert path[-1] == "ch-004"
        assert len(path) == 4

    def test_find_path_same_node(self, pg_kg):
        """F32-T012b: 查找同节点路径返回自身"""
        pg_kg.create_chapter("ch-001", "第一章", 1)
        path = pg_kg.find_path("ch-001", "ch-001")
        assert path == ["ch-001"]

    def test_find_path_no_path(self, pg_kg):
        """F32-T012c: 不存在路径返回 None"""
        pg_kg.create_chapter("ch-001", "第一章", 1)
        pg_kg.create_chapter("ch-002", "第二章", 2)
        path = pg_kg.find_path("ch-001", "ch-002")
        assert path is None


# ── 上下文查询测试 ──────────────────────────────────────

class TestContextQueries:
    """F32-T013 ~ F32-T014: 上下文查询"""

    def test_get_chapter_context(self, pg_kg):
        """F32-T013: 章节上下文包含所有子节和边"""
        pg_kg.create_chapter("ch-001", "AI概述", 1)
        pg_kg.create_section("sec-001", "定义", parent_chapter_id="ch-001", word_count=1000)
        pg_kg.create_section("sec-002", "应用", parent_chapter_id="ch-001", word_count=2000)
        pg_kg.add_edge("ch-001", "sec-001", "CONTAINS")
        pg_kg.add_edge("ch-001", "sec-002", "CONTAINS")

        context = pg_kg.get_chapter_context("ch-001")

        assert "ch-001" in context
        assert len(context["sections"]) == 2
        assert "sec-001" in context["sections"]
        assert "sec-002" in context["sections"]
        assert context["total_word_count"] == 3000

    def test_find_similar_concepts(self, pg_kg):
        """F32-T014: 查找相似概念并按评分排序"""
        pg_kg.create_concept("c-001", "人工智能", "AI研究...", "CS")
        pg_kg.create_concept("c-002", "机器学习", "ML是AI的子领域", "CS")
        pg_kg.create_concept("c-003", "深度学习", "DL是ML的子领域", "CS")
        pg_kg.create_concept("c-004", "NLP", "自然语言处理", "CS")

        pg_kg.add_edge("c-001", "c-002", "SIMILAR_TO", similarity_score=0.9)
        pg_kg.add_edge("c-001", "c-003", "SIMILAR_TO", similarity_score=0.7)
        pg_kg.add_edge("c-001", "c-004", "SIMILAR_TO", similarity_score=0.3)

        similar = pg_kg.find_similar_concepts("c-001", threshold=0.5)

        assert len(similar) == 2
        assert similar[0]["concept_id"] == "c-002"
        assert similar[0]["similarity_score"] == 0.9
        assert similar[1]["concept_id"] == "c-003"


# ── 事务测试 ────────────────────────────────────────────

class TestTransactions:
    """F32-T015: 事务回滚"""

    def test_transaction_rollback(self, mock_adapter):
        """F32-T015: 事务回滚后数据未变更"""
        from f32_pg_knowledge_graph.pg_knowledge_graph import PGKnowledgeGraph

        kg = PGKnowledgeGraph(adapter=mock_adapter)
        kg.initialize()

        kg.create_chapter("ch-001", "第一章", 1)
        assert kg.get_node("ch-001") is not None

        try:
            with mock_adapter.transaction():
                kg.create_chapter("ch-002", "第二章", 2)
                kg.create_chapter("ch-003", "第三章", 3)
                raise RuntimeError("Simulated failure")
        except RuntimeError:
            pass

        assert kg.get_node("ch-001") is not None
        assert kg.get_node("ch-002") is None
        assert kg.get_node("ch-003") is None

    def test_transaction_commit(self, mock_adapter):
        """F32-T015b: 事务提交后数据持久化"""
        from f32_pg_knowledge_graph.pg_knowledge_graph import PGKnowledgeGraph

        kg = PGKnowledgeGraph(adapter=mock_adapter)
        kg.initialize()

        with mock_adapter.transaction():
            kg.create_chapter("ch-001", "第一章", 1)
            kg.create_chapter("ch-002", "第二章", 2)

        assert kg.get_node("ch-001") is not None
        assert kg.get_node("ch-002") is not None


# ── 批量操作测试 ────────────────────────────────────────

class TestBatchOperations:
    """F32-T016: 批量操作"""

    def test_batch_insert(self, mock_adapter):
        """F32-T016: 批量插入节点和边"""
        from f32_pg_knowledge_graph.pg_knowledge_graph import PGKnowledgeGraph

        kg = PGKnowledgeGraph(adapter=mock_adapter)
        kg.initialize()

        nodes = [
            {"id": "ch-001", "node_type": "Chapter", "properties": {"title": "第一章", "order": 1}},
            {"id": "ch-002", "node_type": "Chapter", "properties": {"title": "第二章", "order": 2}},
            {"id": "ch-003", "node_type": "Chapter", "properties": {"title": "第三章", "order": 3}},
        ]
        mock_adapter.batch_insert_nodes(nodes)
        assert mock_adapter.count_nodes() == 3

        edges = [
            {"source_id": "ch-001", "target_id": "ch-002", "edge_type": "FOLLOWS", "properties": {}},
            {"source_id": "ch-002", "target_id": "ch-003", "edge_type": "FOLLOWS", "properties": {}},
        ]
        mock_adapter.batch_insert_edges(edges)
        assert mock_adapter.count_edges() == 2


# ── 连接池测试 ──────────────────────────────────────────

class TestConnectionPool:
    """F32-T017: 连接池管理"""

    def test_pool_creation(self):
        """F32-T017: 创建连接池并获取统计信息"""
        from f32_pg_knowledge_graph.connection_pool import ConnectionPool

        pool = ConnectionPool(
            dsn="postgresql://dummy:dummy@localhost:5432/dummy",
            min_connections=1,
            max_connections=3,
        )

        stats = pool.get_stats()
        assert stats["min_connections"] == 1
        assert stats["max_connections"] == 3
        assert stats["total_connections"] == 0
        assert stats["in_use"] == 0
        assert stats["available"] == 0
        assert stats["closed"] is False

    def test_pool_close(self):
        """F32-T017b: 关闭连接池"""
        from f32_pg_knowledge_graph.connection_pool import ConnectionPool

        pool = ConnectionPool(
            dsn="postgresql://dummy:dummy@localhost:5432/dummy",
            min_connections=1,
            max_connections=3,
        )
        pool.close_all()
        stats = pool.get_stats()
        assert stats["closed"] is True

    def test_pool_auto_reconnect_detection(self):
        """F32-T017c: 连接池属性"""
        from f32_pg_knowledge_graph.connection_pool import ConnectionPool

        pool = ConnectionPool(
            dsn="postgresql://dummy:dummy@localhost:5432/dummy",
            min_connections=2,
            max_connections=5,
            max_idle_time=60.0,
            connection_timeout=10.0,
        )

        assert pool.size == 0
        assert pool.in_use == 0
        assert pool.available == 0
        assert pool.dsn.startswith("postgresql://")

    def test_pool_raises_when_closed(self):
        """F32-T017d: 关闭后获取连接抛出异常"""
        from f32_pg_knowledge_graph.connection_pool import ConnectionPool

        pool = ConnectionPool(
            dsn="postgresql://dummy:dummy@localhost:5432/dummy",
        )
        pool.close_all()

        with pytest.raises(RuntimeError, match="closed"):
            pool.get_connection()


# ── 持久化测试 ──────────────────────────────────────────

class TestPersistence:
    """F32-T018 ~ F32-T019: 数据持久化"""

    def test_export_to_dict(self, pg_kg):
        """F32-T018: 导出图谱为字典"""
        pg_kg.create_chapter("ch-001", "第一章", 1)
        pg_kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        pg_kg.add_edge("ch-001", "sec-001", "CONTAINS")

        data = pg_kg.export_to_dict()

        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_import_from_dict(self, pg_kg):
        """F32-T019: 从字典导入图谱"""
        data = {
            "nodes": [
                {"id": "ch-001", "type": "Chapter", "title": "第一章", "order": 1,
                 "status": "draft", "word_count": 0, "version": "1.0"},
                {"id": "sec-001", "type": "Section", "title": "第一节", "order": 0,
                 "status": "draft", "word_count": 0, "parent_chapter_id": "ch-001"},
            ],
            "edges": [
                {"edge_type": "CONTAINS", "source": "ch-001", "target": "sec-001", "properties": {}},
            ],
        }

        pg_kg.import_from_dict(data)

        node = pg_kg.get_node("ch-001")
        assert node is not None
        assert node.title == "第一章"

        edges = pg_kg.get_edges()
        assert len(edges) == 1
        assert edges[0]["edge_type"] == "CONTAINS"

    def test_get_chapter_dependency_graph(self, pg_kg):
        """F32-T019b: 获取章节依赖图"""
        pg_kg.create_chapter("ch-001", "第一章", 1)
        pg_kg.create_chapter("ch-002", "第二章", 2)
        pg_kg.create_chapter("ch-003", "第三章", 3)

        pg_kg.add_edge("ch-001", "ch-002", "FOLLOWS", logical_type=LogicalType.SEQUENTIAL)
        pg_kg.add_edge("ch-002", "ch-003", "FOLLOWS", logical_type=LogicalType.SEQUENTIAL)
        pg_kg.add_edge("ch-001", "ch-003", "FOLLOWS", logical_type=LogicalType.PREREQUISITE)

        deps = pg_kg.get_chapter_dependency_graph()

        assert "ch-001" in deps
        assert "ch-002" in deps["ch-001"]
        assert "ch-003" in deps["ch-001"]
        assert "ch-003" in deps["ch-002"]


# ── Mock 适配器测试 ─────────────────────────────────────

class TestMockAdapter:
    """F32-T020 ~ F32-T021: Mock 适配器独立测试"""

    def test_mock_adapter_crud(self, mock_adapter):
        """F32-T020: Mock 适配器的 CRUD 操作"""
        mock_adapter.insert_node("n-001", "Chapter", {"title": "Test", "order": 1})

        node = mock_adapter.get_node("n-001")
        assert node is not None
        assert node["node_type"] == "Chapter"
        assert node["properties"]["title"] == "Test"

        mock_adapter.update_node("n-001", {"status": "approved"})
        node = mock_adapter.get_node("n-001")
        assert node["properties"]["status"] == "approved"

        mock_adapter.delete_node("n-001")
        assert mock_adapter.get_node("n-001") is None

    def test_mock_adapter_count(self, mock_adapter):
        """F32-T021: Mock 适配器的计数功能"""
        mock_adapter.insert_node("n-001", "Chapter", {"title": "Ch1"})
        mock_adapter.insert_node("n-002", "Section", {"title": "S1"})
        mock_adapter.insert_node("n-003", "Chapter", {"title": "Ch2"})

        assert mock_adapter.count_nodes() == 3
        assert mock_adapter.count_nodes("Chapter") == 2
        assert mock_adapter.count_nodes("Section") == 1

        mock_adapter.insert_edge("n-001", "n-002", "CONTAINS", {})
        mock_adapter.insert_edge("n-001", "n-003", "FOLLOWS", {})

        assert mock_adapter.count_edges() == 2
        assert mock_adapter.count_edges("CONTAINS") == 1

    def test_mock_adapter_get_neighbors(self, mock_adapter):
        """F32-T021b: Mock 适配器获取邻居"""
        mock_adapter.insert_node("n-001", "Chapter", {"title": "Ch1"})
        mock_adapter.insert_node("n-002", "Section", {"title": "S1"})
        mock_adapter.insert_node("n-003", "Section", {"title": "S2"})

        mock_adapter.insert_edge("n-001", "n-002", "CONTAINS", {})
        mock_adapter.insert_edge("n-001", "n-003", "CONTAINS", {})

        neighbors = mock_adapter.get_neighbors("n-001", depth=1)
        assert len(neighbors) == 2
        neighbor_ids = {n["neighbor_id"] for n in neighbors}
        assert neighbor_ids == {"n-002", "n-003"}

    def test_node_status_update(self, pg_kg):
        """F32-T021c: 更新节点状态"""
        from f05_knowledge_graph.nodes import NodeStatus

        pg_kg.create_chapter("ch-001", "第一章", 1, status=NodeStatus.DRAFT)

        pg_kg.update_node_status("ch-001", NodeStatus.IN_REVIEW)
        node = pg_kg.get_node("ch-001")
        assert node.status == NodeStatus.IN_REVIEW

        pg_kg.update_node_status("ch-001", NodeStatus.APPROVED)
        node = pg_kg.get_node("ch-001")
        assert node.status == NodeStatus.APPROVED

    def test_find_concepts_by_domain(self, pg_kg):
        """F32-T021d: 按领域查找概念"""
        pg_kg.create_concept("c-001", "人工智能", "AI...", "计算机科学")
        pg_kg.create_concept("c-002", "企业管理", "管理...", "商业")
        pg_kg.create_concept("c-003", "机器学习", "ML...", "计算机科学")
        pg_kg.create_concept("c-004", "深度学习", "DL...", "计算机科学")

        concepts = pg_kg.find_concepts_by_domain("计算机科学")
        assert len(concepts) == 3
        assert all(c.domain == "计算机科学" for c in concepts)

    def test_get_referencing_sections(self, pg_kg):
        """F32-T021e: 获取引用某小节的所有小节"""
        pg_kg.create_chapter("ch-001", "AI概述", 1)
        pg_kg.create_section("sec-001", "定义节", parent_chapter_id="ch-001")
        pg_kg.create_section("sec-002", "应用节", parent_chapter_id="ch-001")
        pg_kg.create_section("sec-003", "对比节", parent_chapter_id="ch-001")

        pg_kg.add_edge("sec-002", "sec-001", "REFERENCES",
                       reference_type=ReferenceType.APPLICATION)
        pg_kg.add_edge("sec-003", "sec-001", "REFERENCES",
                       reference_type=ReferenceType.COMPARISON)

        referencing = pg_kg.get_referencing_sections("sec-001")
        assert len(referencing) == 2
        assert "sec-002" in referencing
        assert "sec-003" in referencing


# ── 图迁移工具测试 ──────────────────────────────────────

class TestGraphMigrations:
    """F32-T022: 图迁移工具"""

    def test_migration_register_and_status(self, mock_adapter):
        """F32-T022: 注册迁移并查看状态"""
        from f32_pg_knowledge_graph.graph_migrations import (
            GraphMigration,
            create_default_migrations,
        )

        migration = GraphMigration(mock_adapter)
        create_default_migrations(migration)

        status = migration.status()
        assert len(status) == 4
        assert all(not s["applied"] for s in status)
        assert status[0]["version"] == "001"
        assert status[3]["version"] == "004"


# ── 错误场景测试 ──────────────────────────────────────

class TestMockAdapterErrorCases:
    """F32-T023: MockPGAdapter 错误场景测试"""

    def test_get_nonexistent_node_returns_none(self, mock_adapter):
        """F32-T023a: 获取不存在的节点返回None"""
        result = mock_adapter.get_node("nonexistent-id")
        assert result is None

    def test_delete_nonexistent_node_returns_false(self, mock_adapter):
        """F32-T023b: 删除不存在的节点返回False"""
        result = mock_adapter.delete_node("nonexistent-id")
        assert result is False

    def test_update_nonexistent_node_returns_false(self, mock_adapter):
        """F32-T023c: 更新不存在的节点返回False"""
        result = mock_adapter.update_node("nonexistent-id", {"key": "value"})
        assert result is False

    def test_get_nonexistent_edge_returns_none(self, mock_adapter):
        """F32-T023d: 获取不存在的边返回None"""
        result = mock_adapter.get_edge(9999)
        assert result is None

    def test_delete_nonexistent_edge_returns_false(self, mock_adapter):
        """F32-T023e: 删除不存在的边返回False"""
        result = mock_adapter.delete_edge(9999)
        assert result is False

    def test_find_path_nonexistent_start_returns_none(self, mock_adapter):
        """F32-T023f: 起点不存在时返回None"""
        mock_adapter.insert_node("existing", "Chapter", {})
        result = mock_adapter.find_path("nonexistent", "existing")
        assert result is None

    def test_find_path_nonexistent_end_returns_none(self, mock_adapter):
        """F32-T023g: 终点不存在时返回None"""
        mock_adapter.insert_node("start", "Chapter", {})
        result = mock_adapter.find_path("start", "nonexistent")
        assert result is None

    def test_find_path_same_node_with_self_loop(self, mock_adapter):
        """F32-T023h: 自环节点能找到路径"""
        mock_adapter.insert_node("node", "Chapter", {})
        mock_adapter.insert_edge("node", "node", "SELF_REFERENCE", {})
        result = mock_adapter.find_path("node", "node")
        assert result is not None
        assert result[0] == "node"
        assert result[-1] == "node"

    def test_bfs_traverse_nonexistent_start_returns_single_item(self, mock_adapter):
        """F32-T023i: BFS遍历不存在的起点返回单元素列表"""
        result = mock_adapter.bfs_traverse("nonexistent")
        assert result == ["nonexistent"]

    def test_dfs_traverse_nonexistent_start_returns_single_item(self, mock_adapter):
        """F32-T023j: DFS遍历不存在的起点返回单元素列表"""
        result = mock_adapter.dfs_traverse("nonexistent")
        assert result == ["nonexistent"]

    def test_query_nodes_no_match_returns_empty_list(self, mock_adapter):
        """F32-T023k: 查询不存在的节点类型返回空列表"""
        mock_adapter.insert_node("ch-001", "Chapter", {})
        result = mock_adapter.query_nodes(node_type="NonExistentType")
        assert result == []

    def test_count_nodes_empty_returns_zero(self, mock_adapter):
        """F32-T023l: 空图谱节点计数返回0"""
        result = mock_adapter.count_nodes()
        assert result == 0

    def test_count_edges_empty_returns_zero(self, mock_adapter):
        """F32-T023m: 空图谱边计数返回0"""
        result = mock_adapter.count_edges()
        assert result == 0

    def test_batch_insert_empty_lists_returns_zero(self, mock_adapter):
        """F32-T023n: 批量插入空列表返回0"""
        result_nodes = mock_adapter.batch_insert_nodes([])
        result_edges = mock_adapter.batch_insert_edges([])
        assert result_nodes == 0
        assert result_edges == 0

    def test_insert_duplicate_node_updates_properties(self, mock_adapter):
        """F32-T023o: 插入重复节点时更新属性"""
        mock_adapter.insert_node("node-001", "Chapter", {"title": "Original"})
        mock_adapter.insert_node("node-001", "Chapter", {"title": "Updated"})
        node = mock_adapter.get_node("node-001")
        assert node["properties"]["title"] == "Updated"
