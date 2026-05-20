"""
F27: GraphRAG问答系统 - TDD RED阶段测试

基于知识图谱的问答系统。
验收标准:
- 支持知识图谱路径查询
- 支持向量检索增强
- 单元测试覆盖率 ≥80%
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from f27_graph_rag.graph_rag_query import (
    GraphNode,
    GraphEdge,
    KnowledgeGraph,
    RAGDocument,
    RAGEngine,
    GraphRAGAnswer,
)


class TestGraphRAGQuery:
    """GraphRAG查询测试"""

    def test_graph_rag_query_class_exists(self):
        """F27-T001: GraphRAGQuery类必须存在"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        assert GraphRAGQuery is not None

    def test_graph_rag_query_initialization(self):
        """F27-T002: GraphRAGQuery正确初始化"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        kg = KnowledgeGraph()
        rag = RAGEngine()
        query_engine = GraphRAGQuery(kg, rag)
        assert query_engine.kg is not None
        assert query_engine.rag is not None

    def test_query_returns_graph_rag_answer(self):
        """F27-T003: query方法返回GraphRAGAnswer"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        kg = KnowledgeGraph()
        rag = RAGEngine()
        query_engine = GraphRAGQuery(kg, rag)
        result = query_engine.query("什么是机器学习?")
        assert isinstance(result, GraphRAGAnswer)

    def test_query_answer_field(self):
        """F27-T004: GraphRAGAnswer包含answer字段"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        kg = KnowledgeGraph()
        rag = RAGEngine()
        query_engine = GraphRAGQuery(kg, rag)
        result = query_engine.query("什么是机器学习?")
        assert hasattr(result, 'answer')
        assert isinstance(result.answer, str)

    def test_query_confidence_field(self):
        """F27-T005: GraphRAGAnswer包含confidence字段"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        kg = KnowledgeGraph()
        rag = RAGEngine()
        query_engine = GraphRAGQuery(kg, rag)
        result = query_engine.query("什么是机器学习?")
        assert hasattr(result, 'confidence')
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    def test_query_sources_field(self):
        """F27-T006: GraphRAGAnswer包含sources字段"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        kg = KnowledgeGraph()
        rag = RAGEngine()
        query_engine = GraphRAGQuery(kg, rag)
        result = query_engine.query("什么是机器学习?")
        assert hasattr(result, 'sources')
        assert isinstance(result.sources, list)

    def test_query_graph_paths_field(self):
        """F27-T007: GraphRAGAnswer包含graph_paths字段"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        kg = KnowledgeGraph()
        rag = RAGEngine()
        query_engine = GraphRAGQuery(kg, rag)
        result = query_engine.query("什么是机器学习?")
        assert hasattr(result, 'graph_paths')
        assert isinstance(result.graph_paths, list)

    def test_query_with_kg_nodes(self):
        """F27-T008: query方法能利用知识图谱节点"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        kg = KnowledgeGraph()
        kg.add_node(GraphNode(id="n1", label="机器学习", properties={"定义": "让机器从数据中学习"}))
        kg.add_node(GraphNode(id="n2", label="人工智能", properties={}))
        kg.add_edge(GraphEdge(source="n1", target="n2", relation="属于"))

        rag = RAGEngine()
        query_engine = GraphRAGQuery(kg, rag)
        result = query_engine.query("机器学习和人工智能有什么关系?")

        assert result.answer is not None
        assert len(result.sources) > 0

    def test_query_with_rag_documents(self):
        """F27-T009: query方法能利用RAG文档"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        kg = KnowledgeGraph()
        rag = RAGEngine()
        rag.add_document(RAGDocument(
            id="doc1",
            content="机器学习是人工智能的子领域",
            embedding=[0.1] * 128
        ))

        query_engine = GraphRAGQuery(kg, rag)
        result = query_engine.query("什么是机器学习?")

        assert result.answer is not None

    def test_query_parses_intent(self):
        """F27-T010: query方法能解析问题意图"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        kg = KnowledgeGraph()
        rag = RAGEngine()
        query_engine = GraphRAGQuery(kg, rag)

        intent = query_engine._parse_intent("机器学习和深度学习有什么区别?")
        assert intent is not None
        assert isinstance(intent, dict)

    def test_query_finds_graph_paths(self):
        """F27-T011: query方法能找到知识图谱路径"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        kg = KnowledgeGraph()
        kg.add_node(GraphNode(id="n1", label="机器学习"))
        kg.add_node(GraphNode(id="n2", label="深度学习"))
        kg.add_node(GraphNode(id="n3", label="神经网络"))
        kg.add_edge(GraphEdge(source="n1", target="n2", relation="包含"))
        kg.add_edge(GraphEdge(source="n2", target="n3", relation="基于"))

        rag = RAGEngine()
        query_engine = GraphRAGQuery(kg, rag)
        paths = query_engine._find_graph_paths("n1", "n3")

        assert isinstance(paths, list)

    def test_query_uses_vector_search(self):
        """F27-T012: query方法使用向量搜索"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        kg = KnowledgeGraph()
        rag = RAGEngine()
        rag.add_document(RAGDocument(
            id="doc1",
            content="Python是一种编程语言",
            embedding=[0.1] * 128
        ))

        query_engine = GraphRAGQuery(kg, rag)
        results = query_engine._vector_search("Python是什么?", top_k=3)

        assert isinstance(results, list)

    def test_query_generates_answer(self):
        """F27-T013: query方法能生成答案"""
        from f27_graph_rag.graph_rag_query import GraphRAGQuery

        kg = KnowledgeGraph()
        rag = RAGEngine()
        query_engine = GraphRAGQuery(kg, rag)

        answer = query_engine._generate_answer(
            question="什么是AI?",
            graph_context=["机器学习是AI的子领域"],
            rag_context=["人工智能使机器具有人类智能"]
        )

        assert isinstance(answer, str)
        assert len(answer) > 0


class TestKnowledgeGraph:
    """知识图谱测试"""

    def test_add_node(self):
        """F27-T014: 可以添加节点"""
        from f27_graph_rag.graph_rag_query import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.add_node(GraphNode(id="n1", label="测试"))
        assert len(kg.nodes) == 1

    def test_add_edge(self):
        """F27-T015: 可以添加边"""
        from f27_graph_rag.graph_rag_query import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.add_node(GraphNode(id="n1", label="A"))
        kg.add_node(GraphNode(id="n2", label="B"))
        kg.add_edge(GraphEdge(source="n1", target="n2", relation="连接"))

        assert len(kg.edges) == 1

    def test_find_node(self):
        """F27-T016: 可以查找节点"""
        from f27_graph_rag.graph_rag_query import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.add_node(GraphNode(id="n1", label="测试节点"))

        node = kg.find_node("n1")
        assert node is not None
        assert node.id == "n1"

    def test_find_nonexistent_node(self):
        """F27-T017: 查找不存在的节点返回None"""
        from f27_graph_rag.graph_rag_query import KnowledgeGraph

        kg = KnowledgeGraph()
        node = kg.find_node("nonexistent")
        assert node is None

    def test_find_path_same_start_and_end(self):
        """F27-T018: find_path起点终点相同时返回[start] (覆盖line 52)"""
        from f27_graph_rag.graph_rag_query import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.add_node(GraphNode(id="n1", label="A"))

        path = kg.find_path("n1", "n1")

        assert path == ["n1"]

    def test_find_path_no_path_exists(self):
        """F27-T019: find_path无路径时返回空列表 (覆盖line 68)"""
        from f27_graph_rag.graph_rag_query import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.add_node(GraphNode(id="n1", label="A"))
        kg.add_node(GraphNode(id="n2", label="B"))

        path = kg.find_path("n1", "n2")

        assert path == []

    def test_search_with_partial_word_match(self):
        """F27-T020: search部分单词匹配评分 (覆盖line 102)"""
        from f27_graph_rag.graph_rag_query import RAGEngine, RAGDocument

        engine = RAGEngine()
        engine.add_document(RAGDocument(id="doc1", content="Python programming language"))
        engine.add_document(RAGDocument(id="doc2", content="JavaScript is different"))

        results = engine.search("Python", top_k=2)

        assert len(results) >= 1


class TestRAGEngine:
    """RAG引擎测试"""

    def test_add_document(self):
        """F27-T018: 可以添加文档"""
        from f27_graph_rag.graph_rag_query import RAGEngine

        rag = RAGEngine()
        rag.add_document(RAGDocument(id="doc1", content="测试内容"))

        assert len(rag.documents) == 1

    def test_search_documents(self):
        """F27-T019: 可以搜索文档"""
        from f27_graph_rag.graph_rag_query import RAGEngine

        rag = RAGEngine()
        rag.add_document(RAGDocument(id="doc1", content="机器学习是人工智能"))
        rag.add_document(RAGDocument(id="doc2", content="深度学习是机器学习的子领域"))

        results = rag.search("机器学习", top_k=2)
        assert isinstance(results, list)
