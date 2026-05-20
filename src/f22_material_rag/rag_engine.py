"""
F22: 素材RAG召回引擎

基于知识图谱和上下文预算管理器的检索增强生成召回系统
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np

from f22_material_rag.material import Material
from f22_material_rag.embedding_client import MiniMaxEmbeddingClient
from f22_material_rag.vector_store import InMemoryVectorStore


@dataclass
class RetrievedMaterial:
    """检索到的素材"""
    material_id: str
    content: str
    score: float
    token_count: int
    source_chapter_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MaterialRAGEngine:
    """素材检索增强生成召回系统"""

    DEFAULT_EMBEDDING_DIM = 1024
    DEFAULT_TOP_K = 10
    DEFAULT_MAX_TOKENS = 8000

    def __init__(
        self,
        knowledge_graph,
        context_budget,
        embedding_model: MiniMaxEmbeddingClient = None,
        embedding_dim: int = None,
    ):
        self.kg = knowledge_graph
        self.budget = context_budget
        self.embedding_dim = embedding_dim or self.DEFAULT_EMBEDDING_DIM
        self.embedding_model = embedding_model or MiniMaxEmbeddingClient(
            api_key="mock-key",
            dimension=self.embedding_dim
        )
        self.vector_store = InMemoryVectorStore(dimension=self.embedding_dim)
        self._materials: Dict[str, Material] = {}
        self._embeddings: Dict[str, np.ndarray] = {}

    def add_material(self, material_data: dict) -> None:
        """
        添加素材到向量存储

        Args:
            material_data: {
                "id": str,
                "content": str,
                "chapter_id": str,
                "metadata": dict
            }
        """
        material = Material(
            id=material_data["id"],
            content=material_data["content"],
            chapter_id=material_data.get("chapter_id", ""),
            metadata=material_data.get("metadata", {}),
        )

        self._materials[material.id] = material

        embedding = self.embedding_model.generate_embedding(material.content)
        self._embeddings[material.id] = embedding
        self.vector_store.add(
            material.id,
            embedding,
            metadata={
                "content": material.content,
                "chapter_id": material.chapter_id,
                "token_count": material.token_count,
                "metadata": material.metadata,
            }
        )

    def retrieve_relevant_materials(
        self,
        query: str,
        top_k: int = None,
        max_tokens: int = None,
        use_kg_enhancement: bool = False,
        deduplicate: bool = True,
        similarity_threshold: float = 0.9,
    ) -> List[RetrievedMaterial]:
        """
        检索相关素材

        Args:
            query: 查询文本
            top_k: 返回数量上限
            max_tokens: token数量上限
            use_kg_enhancement: 是否使用知识图谱增强
            deduplicate: 是否去重
            similarity_threshold: 相似度阈值

        Returns:
            检索到的素材列表
        """
        if not query or not query.strip():
            return []

        top_k = top_k or self.DEFAULT_TOP_K
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS

        query_embedding = self.embedding_model.generate_embedding(query)

        search_results = self.vector_store.search(query_embedding, top_k=top_k * 2)

        if use_kg_enhancement:
            search_results = self._kg_enhance_results(search_results, query)

        if deduplicate:
            search_results = self._deduplicate_results(
                search_results, similarity_threshold
            )

        retrieved = []
        total_tokens = 0

        for result in search_results:
            if len(retrieved) >= top_k:
                break

            metadata = result.get("metadata", {})
            token_count = metadata.get("token_count", 0)

            if total_tokens + token_count > max_tokens:
                continue

            retrieved.append(RetrievedMaterial(
                material_id=result["id"],
                content=metadata.get("content", ""),
                score=result["score"],
                token_count=token_count,
                source_chapter_id=metadata.get("chapter_id"),
                metadata=metadata.get("metadata", {}),
            ))
            total_tokens += token_count

        return retrieved

    def build_context_from_materials(
        self,
        materials: List[RetrievedMaterial],
        max_tokens: int = None,
    ) -> str:
        """
        从素材构建上下文（预算感知）

        Args:
            materials: 检索到的素材
            max_tokens: 最大token数

        Returns:
            构建的上下文字符串
        """
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS

        context_parts = []
        total_tokens = 0

        for material in materials:
            material_tokens = material.token_count
            if total_tokens + material_tokens > max_tokens:
                remaining_tokens = max_tokens - total_tokens
                if remaining_tokens > 50:
                    truncated_content = material.content[:remaining_tokens]
                    context_parts.append(truncated_content)
                break

            context_parts.append(material.content)
            total_tokens += material_tokens

        return "\n\n".join(context_parts)

    def get_material_count(self) -> int:
        """获取素材数量"""
        return len(self._materials)

    def get_embedding(self, material_id: str) -> Optional[np.ndarray]:
        """获取素材嵌入"""
        return self._embeddings.get(material_id)

    def estimate_tokens(self, text: str) -> int:
        """估算token数量"""
        return len(text)

    def _kg_enhance_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
    ) -> List[Dict[str, Any]]:
        """知识图谱增强检索结果"""
        if not self.kg:
            return results

        query_embedding = self.embedding_model.generate_embedding(query)
        query_terms = set(query.lower().split())

        enhanced_results = []
        for result in results:
            metadata = result.get("metadata", {})
            chapter_id = metadata.get("chapter_id")

            boost = 1.0

            if chapter_id:
                related_nodes = self.kg.get_edges(node_id=chapter_id)
                for edge in related_nodes:
                    if edge.edge_type == "SIMILAR_TO":
                        score = edge.properties.get("similarity_score", 0)
                        boost += score * 0.2
                    elif edge.edge_type == "FOLLOWS":
                        boost += 0.1

                concept_edges = self.kg.get_edges(node_id=chapter_id, edge_type="DEFINES")
                for edge in concept_edges:
                    target_node = self.kg.get_node(edge.target)
                    if target_node and hasattr(target_node, "name"):
                        node_terms = set(target_node.name.lower().split())
                        if query_terms & node_terms:
                            boost += 0.15

            boosted_score = result["score"] * boost
            enhanced_results.append({
                **result,
                "score": min(boosted_score, 1.0)
            })

        enhanced_results.sort(key=lambda x: x["score"], reverse=True)
        return enhanced_results

    def _deduplicate_results(
        self,
        results: List[Dict[str, Any]],
        threshold: float = 0.9,
    ) -> List[Dict[str, Any]]:
        """去重相似结果"""
        if not results:
            return results

        deduplicated = []
        seen_contents = []

        for result in results:
            metadata = result.get("metadata", {})
            content = metadata.get("content", "").lower().strip()

            is_duplicate = False
            for seen in seen_contents:
                similarity = self._compute_similarity(content, seen)
                if similarity >= threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduplicated.append(result)
                seen_contents.append(content)

        return deduplicated

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        if not text1 or not text2:
            return 0.0

        emb1 = self.embedding_model.generate_embedding(text1)
        emb2 = self.embedding_model.generate_embedding(text2)

        return self.embedding_model.compute_similarity(emb1, emb2)
