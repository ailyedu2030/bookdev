"""
F11: 工作流安全 - 工作流安全管理器
P0漏洞: W-001 状态机绕过-审核节点跳过
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


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
    signature: str | None
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
    content: dict[str, Any]
    pending_tasks: list[str] = field(default_factory=list)
    approval_history: list[dict] = field(default_factory=list)


# 定义有效的状态转换
VALID_STATE_TRANSITIONS = {
    "OUTLINE_REVIEW": ["CONTENT_REVIEW", "REJECTED", "OUTLINE_REVIEW"],
    "CONTENT_REVIEW": ["FINAL_REVIEW", "REJECTED", "CONTENT_REVIEW"],
    "FINAL_REVIEW": ["APPROVED", "REJECTED", "FINAL_REVIEW"],
    "REJECTED": ["OUTLINE_REVIEW"],  # 允许重新提交
    "APPROVED": [],  # 终态，不可转换
}

# 审核节点必须按顺序完成
REVIEW_TASKS = ["task-001", "task-002", "task-003"]  # 定义审核流程中的必需任务

SIGNAL_WHITELIST = ["PauseWorkflow", "GetStatus", "CancelWorkflow"]
MAX_TIMESTAMP_AGE_MINUTES = 5
MAX_TIMESTAMP_DRIFT_MINUTES = 2  # 最大时间戳漂移（防止明显伪造）


class WorkflowSecurityManager:
    """工作流安全管理器"""

    def __init__(self, hsm_client=None, require_multi_approval: bool = False):
        self.hsm_client = hsm_client
        self.require_multi_approval = require_multi_approval
        self._workflows: dict[str, WorkflowState] = {}
        self._used_signatures: set = set()
        self._approval_counts: dict[str, int] = {}
        # F11-001 FIX: 移除硬编码Mock密钥，改用安全方式获取公钥
        self._public_key_pem = None

    def set_public_key(self, public_key_pem: str) -> None:
        """安全地设置公钥"""
        if not public_key_pem or len(public_key_pem) < 32:
            raise SecurityException("INVALID_PUBLIC_KEY", "Public key must be at least 32 characters")
        self._public_key_pem = public_key_pem

    def register_workflow(self, workflow_id: str, content: dict[str, Any]) -> None:
        """注册工作流"""
        self._workflows[workflow_id] = WorkflowState(
            workflow_id=workflow_id,
            current_state="OUTLINE_REVIEW",
            content=content,
            pending_tasks=["task-001"],  # 初始只有第一个审核任务
        )
        self._approval_counts[workflow_id] = 0

    def get_workflow_state(self, workflow_id: str) -> str:
        """获取工作流状态"""
        if workflow_id not in self._workflows:
            raise SecurityException("WORKFLOW_NOT_FOUND", f"Workflow {workflow_id} not found")
        return self._workflows[workflow_id].current_state

    def receive_signal(self, signal_type: str, direct_call: bool, workflow_id: str, task_id: str) -> VerificationResult:
        """接收Signal调用"""
        if direct_call:
            if signal_type not in SIGNAL_WHITELIST:
                raise SecurityException(
                    "DIRECT_SIGNAL_BLOCKED", f"Direct signal '{signal_type}' is blocked. Use external review service."
                )

        return VerificationResult(is_valid=True, reason="Signal allowed")

    def verify_callback(self, callback: ReviewCallback) -> VerificationResult:
        """验证审核回调"""
        if callback.signature is None:
            raise SecurityException("MISSING_SIGNATURE", "Callback must have a signature")

        if callback.workflow_id not in self._workflows:
            return VerificationResult(is_valid=False, reason="WORKFLOW_NOT_FOUND")

        # F11-004 FIX: 严格的状态转换验证
        workflow = self._workflows[callback.workflow_id]
        current_state = workflow.current_state

        # 验证任务ID是否有效（必须在pending_tasks中）
        if callback.task_id not in workflow.pending_tasks:
            return VerificationResult(is_valid=False, reason="INVALID_TASK")

        # 验证状态转换是否合法
        if callback.result == "APPROVED":
            valid_next_states = VALID_STATE_TRANSITIONS.get(current_state, [])
            if "APPROVED" not in valid_next_states and current_state != "APPROVED":
                return VerificationResult(is_valid=False, reason="INVALID_STATE_TRANSITION")

        signature_payload = self._build_signature_payload(callback)

        # F11-003 FIX: 无HSM时不能使用SHA256替代签名验证（不安全回退）
        # 如果没有HSM客户端，必须拒绝签名验证请求
        if not self.hsm_client:
            return VerificationResult(is_valid=False, reason="NO_HSM_AVAILABLE", hsm_verified=False)

        if not self._verify_signature(callback, callback.signature, signature_payload):
            return VerificationResult(is_valid=False, reason="INVALID_SIGNATURE")

        stored_content = self._workflows[callback.workflow_id].content
        stored_hash = self.calculate_content_hash(stored_content)
        if stored_hash != callback.content_hash:
            return VerificationResult(is_valid=False, reason="HASH_MISMATCH")

        # F11-005 FIX: 添加时间戳漂移检测
        if not self._verify_timestamp(callback.timestamp, allow_drift=False):
            return VerificationResult(is_valid=False, reason="TIMESTAMP_TOO_OLD")

        # 检查时间戳是否明显伪造（未来时间或太旧）
        now = datetime.utcnow()
        if callback.timestamp > now + timedelta(minutes=MAX_TIMESTAMP_DRIFT_MINUTES):
            return VerificationResult(is_valid=False, reason="TIMESTAMP_FUTURE_INVALID")

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
            multi_approval_complete=multi_approval_complete,
        )

    def _build_signature_payload(self, callback: ReviewCallback) -> str:
        """构建签名字符串"""
        return f"{callback.workflow_id}|{callback.task_id}|{callback.content_hash}|{callback.reviewer_id}|{callback.timestamp.isoformat()}"

    def _verify_signature(self, callback: ReviewCallback, signature: str, payload: str) -> bool:
        """验证签名"""
        if self.hsm_client:
            return self.hsm_client.verify(payload, signature)

        # F11-003 FIX: 不再提供不安全的回退选项 - 如果没有HSM必须拒绝
        return False

    def _generate_signature(
        self, workflow_id: str, task_id: str, content_hash: str, reviewer_id: str, timestamp: datetime
    ) -> str:
        """生成签名"""
        payload = f"{workflow_id}|{task_id}|{content_hash}|{reviewer_id}|{timestamp.isoformat()}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def _verify_timestamp(self, timestamp: datetime, allow_drift: bool = True) -> bool:
        """验证时间戳"""
        now = datetime.utcnow()
        diff = abs((now - timestamp).total_seconds())

        # 基本时间戳年龄检查
        if diff > (MAX_TIMESTAMP_AGE_MINUTES * 60):
            return False

        # F11-005 FIX: 时间戳漂移检测（可选）
        if not allow_drift:
            if diff > (MAX_TIMESTAMP_DRIFT_MINUTES * 60):
                # 时间戳差异超过允许的漂移，可能是明显伪造
                return False

        return True

    def calculate_content_hash(self, content: dict[str, Any]) -> str:
        """计算内容哈希"""
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _advance_workflow_state(self, workflow_id: str, new_state: str) -> None:
        """推进工作流状态"""
        if workflow_id in self._workflows:
            current = self._workflows[workflow_id].current_state
            valid_next = VALID_STATE_TRANSITIONS.get(current, [])

            # 严格验证状态转换
            if new_state in valid_next or current == new_state:
                self._workflows[workflow_id].current_state = new_state

                # 如果进入下一个审核阶段，添加相应的pending task
                self._update_pending_tasks(workflow_id, new_state)
            else:
                raise SecurityException("INVALID_STATE_TRANSITION", f"Cannot transition from {current} to {new_state}")

    def _update_pending_tasks(self, workflow_id: str, new_state: str) -> None:
        """更新待处理任务列表"""
        state_to_task = {
            "OUTLINE_REVIEW": "task-001",
            "CONTENT_REVIEW": "task-002",
            "FINAL_REVIEW": "task-003",
        }

        if new_state in state_to_task:
            required_task = state_to_task[new_state]
            workflow = self._workflows[workflow_id]

            # 如果pending_tasks中没有当前审核任务但需要进入下一阶段，则添加
            if required_task not in workflow.pending_tasks:
                # 只允许添加当前阶段之后的任务，不允许跳过
                workflow.pending_tasks.append(required_task)

    def _record_approval(self, workflow_id: str, callback: ReviewCallback) -> None:
        """记录审批历史"""
        if workflow_id in self._workflows:
            self._workflows[workflow_id].approval_history.append(
                {
                    "reviewer_id": callback.reviewer_id,
                    "result": callback.result,
                    "timestamp": callback.timestamp.isoformat(),
                }
            )

    def advance_workflow_state(self, callback: ReviewCallback, new_state: str) -> None:
        """推进工作流状态并记录审批"""
        self._advance_workflow_state(callback.workflow_id, new_state)
        self._record_approval(callback.workflow_id, callback)
