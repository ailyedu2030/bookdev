"""
F12: 审批结果安全 - 审批安全管理器
P0漏洞: W-002 人工介入欺骗-审批伪装
"""

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


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
               result: str, comments: str, reviewer_ip: str = None) -> "ApprovalRecord":
        """创建审批记录"""
        import uuid
        # F12-001/F12-002 FIX: 从环境变量或安全源获取真实IP地址
        safe_ip = reviewer_ip or cls._get_safe_ip()
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


MAX_TIMESTAMP_AGE_MINUTES = 5
MAX_TIMESTAMP_DRIFT_MINUTES = 2


class ApprovalSecurityManager:
    """审批结果安全管理器"""

    def __init__(self, hsm_client=None, require_multi_approval: bool = False):
        self.hsm_client = hsm_client
        self.require_multi_approval = require_multi_approval
        self._records: dict[str, ApprovalRecord] = {}
        self._used_signatures: set = set()
        self._audit_trail: dict[str, list[dict]] = {}
        self._approval_requirements: dict[str, int] = {}  # content_id -> required_approval_count

    def calculate_content_hash(self, content: dict[str, Any]) -> str:
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
        signature: str | None = None,
        is_high_risk: bool = False,
        reviewer_ip: str = None
    ) -> ApprovalRecord:
        """提交审批"""
        if signature is None:
            raise SecurityException("MISSING_SIGNATURE", "Approval must have a signature")

        # F12-005 FIX: 强制验证content_hash存在且有效
        if not content_hash or len(content_hash) != 64:
            raise SecurityException("INVALID_CONTENT_HASH", "Content hash must be a valid SHA256 hash")

        # F12-003 FIX: 如果无HSM，拒绝所有审批（移除不安全回退）
        if not self.hsm_client:
            raise SecurityException("HSM_REQUIRED", "Cannot submit approval without HSM - this is a security requirement")

        safe_ip = reviewer_ip or os.environ.get("REVIEWER_IP", "UNKNOWN")

        record = ApprovalRecord(
            record_id=self._generate_record_id(),
            content_id=content_id,
            content_hash=content_hash,
            reviewer_id=reviewer_id,
            result=result,
            comments=comments,
            signature=signature,
            signature_source="HSM",
            timestamp=datetime.utcnow(),
            reviewer_ip=safe_ip,
            is_high_risk=is_high_risk
        )

        # F12-004 FIX: 实现真正的多重审批验证
        if is_high_risk and self.require_multi_approval:
            # 检查是否已有足够的审批
            current_count = self._get_approval_count(content_id)
            required_count = self._get_required_approval_count(is_high_risk)

            if current_count >= required_count:
                raise SecurityException(
                    "MULTI_APPROVAL_COMPLETE",
                    f"Content {content_id} already has {current_count} approvals, maximum is {required_count}"
                )

            self._approval_requirements[content_id] = required_count

        self._records[content_id] = record
        self._add_audit_entry(content_id, record)

        return record

    def _get_approval_count(self, content_id: str) -> int:
        """获取内容已完成的审批数量"""
        return sum(1 for r in self._records.values() if r.content_id == content_id)

    def _get_required_approval_count(self, is_high_risk: bool) -> int:
        """获取所需审批数量"""
        return 3 if is_high_risk else 1

    def verify_record(self, record: ApprovalRecord) -> VerificationResult:
        """验证审批记录"""
        # F12-003 FIX: 必须有HSM才能验证
        if not self.hsm_client:
            return VerificationResult(is_valid=False, reason="NO_HSM_AVAILABLE")

        # F12-001/F12-002 FIX: 验证IP不是UNKNOWN或硬编码值
        if record.reviewer_ip in ("UNKNOWN", "127.0.0.1", ""):
            return VerificationResult(is_valid=False, reason="INVALID_REVIEWER_IP")

        if record.signature_source != "HSM" and self.hsm_client:
            return VerificationResult(is_valid=False, reason="HSM_REQUIRED")

        if record.signature in self._used_signatures:
            return VerificationResult(is_valid=False, reason="REPLAY_DETECTED")

        # F12-005 FIX: 验证content_hash
        if record.content_id in self._records:
            stored_record = self._records[record.content_id]
            if stored_record.content_hash != record.content_hash:
                return VerificationResult(is_valid=False, reason="CONTENT_HASH_MISMATCH")

        # F12-004 FIX: 多重审批验证
        if record.is_high_risk and self.require_multi_approval:
            required_count = self._approval_requirements.get(record.content_id, 3)
            current_count = self._get_approval_count(record.content_id)

            if current_count < required_count:
                return VerificationResult(
                    is_valid=False,
                    reason=f"MULTI_APPROVAL_INCOMPLETE: need {required_count}, have {current_count}"
                )

        if not self._verify_signature(record):
            return VerificationResult(is_valid=False, reason="INVALID_SIGNATURE")

        if not self._verify_timestamp(record.timestamp):
            return VerificationResult(is_valid=False, reason="TIMESTAMP_TOO_OLD")

        # 检查时间戳是否明显伪造
        now = datetime.utcnow()
        if record.timestamp > now + timedelta(minutes=MAX_TIMESTAMP_DRIFT_MINUTES):
            return VerificationResult(is_valid=False, reason="TIMESTAMP_FUTURE_INVALID")

        self._used_signatures.add(record.signature)

        return VerificationResult(is_valid=True, hsm_verified=True)

    def get_record(self, content_id: str) -> ApprovalRecord:
        """获取审批记录"""
        if content_id not in self._records:
            raise ValueError(f"No record found for content_id: {content_id}")
        return self._records[content_id]

    def get_audit_trail(self, content_id: str) -> list[dict]:
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
        # F12-003 FIX: 移除不安全的回退
        return False

    def _verify_timestamp(self, timestamp: datetime) -> bool:
        """验证时间戳"""
        now = datetime.utcnow()
        diff = abs((now - timestamp).total_seconds())
        if diff > (MAX_TIMESTAMP_AGE_MINUTES * 60):
            return False
        if diff > (MAX_TIMESTAMP_DRIFT_MINUTES * 60):
            # 时间戳漂移超过限制，可能是明显伪造
            return False
        return True

    def _add_audit_entry(self, content_id: str, record: ApprovalRecord) -> None:
        """添加审计条目"""
        if content_id not in self._audit_trail:
            self._audit_trail[content_id] = []

        self._audit_trail[content_id].append({
            "record_id": record.record_id,
            "reviewer_id": record.reviewer_id,
            "result": record.result,
            "timestamp": record.timestamp.isoformat(),
            "reviewer_ip": record.reviewer_ip,
            "action": "APPROVAL_SUBMITTED"
        })
