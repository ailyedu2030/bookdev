"""
F22: 素材数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class Material:
    """素材数据类"""
    id: str
    content: str
    chapter_id: str
    token_count: int = 0
    embedding: Any = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.token_count == 0:
            self.token_count = self._estimate_tokens()

    def _estimate_tokens(self) -> int:
        """估算token数量"""
        return len(self.content)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "chapter_id": self.chapter_id,
            "token_count": self.token_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Material":
        """从字典创建"""
        return cls(
            id=data["id"],
            content=data["content"],
            chapter_id=data.get("chapter_id", ""),
            token_count=data.get("token_count", 0),
            metadata=data.get("metadata", {}),
        )
