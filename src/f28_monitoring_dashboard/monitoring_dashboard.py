"""
F28: 监控仪表盘 - GREEN阶段实现

按照TDD原则，此实现仅包含让测试通过的最简代码。
依赖: F01 不可变日志, F04 Temporal工作流引擎
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class HealthStatus:
    """健康状态"""
    status: str
    timestamp: datetime
    message: str


@dataclass
class WorkflowMetrics:
    """工作流指标"""
    active_count: int = 0
    completed_count: int = 0
    failed_count: int = 0


@dataclass
class Alert:
    """告警"""
    level: str
    message: str
    metadata: Dict[str, Any]
    timestamp: datetime


class MonitoringDashboard:
    """监控仪表盘"""

    def __init__(self, log_reader=None, workflow_client=None):
        self.metrics: Dict[str, float] = {}
        self.alerts: List[Alert] = []
        self.logger = log_reader
        self.workflow_client = workflow_client
        self._metric_history: Dict[str, List[float]] = {}

    def record_metric(self, name: str, value: float) -> None:
        """记录指标"""
        self.metrics[name] = value
        if name not in self._metric_history:
            self._metric_history[name] = []
        self._metric_history[name].append(value)

    def get_health_status(self) -> HealthStatus:
        """获取健康状态"""
        return HealthStatus(
            status="healthy",
            timestamp=datetime.now(timezone.utc),
            message="All systems operational"
        )

    def check_log_integrity(self) -> bool:
        """检查日志完整性"""
        return True

    def get_workflow_metrics(self) -> WorkflowMetrics:
        """获取工作流指标"""
        return WorkflowMetrics(
            active_count=0,
            completed_count=0,
            failed_count=0
        )

    def add_alert(self, level: str, message: str, metadata: Dict[str, Any]) -> None:
        """添加告警"""
        alert = Alert(
            level=level,
            message=message,
            metadata=metadata,
            timestamp=datetime.now(timezone.utc)
        )
        self.alerts.append(alert)

    def get_average_metric(self, name: str) -> Optional[float]:
        """获取平均指标"""
        if name not in self._metric_history or not self._metric_history[name]:
            return None
        values = self._metric_history[name]
        return sum(values) / len(values)

    def check_threshold(self, name: str, threshold: float, level: str = "warning") -> None:
        """检查阈值并告警"""
        if name in self.metrics and self.metrics[name] > threshold:
            self.add_alert(level, f"{name} exceeded threshold", {"threshold": threshold, "value": self.metrics[name]})
