"""
F22: 向量存储

内存向量存储实现，支持添加、搜索、删除操作
"""

from typing import List, Dict, Any
import numpy as np


class InMemoryVectorStore:
    """内存向量存储"""

    def __init__(self, dimension: int = 1024):
        self.dimension = dimension
        self._vectors: Dict[str, np.ndarray] = {}
        self._metadata: Dict[str, dict] = {}

    def add(self, id: str, vector: np.ndarray, metadata: dict = None) -> None:
        """
        添加向量到存储

        Args:
            id: 向量唯一标识
            vector: 嵌入向量
            metadata: 关联元数据
        """
        if len(vector) != self.dimension:
            raise ValueError(f"向量维度必须为{self.dimension}，实际为{len(vector)}")

        self._vectors[id] = vector
        if metadata:
            self._metadata[id] = metadata

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索最相似的向量

        Args:
            query_vector: 查询向量
            top_k: 返回数量

        Returns:
            [{id, score, metadata}, ...]
        """
        if len(query_vector) != self.dimension:
            raise ValueError(f"查询向量维度必须为{self.dimension}")

        if not self._vectors:
            return []

        similarities = []
        for vid, vector in self._vectors.items():
            similarity = self._cosine_similarity(query_vector, vector)
            similarities.append({
                "id": vid,
                "score": similarity,
                "metadata": self._metadata.get(vid, {})
            })

        similarities.sort(key=lambda x: x["score"], reverse=True)
        return similarities[:top_k]

    def delete(self, id: str) -> None:
        """删除向量"""
        if id in self._vectors:
            del self._vectors[id]
        if id in self._metadata:
            del self._metadata[id]

    def get(self, id: str) -> np.ndarray:
        """获取向量"""
        return self._vectors.get(id)

    def count(self) -> int:
        """获取向量数量"""
        return len(self._vectors)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        return max(0.0, min(1.0, (similarity + 1.0) / 2.0))
