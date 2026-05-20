"""
F11: 工作流安全 - 工作流安全管理器
P0漏洞: W-001 状态机绕过-审核节点跳过
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import hashlib
import hmac
import json


class SecurityException(Exception):
    """安全异常"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


@dataclass
class ReviewCallback:
    """审核回调数据结构"""
    workflow_id: str
    task_id: str
    content_hash: str
    reviewer_id: str
    result: str
    signature: Optional[str]
    timestamp: datetime


@dataclass
class VerificationResult:
    """验证结果"""
    is_valid: bool
    reason: str = ""
    hsm_verified: bool = False
    approval_count: int = 0
    multi_approval_complete: bool = False


@dataclass
class WorkflowState:
    """工作流状态"""
    workflow_id: str
    current_state: str
    content: Dict[str, Any]
    pending_tasks: List[str] = field(default_factory=list)
    approval_history: List[Dict] = field(default_factory=list)


SIGNAL_WHITELIST = ["PauseWorkflow", "GetStatus", "CancelWorkflow"]
MAX_TIMESTAMP_AGE_MINUTES = 5


class WorkflowSecurityManager:
    """工作流安全管理器"""

    def __init__(self, hsm_client=None, require_multi_approval: bool = False):
        self.hsm_client = hsm_client
        self.require_multi_approval = require_multi_approval
        self._workflows: Dict[str, WorkflowState] = {}
        self._used_signatures: set = set()
        self._approval_counts: Dict[str, int] = {}
        self._hsm_public_key = "mock_public_key_for_testing"

    def register_workflow(self, workflow_id: str, content: Dict[str, Any]) -> None:
        """注册工作流"""
        self._workflows[workflow_id] = WorkflowState(
            workflow_id=workflow_id,
            current_state="OUTLINE_REVIEW",
            content=content,
            pending_tasks=["task-001"]
        )
        self._approval_counts[workflow_id] = 0

    def get_workflow_state(self, workflow_id: str) -> str:
        """获取工作流状态"""
        if workflow_id not in self._workflows:
            raise SecurityException("WORKFLOW_NOT_FOUND", f"Workflow {workflow_id} not found")
        return self._workflows[workflow_id].current_state

    def receive_signal(
        self,
        signal_type: str,
        direct_call: bool,
        workflow_id: str,
        task_id: str
    ) -> VerificationResult:
        """接收Signal调用"""
        if direct_call:
            if signal_type not in SIGNAL_WHITELIST:
                raise SecurityException(
                    "DIRECT_SIGNAL_BLOCKED",
                    f"Direct signal '{signal_type}' is blocked. Use external review service."
                )

        return VerificationResult(is_valid=True, reason="Signal allowed")

    def verify_callback(self, callback: ReviewCallback) -> VerificationResult:
        """验证审核回调"""
        if callback.signature is None:
            raise SecurityException("MISSING_SIGNATURE", "Callback must have a signature")

        if callback.workflow_id not in self._workflows:
            return VerificationResult(is_valid=False, reason="WORKFLOW_NOT_FOUND")

        signature_payload = self._build_signature_payload(callback)
        if not self._verify_signature(callback, callback.signature, signature_payload):
            return VerificationResult(is_valid=False, reason="INVALID_SIGNATURE")

        stored_content = self._workflows[callback.workflow_id].content
        stored_hash = self.calculate_content_hash(stored_content)
        if stored_hash != callback.content_hash:
            return VerificationResult(is_valid=False, reason="HASH_MISMATCH")

        if not self._verify_timestamp(callback.timestamp):
            return VerificationResult(is_valid=False, reason="TIMESTAMP_TOO_OLD")

        if callback.signature in self._used_signatures:
            return VerificationResult(is_valid=False, reason="REPLAY_DETECTED")
        self._used_signatures.add(callback.signature)

        self._approval_counts[callback.workflow_id] += 1
        approval_count = self._approval_counts[callback.workflow_id]

        hsm_verified = False
        if self.hsm_client:
            hsm_verified = self.hsm_client.verify(signature_payload, callback.signature)

        multi_approval_complete = False
        if self.require_multi_approval and approval_count >= 2:
            multi_approval_complete = True

        return VerificationResult(
            is_valid=True,
            hsm_verified=hsm_verified,
            approval_count=approval_count,
            multi_approval_complete=multi_approval_complete
        )

    def _build_signature_payload(self, callback: ReviewCallback) -> str:
        """构建签名字符串"""
        return f"{callback.workflow_id}|{callback.task_id}|{callback.content_hash}|{callback.reviewer_id}|{callback.timestamp.isoformat()}"

    def _verify_signature(self, callback: ReviewCallback, signature: str, payload: str) -> bool:
        """验证签名"""
        if self.hsm_client:
            return self.hsm_client.verify(payload, signature)

        expected = self._generate_signature(
            callback.workflow_id,
            callback.task_id,
            callback.content_hash,
            callback.reviewer_id,
            callback.timestamp
        )
        return hmac.compare_digest(signature, expected)

    def _generate_signature(
        self,
        workflow_id: str,
        task_id: str,
        content_hash: str,
        reviewer_id: str,
        timestamp: datetime
    ) -> str:
        """生成签名"""
        payload = f"{workflow_id}|{task_id}|{content_hash}|{reviewer_id}|{timestamp.isoformat()}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def _verify_timestamp(self, timestamp: datetime) -> bool:
        """验证时间戳"""
        now = datetime.utcnow()
        diff = abs((now - timestamp).total_seconds())
        return diff <= (MAX_TIMESTAMP_AGE_MINUTES * 60)

    def calculate_content_hash(self, content: Dict[str, Any]) -> str:
        """计算内容哈希"""
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _advance_workflow_state(self, workflow_id: str, new_state: str) -> None:
        """推进工作流状态"""
        if workflow_id in self._workflows:
            self._workflows[workflow_id].current_state = new_state

    def _record_approval(self, workflow_id: str, callback: ReviewCallback) -> None:
        """记录审批历史"""
        if workflow_id in self._workflows:
            self._workflows[workflow_id].approval_history.append({
                "reviewer_id": callback.reviewer_id,
                "result": callback.result,
                "timestamp": callback.timestamp.isoformat()
            })

    def advance_workflow_state(self, callback: ReviewCallback, new_state: str) -> None:
        """推进工作流状态并记录审批"""
        self._advance_workflow_state(callback.workflow_id, new_state)
        self._record_approval(callback.workflow_id, callback)
