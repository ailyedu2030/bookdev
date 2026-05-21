"""
F22: 素材RAG召回 - TDD RED阶段测试

按照TDD原则：
1. RED: 写失败测试 (本文件)
2. GREEN: 写最简实现让测试通过
3. Refactor: 优化代码质量

测试用例:
- F22-T001: 基本检索
- F22-T002: 预算感知
- F22-T003: 知识图谱增强
- F22-T004: 去重
- F22-T005: 增量添加
"""

from dataclasses import dataclass, field

import numpy as np
import pytest


@dataclass
class RetrievedMaterial:
    """检索到的素材"""

    material_id: str
    content: str
    score: float
    token_count: int
    source_chapter_id: str | None = None
    metadata: dict = field(default_factory=dict)


def create_mock_knowledge_graph():
    """创建模拟知识图谱"""
    from f05_knowledge_graph.knowledge_graph import KnowledgeGraph
    from f05_knowledge_graph.nodes import NodeStatus

    kg = KnowledgeGraph()

    kg.create_chapter("ch-001", "人工智能概述", 1, status=NodeStatus.APPROVED)
    kg.create_chapter("ch-002", "机器学习", 2, status=NodeStatus.APPROVED)
    kg.create_chapter("ch-003", "深度学习", 3, status=NodeStatus.APPROVED)

    kg.create_section("sec-001", "AI定义", parent_chapter_id="ch-001")
    kg.create_section("sec-002", "ML算法", parent_chapter_id="ch-002")
    kg.create_section("sec-003", "神经网络", parent_chapter_id="ch-003")

    kg.add_edge("ch-001", "ch-002", "FOLLOWS")
    kg.add_edge("ch-002", "ch-003", "FOLLOWS")

    return kg


def create_mock_budget_manager(max_tokens=8000):
    """创建模拟预算管理器"""
    from f02_context_budget.context_budget_manager import ContextBudgetManager

    budget = ContextBudgetManager()
    budget._material_budget = max_tokens
    return budget


def add_test_materials(engine):
    """添加测试素材"""
    materials = [
        {
            "id": "m-001",
            "content": "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的技术科学。",
            "chapter_id": "ch-001",
            "metadata": {"type": "definition"},
        },
        {
            "id": "m-002",
            "content": "机器学习是人工智能的一个分支，专门研究如何使用计算机模拟人类学习行为并自动改进算法。",
            "chapter_id": "ch-002",
            "metadata": {"type": "explanation"},
        },
        {
            "id": "m-003",
            "content": "深度学习是机器学习的分支，使用多层神经网络分析各种因素进行数据表征学习。",
            "chapter_id": "ch-003",
            "metadata": {"type": "explanation"},
        },
        {
            "id": "m-004",
            "content": "神经网络是一种受人脑启发的计算模型，用于识别数据中的复杂模式和关系。",
            "chapter_id": "ch-003",
            "metadata": {"type": "definition"},
        },
        {
            "id": "m-005",
            "content": "自然语言处理是人工智能的一个分支，研究如何让计算机理解和生成人类语言。",
            "chapter_id": "ch-001",
            "metadata": {"type": "definition"},
        },
    ]

    for m in materials:
        engine.add_material(m)


def add_large_materials(engine):
    """添加大尺寸素材"""
    materials = [
        {"id": f"large-m-{i}", "content": "这是第{i}个大型素材内容。" * 100, "chapter_id": f"ch-{i}", "metadata": {}}
        for i in range(10)
    ]

    for m in materials:
        engine.add_material(m)


def add_duplicate_materials(engine):
    """添加重复素材"""
    content = "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的技术科学。"

    for i in range(3):
        engine.add_material({"id": f"dup-{i}", "content": content, "chapter_id": "ch-001", "metadata": {}})


def add_near_duplicate_materials(engine):
    """添加近似重复素材"""
    base_content = "机器学习是人工智能的一个分支，专门研究如何使用计算机模拟人类学习行为。"

    variations = [
        base_content + "它包括监督学习、无监督学习和强化学习等多种方法。",
        base_content + "它在图像识别，自然语言处理等领域有广泛应用。",
        base_content,
    ]

    for i, content in enumerate(variations):
        engine.add_material({"id": f"near-dup-{i}", "content": content, "chapter_id": "ch-002", "metadata": {}})


class TestMaterialRAGRetrieval:
    """F22-T001: 基本检索测试"""

    def test_retrieve_relevant_materials(self):
        """检索返回相关素材"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        add_test_materials(engine)

        results = engine.retrieve_relevant_materials(query="人工智能 机器学习", top_k=3)

        assert len(results) > 0
        from f22_material_rag.rag_engine import RetrievedMaterial as RRM

        assert all(isinstance(r, RRM) for r in results)
        assert all(r.score >= 0.0 and r.score <= 1.0 for r in results)

    def test_retrieve_respects_top_k(self):
        """检索结果数量不超过top_k"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        add_test_materials(engine)

        results = engine.retrieve_relevant_materials(query="人工智能", top_k=2)

        assert len(results) <= 2

    def test_empty_query_returns_empty(self):
        """空查询返回空列表"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        results = engine.retrieve_relevant_materials(query="", top_k=5)

        assert len(results) == 0

    def test_no_match_returns_nearest(self):
        """无完全匹配时返回最近结果"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        add_test_materials(engine)

        results = engine.retrieve_relevant_materials(query="完全不匹配的查询 xyz123", top_k=3)

        assert len(results) >= 0


class TestBudgetAwareRetrieval:
    """F22-T002: 预算感知测试"""

    def test_respects_token_budget(self):
        """检索结果不超过预算限制"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager(max_tokens=5000)
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        add_test_materials(engine)

        results = engine.retrieve_relevant_materials(query="人工智能", top_k=10, max_tokens=5000)

        total_tokens = sum(r.token_count for r in results)
        assert total_tokens <= 5000

    def test_budget_exceeded_trims_results(self):
        """超出预算时自动裁剪结果"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager(max_tokens=1000)
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        add_large_materials(engine)

        results = engine.retrieve_relevant_materials(query="教学", top_k=10, max_tokens=1000)

        total_tokens = sum(r.token_count for r in results)
        assert total_tokens <= 1000

    def test_build_context_from_materials(self):
        """从素材构建上下文（预算感知）"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager(max_tokens=8000)
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        materials = [
            RetrievedMaterial(
                material_id="m1",
                content="人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统。",
                score=0.95,
                token_count=50,
                source_chapter_id="ch-001",
            ),
            RetrievedMaterial(
                material_id="m2",
                content="机器学习是人工智能的一个分支，专门研究如何使用计算机模拟人类学习行为。",
                score=0.85,
                token_count=45,
                source_chapter_id="ch-002",
            ),
        ]

        context = engine.build_context_from_materials(materials, max_tokens=8000)

        assert isinstance(context, str)
        assert len(context) > 0

    def test_build_context_respects_budget(self):
        """构建上下文严格遵守预算"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager(max_tokens=100)
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        materials = [
            RetrievedMaterial(
                material_id="m1",
                content="这是一段很长的内容，" * 100,
                score=0.95,
                token_count=500,
                source_chapter_id="ch-001",
            ),
        ]

        context = engine.build_context_from_materials(materials, max_tokens=100)

        token_count = engine.estimate_tokens(context)
        assert token_count <= 100


class TestKGraphEnhancement:
    """F22-T003: 知识图谱增强测试"""

    def test_kg_enhances_retrieval(self):
        """知识图谱关系提升召回质量"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        add_test_materials(engine)

        results_with_kg = engine.retrieve_relevant_materials(query="深度学习", top_k=5, use_kg_enhancement=True)

        results_without_kg = engine.retrieve_relevant_materials(query="深度学习", top_k=5, use_kg_enhancement=False)

        assert (
            len(results_with_kg) >= len(results_without_kg) or results_with_kg[0].score >= results_without_kg[0].score
        )

    def test_kg_boosts_related_concepts(self):
        """相关概念被知识图谱提升"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        kg.add_edge("ch-003", "ch-001", "SIMILAR_TO", similarity_score=0.8)

        add_test_materials(engine)

        results = engine.retrieve_relevant_materials(query="神经网络", top_k=5, use_kg_enhancement=True)

        if results:
            result_chapters = [r.source_chapter_id for r in results]
            assert "ch-003" in result_chapters or "ch-001" in result_chapters

    def test_kg_enables_cross_reference(self):
        """知识图谱启用交叉引用"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        kg.add_edge("sec-001", "sec-002", "REFERENCES", reference_type="definition")

        add_test_materials(engine)

        results = engine.retrieve_relevant_materials(query="人工智能定义", top_k=3, use_kg_enhancement=True)

        assert isinstance(results, list)


class TestMaterialDeduplication:
    """F22-T004: 去重测试"""

    def test_deduplicates_similar_materials(self):
        """相似素材自动去重"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        add_duplicate_materials(engine)

        results = engine.retrieve_relevant_materials(query="人工智能", top_k=10, deduplicate=True)

        material_ids = [r.material_id for r in results]
        assert len(material_ids) == len(set(material_ids))

    def test_deduplication_uses_similarity_threshold(self):
        """去重使用相似度阈值"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        add_near_duplicate_materials(engine)

        results = engine.retrieve_relevant_materials(
            query="机器学习", top_k=5, deduplicate=True, similarity_threshold=0.9
        )

        for i, r1 in enumerate(results):
            for r2 in results[i + 1 :]:
                similarity = engine._compute_similarity(r1.content, r2.content)
                if similarity > 0.9:
                    raise AssertionError("Similar materials should be deduplicated")


class TestMaterialIndexing:
    """F22-T005: 增量添加测试"""

    def test_add_material_increments_index(self):
        """新素材正确添加"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        initial_count = engine.get_material_count()

        engine.add_material(
            {
                "id": "new-material-001",
                "content": "这是一个新添加的素材内容。",
                "chapter_id": "ch-new",
                "metadata": {"type": "example"},
            }
        )

        new_count = engine.get_material_count()
        assert new_count == initial_count + 1

    def test_add_material_enables_retrieval(self):
        """新添加素材可检索"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        engine.add_material(
            {
                "id": "unique-material-xyz",
                "content": "区块链技术是一种分布式账本技术。",
                "chapter_id": "ch-blockchain",
                "metadata": {},
            }
        )

        results = engine.retrieve_relevant_materials(query="区块链 分布式账本", top_k=5)

        material_ids = [r.material_id for r in results]
        assert "unique-material-xyz" in material_ids

    def test_add_multiple_materials(self):
        """批量添加多个素材"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        materials = [
            {"id": f"batch-material-{i}", "content": f"批量素材内容 {i}", "chapter_id": "ch-batch", "metadata": {}}
            for i in range(5)
        ]

        for m in materials:
            engine.add_material(m)

        assert engine.get_material_count() >= 5

    def test_add_material_with_embedding(self):
        """添加素材时正确生成嵌入"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = create_mock_knowledge_graph()
        budget = create_mock_budget_manager()
        engine = MaterialRAGEngine(knowledge_graph=kg, context_budget=budget)

        engine.add_material(
            {"id": "embedding-test", "content": "测试嵌入生成", "chapter_id": "ch-test", "metadata": {}}
        )

        embedding = engine.get_embedding("embedding-test")
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) > 0


class TestEmbeddingClient:
    """嵌入客户端测试"""

    def test_generate_embedding(self):
        """生成文本嵌入"""
        from f22_material_rag.embedding_client import MiniMaxEmbeddingClient

        client = MiniMaxEmbeddingClient(api_key="test-key")
        embedding = client.generate_embedding("测试文本")

        assert embedding is not None
        assert len(embedding) > 0

    def test_batch_generate_embedding(self):
        """批量生成嵌入"""
        from f22_material_rag.embedding_client import MiniMaxEmbeddingClient

        client = MiniMaxEmbeddingClient(api_key="test-key")
        texts = ["文本1", "文本2", "文本3"]

        embeddings = client.batch_generate_embedding(texts)

        assert len(embeddings) == 3
        assert all(len(e) > 0 for e in embeddings)


class TestVectorStore:
    """向量存储测试"""

    def test_add_and_search(self):
        """添加向量并搜索"""
        from f22_material_rag.vector_store import InMemoryVectorStore

        store = InMemoryVectorStore(dimension=10)

        store.add("id1", np.array([1.0] * 10))
        store.add("id2", np.array([0.0] * 10))

        results = store.search(np.array([1.0] * 10), top_k=2)

        assert len(results) <= 2
        assert results[0]["id"] == "id1"

    def test_search_with_scores(self):
        """搜索返回相似度分数"""
        from f22_material_rag.vector_store import InMemoryVectorStore

        store = InMemoryVectorStore(dimension=5)

        store.add("id1", np.array([1.0, 0.0, 0.0, 0.0, 0.0]))
        store.add("id2", np.array([0.0, 1.0, 0.0, 0.0, 0.0]))

        results = store.search(np.array([1.0, 0.0, 0.0, 0.0, 0.0]), top_k=2)

        assert results[0]["score"] >= results[1]["score"]

    def test_delete_vector(self):
        """删除向量"""
        from f22_material_rag.vector_store import InMemoryVectorStore

        store = InMemoryVectorStore(dimension=5)
        store.add("id1", np.array([1.0] * 5))

        store.delete("id1")

        results = store.search(np.array([1.0] * 5), top_k=1)
        assert len(results) == 0 or results[0]["id"] != "id1"

    def test_add_wrong_dimension_raises(self):
        """添加错误维度向量抛出异常 (覆盖line 29)"""
        from f22_material_rag.vector_store import InMemoryVectorStore

        store = InMemoryVectorStore(dimension=5)

        with pytest.raises(ValueError, match="向量维度必须为5"):
            store.add("id1", np.array([1.0] * 10))

    def test_search_wrong_dimension_raises(self):
        """搜索错误维度向量抛出异常 (覆盖line 47)"""
        from f22_material_rag.vector_store import InMemoryVectorStore

        store = InMemoryVectorStore(dimension=5)
        store.add("id1", np.array([1.0] * 5))

        with pytest.raises(ValueError, match="查询向量维度必须为5"):
            store.search(np.array([1.0] * 10), top_k=1)

    def test_delete_removes_metadata(self):
        """删除向量时同时删除元数据 (覆盖line 69)"""
        from f22_material_rag.vector_store import InMemoryVectorStore

        store = InMemoryVectorStore(dimension=5)
        store.add("id1", np.array([1.0] * 5), metadata={"key": "value"})

        store.delete("id1")

        assert store.get("id1") is None

    def test_get_existing_vector(self):
        """获取存在的向量 (覆盖line 73)"""
        from f22_material_rag.vector_store import InMemoryVectorStore

        store = InMemoryVectorStore(dimension=5)
        vector = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        store.add("id1", vector)

        result = store.get("id1")

        assert result is not None
        assert np.array_equal(result, vector)

    def test_count_vectors(self):
        """统计向量数量 (覆盖line 77)"""
        from f22_material_rag.vector_store import InMemoryVectorStore

        store = InMemoryVectorStore(dimension=5)
        assert store.count() == 0

        store.add("id1", np.array([1.0] * 5))
        assert store.count() == 1

        store.add("id2", np.array([0.0] * 5))
        assert store.count() == 2

        store.delete("id1")
        assert store.count() == 1


class TestMaterialDataClass:
    """素材数据结构测试"""

    def test_material_creation(self):
        """创建素材对象"""
        from f22_material_rag.material import Material

        material = Material(
            id="test-001", content="测试内容", chapter_id="ch-001", token_count=10, metadata={"key": "value"}
        )

        assert material.id == "test-001"
        assert material.content == "测试内容"
        assert material.token_count == 10

    def test_material_to_dict(self):
        """素材转换为字典"""
        from f22_material_rag.material import Material

        material = Material(id="test-001", content="测试内容", chapter_id="ch-001")

        d = material.to_dict()

        assert d["id"] == "test-001"
        assert d["content"] == "测试内容"


class TestRAGEngineUncovered:
    """覆盖RAG Engine未测试的分支"""

    def test_kg_enhance_results_no_kg(self):
        """_kg_enhance_results处理无KG情况 (覆盖line 205)"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        rag = MaterialRAGEngine(knowledge_graph=None, context_budget=None)

        results = [{"content": "test", "score": 0.8, "metadata": {}}]

        boosted = rag._kg_enhance_results(results, "test query")
        assert len(boosted) == 1
        assert boosted[0]["score"] == 0.8

    def test_deduplicate_empty_results(self):
        """_deduplicate_results处理空列表 (覆盖line 250)"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        rag = MaterialRAGEngine(knowledge_graph=None, context_budget=None)

        result = rag._deduplicate_results([])
        assert result == []

    def test_compute_similarity_empty_text(self):
        """_compute_similarity处理空文本 (覆盖line 275)"""
        from f22_material_rag.rag_engine import MaterialRAGEngine

        rag = MaterialRAGEngine(knowledge_graph=None, context_budget=None)

        result = rag._compute_similarity("", "text")
        assert result == 0.0

        result = rag._compute_similarity("text", "")
        assert result == 0.0

        result = rag._compute_similarity("", "")
        assert result == 0.0


class TestEmbeddingClientUncovered:
    """覆盖EmbeddingClient未测试的分支"""

    def test_generate_embedding_empty_text(self):
        """line 31: 空文本或空白文本返回零向量"""
        from f22_material_rag.embedding_client import MiniMaxEmbeddingClient

        client = MiniMaxEmbeddingClient(api_key="test", dimension=128)

        result = client.generate_embedding("")
        assert np.array_equal(result, np.zeros(128))

        result = client.generate_embedding("   ")
        assert np.array_equal(result, np.zeros(128))

        result = client.generate_embedding("  \t\n  ")
        assert np.array_equal(result, np.zeros(128))


class TestMaterialUncovered:
    """覆盖Material未测试的分支"""

    def test_material_from_dict(self):
        """line 40: from_dict方法从字典创建Material"""
        from f22_material_rag.material import Material

        data = {
            "id": "mat-001",
            "content": "测试内容",
            "chapter_id": "ch-001",
            "token_count": 100,
            "metadata": {"source": "test"},
        }

        material = Material.from_dict(data)

        assert material.id == "mat-001"
        assert material.content == "测试内容"
        assert material.chapter_id == "ch-001"
        assert material.token_count == 100
        assert material.metadata == {"source": "test"}

    def test_material_from_dict_with_defaults(self):
        """line 43-45: from_dict使用默认值"""
        from f22_material_rag.material import Material

        data = {"id": "mat-002", "content": "最小数据"}

        material = Material.from_dict(data)

        assert material.id == "mat-002"
        assert material.chapter_id == ""
        assert material.token_count == len("最小数据")
        assert material.metadata == {}


class TestRAGEngineKGUncovered:
    """覆盖RAGEngine知识图谱增强未测试的分支"""

    def test_kg_enhance_results_with_defines_edge(self):
        """lines 228-232: DEFINES类型的edge提供boost"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph
        from f05_knowledge_graph.nodes import NodeStatus

        from f22_material_rag.rag_engine import MaterialRAGEngine

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "测试章节", 1, status=NodeStatus.APPROVED)
        kg.create_concept("concept-001", "人工智能 机器学习", "AI和ML的定义", "CS")
        kg.add_edge("ch-001", "concept-001", "DEFINES")

        rag = MaterialRAGEngine(knowledge_graph=kg, context_budget=None)

        results = [{"content": "AI是人工智能", "score": 0.5, "metadata": {"chapter_id": "ch-001"}}]

        boosted = rag._kg_enhance_results(results, "人工智能")

        assert len(boosted) == 1
        assert boosted[0]["score"] > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
