"""
F05: 知识图谱核心 - TDD RED阶段测试

本测试文件包含所有RED测试用例，这些测试在实现前应该失败。
按照TDD原则：
1. RED: 写失败测试 (本文件)
2. GREEN: 写最简实现让测试通过
3. Refactor: 优化代码质量

节点类型:
- Chapter(id, title, order, status, wordCount, version)
- Section(id, title, order, status, wordCount, parentChapterId)
- Subsection(id, title, order, status, content, parentSectionId)
- Concept(id, name, definition, domain, relatedTerms[], sourceChapterId)
- Term(id, term, definition, synonyms[], domain, firstDefinedAt)

边类型:
- CONTAINS(Chapter → Section)
- FOLLOWS(Chapter/Section → Chapter/Section, logicalType)
- DEFINES(Chapter/Section → Concept, definitionText)
- USES(Chapter/Section → Term, usageContext)
- REFERENCES(Section → Section, referenceType, context)
- ASSIGNED_TO(Chapter/Section → Author)
- REVIEWED_BY(Chapter/Section → Author, reviewAt, status)
- SIMILAR_TO(Concept → Concept, similarityScore)
"""

import pytest
from enum import Enum


class LogicalType(Enum):
    PREREQUISITE = "prerequisite"
    SEQUENTIAL = "sequential"
    OPTIONAL = "optional"


class ReferenceType(Enum):
    DEFINITION = "definition"
    APPLICATION = "application"
    EXAMPLE = "example"
    COMPARISON = "comparison"


class TestKnowledgeGraphNodes:
    """知识图谱节点创建测试"""

    def test_create_chapter_node(self):
        """F05-T001: 创建章节点"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        node = kg.create_chapter(
            chapter_id="ch-001",
            title="人工智能概述",
            order=1
        )

        assert node.type == "Chapter"
        assert node.id == "ch-001"
        assert node.title == "人工智能概述"
        assert node.order == 1
        assert node.status.value == "draft"
        assert node.version == "1.0"

    def test_create_section_node(self):
        """F05-T002: 创建节节点"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        section = kg.create_section(
            section_id="sec-001",
            title="人工智能的定义",
            parent_chapter_id="ch-001"
        )

        assert section.type == "Section"
        assert section.id == "sec-001"
        assert section.parent_chapter_id == "ch-001"
        assert section.title == "人工智能的定义"

    def test_create_subsection_node(self):
        """F05-T003: 创建小节节点"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        subsection = kg.create_subsection(
            subsection_id="sub-001",
            title="AI的历史",
            parent_section_id="sec-001",
            content="人工智能起源于1956年..."
        )

        assert subsection.type == "Subsection"
        assert subsection.id == "sub-001"
        assert subsection.parent_section_id == "sec-001"
        assert subsection.content == "人工智能起源于1956年..."

    def test_create_concept_node(self):
        """F05-T004: 创建概念节点"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        concept = kg.create_concept(
            concept_id="c-001",
            name="人工智能",
            definition="研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术...",
            domain="计算机科学"
        )

        assert concept.type == "Concept"
        assert concept.name == "人工智能"
        assert concept.definition_hash is not None
        assert len(concept.definition_hash) == 64  # SHA-256

    def test_create_term_node(self):
        """F05-T005: 创建术语节点"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        term = kg.create_term(
            term_id="t-001",
            term="机器学习",
            definition="研究、使用数据提升性能的算法...",
            domain="计算机科学",
            synonyms=["ML", "Machine Learning"]
        )

        assert term.type == "Term"
        assert term.term == "机器学习"
        assert "ML" in term.synonyms


class TestKnowledgeGraphEdges:
    """知识图谱边创建测试"""

    def test_contains_edge_chapter_to_section(self):
        """F05-T006: 创建CONTAINS边 (Chapter → Section)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")

        edge = kg.add_edge("ch-001", "sec-001", "CONTAINS")

        assert edge.edge_type == "CONTAINS"
        assert edge.source == "ch-001"
        assert edge.target == "sec-001"

    def test_follows_edge_between_chapters(self):
        """F05-T007: 创建FOLLOWS边 (Chapter → Chapter)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph
        from f05_knowledge_graph.nodes import NodeStatus

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_chapter("ch-002", "第二章", 2)

        edge = kg.add_edge(
            "ch-001", "ch-002",
            "FOLLOWS",
            logical_type=LogicalType.SEQUENTIAL
        )

        assert edge.edge_type == "FOLLOWS"
        assert edge.source == "ch-001"
        assert edge.target == "ch-002"
        assert edge.properties["logical_type"] == LogicalType.SEQUENTIAL

    def test_follows_edge_between_sections(self):
        """F05-T008: 创建FOLLOWS边 (Section → Section)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")

        edge = kg.add_edge(
            "sec-001", "sec-002",
            "FOLLOWS",
            logical_type=LogicalType.PREREQUISITE
        )

        assert edge.edge_type == "FOLLOWS"
        assert edge.properties["logical_type"] == LogicalType.PREREQUISITE

    def test_defines_edge(self):
        """F05-T009: 创建DEFINES边 (Chapter/Section → Concept)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_concept("c-001", "人工智能", "AI的定义...", "CS")

        edge = kg.add_edge(
            "ch-001", "c-001",
            "DEFINES",
            definition_text="本章定义了人工智能的基本概念"
        )

        assert edge.edge_type == "DEFINES"
        assert edge.properties["definition_text"] == "本章定义了人工智能的基本概念"

    def test_uses_edge(self):
        """F05-T010: 创建USES边 (Chapter/Section → Term)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_term("t-001", "机器学习", "ML的定义...", "CS")

        edge = kg.add_edge(
            "ch-001", "t-001",
            "USES",
            usage_context="本章多处使用机器学习术语"
        )

        assert edge.edge_type == "USES"
        assert edge.properties["usage_context"] == "本章多处使用机器学习术语"

    def test_references_edge_with_context(self):
        """F05-T011: 创建REFERENCES边 (Section → Section)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "定义节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "应用节", parent_chapter_id="ch-001")

        edge = kg.add_edge(
            "sec-001", "sec-002",
            "REFERENCES",
            reference_type=ReferenceType.APPLICATION,
            context="用于说明定义的应用场景"
        )

        assert edge.edge_type == "REFERENCES"
        assert edge.properties["reference_type"] == ReferenceType.APPLICATION
        assert edge.properties["context"] == "用于说明定义的应用场景"

    def test_similar_to_edge(self):
        """F05-T012: 创建SIMILAR_TO边 (Concept → Concept)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_concept("c-001", "人工智能", "AI定义...", "CS")
        kg.create_concept("c-002", "机器学习", "ML定义...", "CS")

        edge = kg.add_edge(
            "c-001", "c-002",
            "SIMILAR_TO",
            similarity_score=0.85
        )

        assert edge.edge_type == "SIMILAR_TO"
        assert edge.properties["similarity_score"] == 0.85


class TestKnowledgeGraphQueries:
    """知识图谱查询测试"""

    def test_get_chapter_context(self):
        """F05-T013: 查询章节上下文 (包含所有子节点和边)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "AI概述", 1)
        kg.create_section("sec-001", "定义", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "应用", parent_chapter_id="ch-001")
        kg.add_edge("ch-001", "sec-001", "CONTAINS")
        kg.add_edge("ch-001", "sec-002", "CONTAINS")

        context = kg.get_chapter_context("ch-001")

        assert "ch-001" in context
        assert len(context["sections"]) == 2
        assert "sec-001" in context["sections"]
        assert "sec-002" in context["sections"]
        assert len(context["edges"]) == 2

    def test_get_section_context(self):
        """F05-T014: 查询小节上下文"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "AI概述", 1)
        kg.create_section("sec-001", "定义", parent_chapter_id="ch-001")
        kg.create_subsection("sub-001", "AI历史", parent_section_id="sec-001")

        context = kg.get_section_context("sec-001")

        assert "sec-001" in context
        assert len(context["subsections"]) == 1
        assert "sub-001" in context["subsections"]

    def test_find_similar_concepts(self):
        """F05-T015: 查找相似概念"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_concept("c-001", "人工智能", "AI研究领域...", "CS")
        kg.create_concept("c-002", "机器学习", "ML是AI的子领域...", "CS")
        kg.create_concept("c-003", "深度学习", "DL是ML的子领域...", "CS")
        kg.add_edge("c-001", "c-002", "SIMILAR_TO", similarity_score=0.8)
        kg.add_edge("c-001", "c-003", "SIMILAR_TO", similarity_score=0.6)

        similar = kg.find_similar_concepts("c-001", threshold=0.5)

        assert len(similar) == 2
        assert similar[0]["concept_id"] == "c-002"
        assert similar[0]["similarity_score"] == 0.8

    def test_find_concepts_by_domain(self):
        """F05-T016: 按领域查找概念"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_concept("c-001", "人工智能", "AI...", "计算机科学")
        kg.create_concept("c-002", "企业管理", "管理...", "商业")
        kg.create_concept("c-003", "机器学习", "ML...", "计算机科学")

        concepts = kg.find_concepts_by_domain("计算机科学")

        assert len(concepts) == 2
        assert all(c.domain == "计算机科学" for c in concepts)

    def test_get_term_definitions(self):
        """F05-T017: 获取术语定义 (包括所有同义词)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_term("t-001", "人工智能", "AI的定义...", "CS", synonyms=["AI", "Artificial Intelligence"])

        term = kg.get_term("t-001")

        assert term.term == "人工智能"
        assert "AI" in term.synonyms
        assert "Artificial Intelligence" in term.synonyms

    def test_get_referencing_sections(self):
        """F05-T018: 获取引用某小节的所有小节"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "AI概述", 1)
        kg.create_section("sec-001", "定义节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "应用节", parent_chapter_id="ch-001")
        kg.create_section("sec-003", "对比节", parent_chapter_id="ch-001")
        kg.add_edge("sec-002", "sec-001", "REFERENCES", reference_type=ReferenceType.APPLICATION)
        kg.add_edge("sec-003", "sec-001", "REFERENCES", reference_type=ReferenceType.COMPARISON)

        referencing = kg.get_referencing_sections("sec-001")

        assert len(referencing) == 2
        assert "sec-002" in referencing
        assert "sec-003" in referencing

    def test_get_chapter_dependency_graph(self):
        """F05-T019: 获取章节依赖图"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_chapter("ch-002", "第二章", 2)
        kg.create_chapter("ch-003", "第三章", 3)
        kg.add_edge("ch-001", "ch-002", "FOLLOWS", logical_type=LogicalType.SEQUENTIAL)
        kg.add_edge("ch-002", "ch-003", "FOLLOWS", logical_type=LogicalType.SEQUENTIAL)
        kg.add_edge("ch-001", "ch-003", "FOLLOWS", logical_type=LogicalType.PREREQUISITE)

        deps = kg.get_chapter_dependency_graph()

        assert "ch-001" in deps
        assert "ch-002" in deps["ch-001"]
        assert "ch-003" in deps["ch-002"]
        assert "ch-003" in deps["ch-001"]


class TestKnowledgeGraphIntegrity:
    """知识图谱完整性测试"""

    def test_concept_definition_hash(self):
        """F05-T020: 概念定义哈希正确计算"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph
        import hashlib

        kg = KnowledgeGraph()
        definition = "人工智能是研究、开发用于模拟、延伸和扩展人的智能..."
        concept = kg.create_concept("c-001", "人工智能", definition, "CS")

        expected_hash = hashlib.sha256(definition.encode()).hexdigest()
        assert concept.definition_hash == expected_hash

    def test_chapter_word_count_tracking(self):
        """F05-T021: 章节字数统计"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001", word_count=1000)
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001", word_count=2000)

        context = kg.get_chapter_context("ch-001")
        assert context["total_word_count"] == 3000

    def test_node_status_transitions(self):
        """F05-T022: 节点状态转换"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph
        from f05_knowledge_graph.nodes import NodeStatus

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)

        kg.update_node_status("ch-001", NodeStatus.IN_REVIEW)
        node = kg.get_node("ch-001")
        assert node.status == NodeStatus.IN_REVIEW

        kg.update_node_status("ch-001", NodeStatus.APPROVED)
        node = kg.get_node("ch-001")
        assert node.status == NodeStatus.APPROVED


class TestKnowledgeGraphTraversal:
    """知识图谱遍历测试"""

    def test_bfs_traversal_from_chapter(self):
        """F05-T023: BFS遍历从章节开始"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        kg.add_edge("ch-001", "sec-001", "CONTAINS")
        kg.add_edge("ch-001", "sec-002", "CONTAINS")

        traversal = kg.bfs_traverse("ch-001")

        assert len(traversal) == 3
        assert traversal[0] == "ch-001"

    def test_dfs_traversal_from_concept(self):
        """F05-T024: DFS遍历从概念开始"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_concept("c-001", "AI", "...", "CS")
        kg.create_concept("c-002", "ML", "...", "CS")
        kg.create_concept("c-003", "DL", "...", "CS")
        kg.add_edge("c-001", "c-002", "SIMILAR_TO", similarity_score=0.8)
        kg.add_edge("c-002", "c-003", "SIMILAR_TO", similarity_score=0.9)

        traversal = kg.dfs_traverse("c-001")

        assert "c-001" in traversal
        assert "c-002" in traversal
        assert "c-003" in traversal

    def test_find_path_between_nodes(self):
        """F05-T025: 查找两个节点之间的路径"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_chapter("ch-002", "第二章", 2)
        kg.create_chapter("ch-003", "第三章", 3)
        kg.add_edge("ch-001", "ch-002", "FOLLOWS")
        kg.add_edge("ch-002", "ch-003", "FOLLOWS")

        path = kg.find_path("ch-001", "ch-003")

        assert path is not None
        assert path[0] == "ch-001"
        assert path[-1] == "ch-003"
        assert len(path) == 3


class TestKnowledgeGraphPersistence:
    """知识图谱持久化测试"""

    def test_export_to_dict(self):
        """F05-T026: 导出图谱为字典"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")

        data = kg.export_to_dict()

        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2

    def test_import_from_dict(self):
        """F05-T027: 从字典导入图谱"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        data = {
            "nodes": [
                {"id": "ch-001", "type": "Chapter", "title": "第一章", "order": 1, "status": "draft", "word_count": 0, "version": "1.0"}
            ],
            "edges": []
        }

        kg = KnowledgeGraph()
        kg.import_from_dict(data)

        node = kg.get_node("ch-001")
        assert node is not None
        assert node.title == "第一章"

    def test_add_edge_to_unregistered_source(self):
        """add_edge处理未注册的source (覆盖line 168)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        edge = kg.add_edge("unregistered_node", "some_target", "FOLLOWS")

        assert edge.source == "unregistered_node"
        assert "unregistered_node" in kg._adjacency

    def test_get_chapter_context_nonexistent(self):
        """get_chapter_context处理不存在的章节 (覆盖line 186)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        context = kg.get_chapter_context("nonexistent")

        assert context == {}

    def test_export_import_with_external_edge_reference(self):
        """import_from_dict处理指向未导入节点的边 (覆盖lines 385-386)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)

        data = kg.export_to_dict()
        data["edges"].append({
            "edge_type": "FOLLOWS",
            "source": "ch-001",
            "target": "external_node",
            "properties": {}
        })

        kg2 = KnowledgeGraph()
        kg2.import_from_dict(data)

        assert len(kg2._edges) == 1
        assert kg2._edges[0].target == "external_node"


class TestKnowledgeGraphUncoveredBranches:
    """覆盖KnowledgeGraph未测试的分支"""

    def test_find_similar_concepts_not_found(self):
        """find_similar_concepts处理不存在的概念 (覆盖lines 240-241)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        result = kg.find_similar_concepts("nonexistent-id")
        assert result == []

    def test_find_similar_concepts_target_not_found(self):
        """find_similar_concepts处理目标节点不存在 (覆盖line 251)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_concept("c-001", "AI", "definition", "CS")
        kg.add_edge("c-001", "ghost-node", "SIMILAR_TO", similarity_score=0.9)

        result = kg.find_similar_concepts("c-001")
        assert len(result) == 0

    def test_get_term_not_found(self):
        """get_term处理不存在的术语 (覆盖line 274)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        result = kg.get_term("nonexistent-id")
        assert result is None

    def test_get_referencing_sections(self):
        """get_referencing_sections (覆盖line 281)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "Chapter 1", 1)
        kg.create_section("sec-001", "Section 1", parent_chapter_id="ch-001")
        kg.add_edge("sec-001", "ch-001", "REFERENCES")

        result = kg.get_referencing_sections("ch-001")
        assert "sec-001" in result

    def test_bfs_traverse_node_not_found(self):
        """bfs_traverse处理不存在的起始节点 (覆盖line 297)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        result = kg.bfs_traverse("nonexistent-id")
        assert result == []

    def test_dfs_traverse_node_not_found(self):
        """dfs_traverse处理不存在的起始节点 (覆盖line 319)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        result = kg.dfs_traverse("nonexistent-id")
        assert result == []

    def test_find_path_not_found(self):
        """find_path处理不存在的节点 (覆盖lines 337-338)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "Chapter 1", 1)

        result = kg.find_path("ch-001", "nonexistent-id")
        assert result is None

    def test_find_path_same_node(self):
        """find_path处理相同节点 (覆盖line 341)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "Chapter 1", 1)

        result = kg.find_path("ch-001", "ch-001")
        assert result == ["ch-001"]

    def test_find_path_no_path_exists(self):
        """find_path处理不存在路径 (覆盖line 357)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "Chapter 1", 1)
        kg.create_chapter("ch-002", "Chapter 2", 2)

        result = kg.find_path("ch-001", "ch-002")
        assert result is None

    def test_get_section_context_nonexistent(self):
        """get_section_context处理不存在的section (覆盖line 217)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        context = kg.get_section_context("nonexistent-section")
        assert context == {}

    def test_bfs_traverse_with_visited_node(self):
        """bfs_traverse处理已访问节点 (覆盖line 306)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "Chapter 1", 1)
        kg.create_section("sec-001", "Section 1", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "Section 2", parent_chapter_id="ch-001")
        kg.add_edge("ch-001", "sec-001", "CONTAINS")
        kg.add_edge("ch-001", "sec-002", "CONTAINS")
        kg.add_edge("sec-001", "sec-002", "FOLLOWS")

        # Create a cycle to trigger visited check
        kg.add_edge("sec-002", "ch-001", "FOLLOWS")

        # BFS should handle cycle gracefully
        result = kg.bfs_traverse("ch-001")
        assert len(result) > 0
        assert "ch-001" in result

    def test_dfs_traverse_with_visited_node(self):
        """dfs_traverse处理已访问节点 (覆盖line 326)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.create_concept("c-001", "AI", "...", "CS")
        kg.create_concept("c-002", "ML", "...", "CS")
        kg.add_edge("c-001", "c-002", "SIMILAR_TO", similarity_score=0.8)

        # Create a cycle
        kg.add_edge("c-002", "c-001", "SIMILAR_TO", similarity_score=0.8)

        # DFS should handle cycle gracefully
        result = kg.dfs_traverse("c-001")
        assert "c-001" in result
        assert "c-002" in result


class TestNodesToDictCoverage:
    """覆盖nodes.py中to_dict方法的分支"""

    def test_subsection_node_to_dict(self):
        """SubsectionNode.to_dict覆盖 (覆盖lines 102-108)"""
        from f05_knowledge_graph.nodes import SubsectionNode

        node = SubsectionNode(
            id="sub-001",
            title="小节标题",
            order=1,
            content="小节内容",
            parent_section_id="sec-001"
        )

        d = node.to_dict()
        assert d["id"] == "sub-001"
        assert d["type"] == "Subsection"
        assert d["parent_section_id"] == "sec-001"
        assert d["content"] == "小节内容"

    def test_concept_node_to_dict(self):
        """ConceptNode.to_dict覆盖 (覆盖line 128)"""
        from f05_knowledge_graph.nodes import ConceptNode

        node = ConceptNode(
            id="c-001",
            name="人工智能",
            definition="AI的定义",
            domain="计算机科学",
            related_terms=["AI", "ML"]
        )

        d = node.to_dict()
        assert d["id"] == "c-001"
        assert d["type"] == "Concept"
        assert d["name"] == "人工智能"
        assert d["domain"] == "计算机科学"
        assert "definition_hash" in d

    def test_term_node_to_dict(self):
        """TermNode.to_dict覆盖 (覆盖line 154)"""
        from f05_knowledge_graph.nodes import TermNode

        node = TermNode(
            id="t-001",
            term="机器学习",
            definition="ML的定义",
            domain="计算机科学",
            synonyms=["ML", "Machine Learning"]
        )

        d = node.to_dict()
        assert d["id"] == "t-001"
        assert d["type"] == "Term"
        assert d["term"] == "机器学习"
        assert "synonyms" in d
        assert "first_defined_at" in d

    def test_create_node_unknown_type_raises(self):
        """create_node处理未知类型 (覆盖line 176)"""
        from f05_knowledge_graph.nodes import create_node

        with pytest.raises(ValueError) as exc_info:
            create_node("UnknownType", id="test", title="Test")

        assert "Unknown node type" in str(exc_info.value)
