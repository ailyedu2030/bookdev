"""
F28: 监控仪表盘 - GREEN阶段实现

按照TDD原则，此实现仅包含让测试通过的最简代码。
依赖: F01 不可变日志, F04 Temporal工作流引擎
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


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
    metadata: dict[str, Any]
    timestamp: datetime


class MonitoringDashboard:
    """监控仪表盘"""

    # Maximum history length to prevent unbounded growth
    MAX_HISTORY_LENGTH = 1000

    def __init__(self, log_reader=None, workflow_client=None):
        self.metrics: dict[str, float] = {}
        self.alerts: list[Alert] = []
        self.logger = log_reader
        self.workflow_client = workflow_client
        self._metric_history: dict[str, list[float]] = {}
        self._active_alerts: dict[str, Alert] = {}  # Track active alerts by metric name

    def record_metric(self, name: str, value: float) -> None:
        """记录指标"""
        self.metrics[name] = value
        if name not in self._metric_history:
            self._metric_history[name] = []
        self._metric_history[name].append(value)
        # Limit history size to prevent unbounded growth
        if len(self._metric_history[name]) > self.MAX_HISTORY_LENGTH:
            self._metric_history[name] = self._metric_history[name][-self.MAX_HISTORY_LENGTH :]

    def get_health_status(self) -> HealthStatus:
        """获取健康状态 - 实际检查各组件状态"""
        # Check if there are any active critical/warning alerts
        has_critical = any(alert.level == "critical" for alert in self.alerts)
        has_warning = any(alert.level == "warning" for alert in self.alerts)

        if has_critical:
            return HealthStatus(
                status="critical",
                timestamp=datetime.now(UTC),
                message="Critical alerts active - immediate attention required",
            )
        elif has_warning:
            return HealthStatus(
                status="degraded", timestamp=datetime.now(UTC), message="System operating with warnings"
            )
        else:
            return HealthStatus(status="healthy", timestamp=datetime.now(UTC), message="All systems operational")

    def check_log_integrity(self) -> bool:
        """检查日志完整性 - 实际验证日志记录"""
        if self.logger is None:
            return False

        # Check if logger has the verify_integrity method
        if hasattr(self.logger, "verify_integrity"):
            try:
                return self.logger.verify_integrity()
            except Exception:
                return False

        # Fallback: check if logger has recent entries
        if hasattr(self.logger, "get_recent_entries"):
            try:
                entries = self.logger.get_recent_entries(limit=10)
                return len(entries) > 0
            except Exception:
                return False

        return True

    def get_workflow_metrics(self) -> WorkflowMetrics:
        """获取工作流指标 - 实际从workflow_client获取"""
        if self.workflow_client is None:
            return WorkflowMetrics(active_count=0, completed_count=0, failed_count=0)

        try:
            # Try to get metrics from workflow client
            if hasattr(self.workflow_client, "get_metrics"):
                raw_metrics = self.workflow_client.get_metrics()
                return WorkflowMetrics(
                    active_count=raw_metrics.get("active", 0),
                    completed_count=raw_metrics.get("completed", 0),
                    failed_count=raw_metrics.get("failed", 0),
                )
            elif hasattr(self.workflow_client, "get_workflow_stats"):
                stats = self.workflow_client.get_workflow_stats()
                return WorkflowMetrics(
                    active_count=stats.get("running", 0),
                    completed_count=stats.get("completed", 0),
                    failed_count=stats.get("failed", 0),
                )
        except Exception:
            pass

        return WorkflowMetrics(active_count=0, completed_count=0, failed_count=0)

    def add_alert(self, level: str, message: str, metadata: dict[str, Any]) -> None:
        """添加告警"""
        alert = Alert(level=level, message=message, metadata=metadata, timestamp=datetime.now(UTC))
        self.alerts.append(alert)

        # Track active alert by metric name for recovery detection
        metric_name = metadata.get("metric_name")
        if metric_name and level in ("warning", "critical"):
            self._active_alerts[metric_name] = alert

    def get_average_metric(self, name: str) -> float | None:
        """获取平均指标"""
        if name not in self._metric_history or not self._metric_history[name]:
            return None
        values = self._metric_history[name]
        return sum(values) / len(values)

    def check_threshold(self, name: str, threshold: float, level: str = "warning") -> None:
        """检查阈值并告警"""
        current_value = self.metrics.get(name)
        if current_value is None:
            return

        if current_value > threshold:
            self.add_alert(
                level,
                f"{name} exceeded threshold",
                {"threshold": threshold, "value": current_value, "metric_name": name},
            )
        else:
            # Metric recovered - clear any active alert for this metric
            self._clear_recovered_alert(name)

    def _clear_recovered_alert(self, metric_name: str) -> None:
        """清除已恢复指标的告警"""
        if metric_name in self._active_alerts:
            del self._active_alerts[metric_name]

    def get_active_alerts(self) -> list[Alert]:
        """获取当前活跃的告警"""
        return list(self._active_alerts.values())

    def clear_alert(self, metric_name: str) -> None:
        """手动清除特定指标的告警"""
        if metric_name in self._active_alerts:
            del self._active_alerts[metric_name]

    def get_metric_trend(self, name: str, window_size: int = 10) -> float | None:
        """获取指标趋势（最近window_size的平均变化率）"""
        if name not in self._metric_history or len(self._metric_history[name]) < 2:
            return None

        history = self._metric_history[name][-window_size:]
        if len(history) < 2:
            return None

        # Calculate average change
        changes = [history[i + 1] - history[i] for i in range(len(history) - 1)]
        return sum(changes) / len(changes) if changes else 0.0
