"""
F22: MiniMax嵌入客户端

提供文本嵌入功能，支持单条和批量生成
"""


import numpy as np


class MiniMaxEmbeddingClient:
    """MiniMax嵌入客户端"""

    DEFAULT_DIMENSION = 1024

    def __init__(self, api_key: str, dimension: int = None):
        self.api_key = api_key
        self.dimension = dimension or self.DEFAULT_DIMENSION

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        生成单条文本的嵌入向量

        Args:
            text: 待嵌入文本

        Returns:
            嵌入向量 (numpy array)

        Raises:
            ValueError: 如果文本为空或仅包含空白字符
        """
        if not text or not text.strip():
            # KG-004: Raise exception instead of returning zero vector
            raise ValueError("Text cannot be empty or whitespace only when generating embedding")

        embedding = self._compute_embedding(text)
        return embedding

    def batch_generate_embedding(self, texts: list[str]) -> list[np.ndarray]:
        """
        批量生成嵌入向量

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表

        Raises:
            ValueError: 如果任何文本为空或仅包含空白字符
        """
        return [self.generate_embedding(text) for text in texts]

    def _compute_embedding(self, text: str) -> np.ndarray:
        """
        计算文本嵌入（简化实现）

        实际应调用MiniMax API:
        POST https://api.minimaxi.com/v1/embeddings
        """
        text_hash = hash(text)
        np.random.seed(text_hash % (2**32))
        embedding = np.random.randn(self.dimension)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding

    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        计算两个嵌入向量的余弦相似度

        Args:
            embedding1: 嵌入向量1
            embedding2: 嵌入向量2

        Returns:
            相似度分数 [0, 1]
        """
        dot_product = np.dot(embedding1, embedding2)
        return max(0.0, min(1.0, (dot_product + 1.0) / 2.0))
