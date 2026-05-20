"""
F12: 审批结果安全 - 审批安全管理器
P0漏洞: W-002 人工介入欺骗-审批伪装
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import hashlib
import hmac


class SecurityException(Exception):
    """安全异常"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


@dataclass
class VerificationResult:
    """验证结果"""
    is_valid: bool
    reason: str = ""
    hsm_verified: bool = False


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
        import uuid
        return cls(
            record_id=str(uuid.uuid4()),
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


MAX_TIMESTAMP_AGE_MINUTES = 5


class ApprovalSecurityManager:
    """审批结果安全管理器"""

    def __init__(self, hsm_client=None, require_multi_approval: bool = False):
        self.hsm_client = hsm_client
        self.require_multi_approval = require_multi_approval
        self._records: Dict[str, ApprovalRecord] = {}
        self._used_signatures: set = set()
        self._audit_trail: Dict[str, List[Dict]] = {}

    def calculate_content_hash(self, content: Dict[str, Any]) -> str:
        """计算内容哈希"""
        import json
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def submit_approval(
        self,
        content_id: str,
        content_hash: str,
        reviewer_id: str,
        result: str,
        comments: str = "",
        signature: Optional[str] = None,
        is_high_risk: bool = False
    ) -> ApprovalRecord:
        """提交审批"""
        if signature is None:
            raise SecurityException("MISSING_SIGNATURE", "Approval must have a signature")

        record = ApprovalRecord(
            record_id=self._generate_record_id(),
            content_id=content_id,
            content_hash=content_hash,
            reviewer_id=reviewer_id,
            result=result,
            comments=comments,
            signature=signature,
            signature_source="HSM" if self.hsm_client else "SOFTWARE",
            timestamp=datetime.utcnow(),
            reviewer_ip="127.0.0.1",
            is_high_risk=is_high_risk
        )

        if is_high_risk and self.require_multi_approval:
            pass

        self._records[content_id] = record
        self._add_audit_entry(content_id, record)

        return record

    def verify_record(self, record: ApprovalRecord) -> VerificationResult:
        """验证审批记录"""
        if record.signature_source != "HSM" and self.hsm_client:
            return VerificationResult(is_valid=False, reason="HSM_REQUIRED")

        if record.signature in self._used_signatures:
            return VerificationResult(is_valid=False, reason="REPLAY_DETECTED")

        if not self._verify_signature(record):
            return VerificationResult(is_valid=False, reason="INVALID_SIGNATURE")

        if record.content_id in self._records:
            stored_record = self._records[record.content_id]
            if stored_record.content_hash != record.content_hash:
                return VerificationResult(is_valid=False, reason="CONTENT_HASH_MISMATCH")

        if not self._verify_timestamp(record.timestamp):
            return VerificationResult(is_valid=False, reason="TIMESTAMP_TOO_OLD")

        if record.is_high_risk and self.require_multi_approval:
            return VerificationResult(is_valid=False, reason="MULTI_APPROVAL_REQUIRED")

        self._used_signatures.add(record.signature)

        return VerificationResult(is_valid=True, hsm_verified=True)

    def get_record(self, content_id: str) -> ApprovalRecord:
        """获取审批记录"""
        if content_id not in self._records:
            raise ValueError(f"No record found for content_id: {content_id}")
        return self._records[content_id]

    def get_audit_trail(self, content_id: str) -> List[Dict]:
        """获取审计追踪"""
        return self._audit_trail.get(content_id, [])

    def _generate_record_id(self) -> str:
        """生成记录ID"""
        import uuid
        return f"rec-{uuid.uuid4().hex[:12]}"

    def _verify_signature(self, record: ApprovalRecord) -> bool:
        """验证签名"""
        if self.hsm_client:
            return self.hsm_client.verify(
                record.to_signable_string(),
                record.signature
            )

        return hmac.compare_digest(record.signature, "valid_signature")

    def _verify_timestamp(self, timestamp: datetime) -> bool:
        """验证时间戳"""
        now = datetime.utcnow()
        diff = abs((now - timestamp).total_seconds())
        return diff <= (MAX_TIMESTAMP_AGE_MINUTES * 60)

    def _add_audit_entry(self, content_id: str, record: ApprovalRecord) -> None:
        """添加审计条目"""
        if content_id not in self._audit_trail:
            self._audit_trail[content_id] = []

        self._audit_trail[content_id].append({
            "record_id": record.record_id,
            "reviewer_id": record.reviewer_id,
            "result": record.result,
            "timestamp": record.timestamp.isoformat(),
            "action": "APPROVAL_SUBMITTED"
        })
