"""Pipeline 专用异常层次结构。"""

from typing import Any


class PipelineError(Exception):
    """流水线基础异常。"""

    def __init__(self, message: str, stage: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.stage = stage
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": type(self).__name__,
            "message": str(self),
            "stage": self.stage,
            "details": self.details,
        }


class StageExecutionError(PipelineError):
    """阶段执行失败异常。"""

    def __init__(
        self,
        message: str,
        stage: str | None = None,
        component: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, stage, details)
        self.component = component

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["component"] = self.component
        return result


class SecurityViolationError(PipelineError):
    """安全违规异常 — 触发流水线紧急中止。"""

    def __init__(
        self,
        message: str,
        rule_id: str = "UNKNOWN",
        severity: str = "CRITICAL",
        stage: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, stage, details)
        self.rule_id = rule_id
        self.severity = severity

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["rule_id"] = self.rule_id
        result["severity"] = self.severity
        return result


class BudgetExceededError(PipelineError):
    """上下文预算超限异常 — 触发 RAG 降级或预算重新分配。"""

    def __init__(
        self,
        message: str,
        current_usage: int = 0,
        budget_limit: int = 0,
        stage: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, stage, details)
        self.current_usage = current_usage
        self.budget_limit = budget_limit

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["current_usage"] = self.current_usage
        result["budget_limit"] = self.budget_limit
        return result


class CheckpointError(PipelineError):
    """断点/恢复异常。"""

    def __init__(
        self,
        message: str,
        checkpoint_id: str = "UNKNOWN",
        stage: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, stage, details)
        self.checkpoint_id = checkpoint_id

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["checkpoint_id"] = self.checkpoint_id
        return result


class PipelineAbortedError(PipelineError):
    """流水线主动中止异常 (非错误中止)。"""

    def __init__(
        self,
        message: str,
        reason: str = "UNKNOWN",
        stage: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, stage, details)
        self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["abort_reason"] = self.reason
        return result
