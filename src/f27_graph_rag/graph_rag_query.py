"""
F27: GraphRAG问答系统

基于知识图谱的问答系统。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class GraphNode:
    """知识图谱节点"""
    id: str
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """知识图谱边"""
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    """知识图谱"""
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode):
        """添加节点"""
        self.nodes.append(node)

    def add_edge(self, edge: GraphEdge):
        """添加边"""
        self.edges.append(edge)

    def find_node(self, node_id: str) -> Optional[GraphNode]:
        """查找节点"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def find_path(self, start: str, end: str, max_depth: int = 10) -> List[str]:
        """
        查找路径（简单BFS）
        
        Fixed: Added max_depth to prevent infinite loops and improve safety
        """
        if start == end:
            return [start]

        visited = {start}
        queue = [(start, [start])]
        depth_count = {start: 0}

        while queue:
            current, path = queue.pop(0)
            current_depth = depth_count.get(current, 0)
            
            # Safety check to prevent infinite traversal
            if current_depth >= max_depth:
                continue

            for edge in self.edges:
                if edge.source == current and edge.target not in visited:
                    new_path = path + [edge.target]
                    if edge.target == end:
                        return new_path
                    visited.add(edge.target)
                    depth_count[edge.target] = current_depth + 1
                    queue.append((edge.target, new_path))

        return []


@dataclass
class RAGDocument:
    """RAG文档"""
    id: str
    content: str
    embedding: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGEngine:
    """RAG引擎"""
    documents: List[RAGDocument] = field(default_factory=list)

    def add_document(self, doc: RAGDocument):
        """添加文档"""
        self.documents.append(doc)

    def search(self, query: str, top_k: int = 5) -> List[RAGDocument]:
        """搜索文档（简单关键词匹配）"""
        query_lower = query.lower()
        scored = []

        for doc in self.documents:
            if query_lower in doc.content.lower():
                scored.append((doc, 1.0))
            else:
                words = query_lower.split()
                content_lower = doc.content.lower()
                matches = sum(1 for w in words if w in content_lower)
                if matches > 0:
                    scored.append((doc, matches / len(words)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[:top_k]]


@dataclass
class GraphRAGAnswer:
    """GraphRAG答案"""
    answer: str
    confidence: float
    sources: List[str]
    graph_paths: List[List[str]]
    evidence: List[str]


class GraphRAGQuery:
    """GraphRAG问答"""

    def __init__(self, knowledge_graph: KnowledgeGraph, rag_engine: RAGEngine):
        """初始化GraphRAG查询引擎

        Args:
            knowledge_graph: 知识图谱
            rag_engine: RAG引擎
        """
        self.kg = knowledge_graph
        self.rag = rag_engine

    def query(self, question: str) -> GraphRAGAnswer:
        """执行GraphRAG查询

        Args:
            question: 问题

        Returns:
            GraphRAGAnswer答案对象
        """
        intent = self._parse_intent(question)

        graph_context = self._get_graph_context(intent)
        rag_context = self._get_rag_context(question)

        answer = self._generate_answer(
            question=question,
            graph_context=graph_context,
            rag_context=rag_context
        )

        sources = list(set(
            [n.label for n in self.kg.nodes]
            + [doc.id for doc in self.rag.documents[:3]]
        ))

        graph_paths = []
        # Fixed: Limit path finding to prevent excessive computation
        for edge in self.kg.edges[:3]:
            path = self.kg.find_path(edge.source, edge.target, max_depth=10)
            if path:
                graph_paths.append(path)

        confidence = 0.5 + (0.3 if graph_context else 0) + (0.2 if rag_context else 0)

        return GraphRAGAnswer(
            answer=answer,
            confidence=min(confidence, 1.0),
            sources=sources,
            graph_paths=graph_paths[:5],
            evidence=graph_context + rag_context
        )

    def _parse_intent(self, question: str) -> Dict[str, Any]:
        """解析问题意图

        Args:
            question: 问题

        Returns:
            意图字典
        """
        question_lower = question.lower()

        intent = {
            "original": question,
            "type": "general",
            "entities": []
        }

        for node in self.kg.nodes:
            if node.label.lower() in question_lower:
                intent["entities"].append(node.id)
                intent["type"] = "comparison" if "什么" in question_lower or "区别" in question_lower else "definition"

        return intent

    def _get_graph_context(self, intent: Dict[str, Any]) -> List[str]:
        """获取知识图谱上下文

        Args:
            intent: 意图字典

        Returns:
            上下文列表
        """
        context = []

        for entity_id in intent.get("entities", []):
            node = self.kg.find_node(entity_id)
            if node:
                context.append(f"{node.label}: {node.properties.get('定义', node.label)}")

                for edge in self.kg.edges:
                    if edge.source == entity_id or edge.target == entity_id:
                        neighbor_id = edge.target if edge.source == entity_id else edge.source
                        neighbor = self.kg.find_node(neighbor_id)
                        if neighbor:
                            context.append(f"{node.label} {edge.relation} {neighbor.label}")

        return context[:10]

    def _get_rag_context(self, question: str) -> List[str]:
        """获取RAG上下文

        Args:
            question: 问题

        Returns:
            上下文列表
        """
        results = self._vector_search(question, top_k=3)
        return [doc.content for doc in results]

    def _vector_search(self, query: str, top_k: int = 5) -> List[RAGDocument]:
        """向量搜索

        Args:
            query: 查询
            top_k: 返回数量

        Returns:
            文档列表
        """
        return self.rag.search(query, top_k)

    def _find_graph_paths(self, start: str, end: str, max_depth: int = 10) -> List[List[str]]:
        """
        查找图谱路径

        Args:
            start: 起始节点
            end: 结束节点
            max_depth: 最大深度

        Returns:
            路径列表
        """
        path = self.kg.find_path(start, end, max_depth)
        return [path] if path else []

    def _generate_answer(
        self,
        question: str,
        graph_context: List[str],
        rag_context: List[str]
    ) -> str:
        """生成答案

        Args:
            question: 问题
            graph_context: 图谱上下文
            rag_context: RAG上下文

        Returns:
            答案文本
        """
        parts = []

        if graph_context:
            parts.append("根据知识图谱：")
            parts.extend(graph_context[:3])

        if rag_context:
            parts.append("相关文档：")
            parts.extend(rag_context[:2])

        if not parts:
            return "抱歉，我无法找到相关信息来回答这个问题。"

        return " ".join(parts)
