"""
F12: 审批记录数据结构
"""

from datetime import datetime
from dataclasses import dataclass
import uuid


@dataclass
class ApprovalRecord:
    """审批记录"""
    record_id: str
    content_id: str
    content_hash: str
    reviewer_id: str
    result: str
    comments: str
    signature: str
    signature_source: str
    timestamp: datetime
    reviewer_ip: str
    is_high_risk: bool = False

    def to_signable_string(self) -> str:
        """构建待签名字符串"""
        return f"{self.content_id}|{self.content_hash}|{self.reviewer_id}|{self.result}|{self.timestamp.isoformat()}"

    @classmethod
    def create(cls, content_id: str, content_hash: str, reviewer_id: str,
               result: str, comments: str) -> "ApprovalRecord":
        """创建审批记录"""
        return cls(
            record_id=f"rec-{uuid.uuid4().hex[:12]}",
            content_id=content_id,
            content_hash=content_hash,
            reviewer_id=reviewer_id,
            result=result,
            comments=comments,
            signature="",
            signature_source="",
            timestamp=datetime.utcnow(),
            reviewer_ip="127.0.0.1"
        )

    def __setattr__(self, name, value):
        """实现不可变性"""
        if name in ["result", "content_hash", "signature"]:
            if hasattr(self, name) and getattr(self, name):
                raise AttributeError(f"Field '{name}' is immutable after creation")
        super().__setattr__(name, value)
