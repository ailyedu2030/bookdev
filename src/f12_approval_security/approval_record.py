"""
F12: 审批记录数据结构
"""

import os
import uuid
from dataclasses import dataclass
from datetime import datetime


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
               result: str, comments: str, reviewer_ip: str = None) -> "ApprovalRecord":
        """创建审批记录

        Args:
            content_id: 内容ID
            content_hash: 内容哈希 (SHA256)
            reviewer_id: 审核者ID
            result: 审批结果
            comments: 审批评论
            reviewer_ip: 审核者IP地址（可选），如果未提供则从环境变量获取
        """
        # F12-001/F12-002 FIX: 从环境变量或安全源获取真实IP地址
        safe_ip = reviewer_ip or cls._get_safe_ip()
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
            reviewer_ip=safe_ip
        )

    @staticmethod
    def _get_safe_ip() -> str:
        """安全地获取IP地址"""
        # 从环境变量获取（如果有）
        ip = os.environ.get("REVIEWER_IP")
        if ip:
            return ip
        # 如果无法获取，返回UNKNOWN而不是硬编码127.0.0.1
        return "UNKNOWN"

    def __setattr__(self, name, value):
        """实现不可变性"""
        if name in ["result", "content_hash", "signature"]:
            if hasattr(self, name) and getattr(self, name):
                raise AttributeError(f"Field '{name}' is immutable after creation")
        super().__setattr__(name, value)
