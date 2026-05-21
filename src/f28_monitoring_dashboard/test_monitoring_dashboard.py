"""
F28: 监控仪表盘 - 测试文件

TDD RED阶段：编写失败测试
依赖: F04 Temporal工作流引擎, F01 不可变日志
"""


import pytest

from f28_monitoring_dashboard import (
    HealthStatus,
    MonitoringDashboard,
    WorkflowMetrics,
)


class TestMonitoringDashboardBasic:
    """测试监控仪表盘基本功能"""

    def test_init_creates_empty_metrics(self):
        """F28-UT001: 初始化时指标为空字典"""
        md = MonitoringDashboard()
        assert md.metrics == {}

    def test_init_creates_empty_alerts(self):
        """F28-UT002: 初始化时告警列表为空"""
        md = MonitoringDashboard()
        assert md.alerts == []


class TestRecordMetric:
    """测试记录指标"""

    def test_record_metric_stores_value(self):
        """F28-UT003: 记录指标存储值"""
        md = MonitoringDashboard()
        md.record_metric("cpu_usage", 75.5)
        assert md.metrics["cpu_usage"] == 75.5

    def test_record_metric_updates_existing(self):
        """F28-UT004: 记录指标更新现有值"""
        md = MonitoringDashboard()
        md.record_metric("cpu_usage", 75.5)
        md.record_metric("cpu_usage", 80.0)
        assert md.metrics["cpu_usage"] == 80.0

    def test_record_metric_supports_multiple_metrics(self):
        """F28-UT005: 支持多个不同指标"""
        md = MonitoringDashboard()
        md.record_metric("cpu_usage", 75.5)
        md.record_metric("memory_usage", 60.0)
        md.record_metric("disk_usage", 50.0)
        assert len(md.metrics) == 3


class TestHealthStatus:
    """测试健康状态"""

    def test_get_health_status_returns_health_status_type(self):
        """F28-UT006: 获取健康状态返回HealthStatus类型"""
        md = MonitoringDashboard()
        status = md.get_health_status()
        assert isinstance(status, HealthStatus)

    def test_get_health_status_has_status_field(self):
        """F28-UT007: 健康状态包含status字段"""
        md = MonitoringDashboard()
        status = md.get_health_status()
        assert hasattr(status, "status")

    def test_get_health_status_has_timestamp_field(self):
        """F28-UT008: 健康状态包含timestamp字段"""
        md = MonitoringDashboard()
        status = md.get_health_status()
        assert hasattr(status, "timestamp")

    def test_get_health_status_has_message_field(self):
        """F28-UT009: 健康状态包含message字段"""
        md = MonitoringDashboard()
        status = md.get_health_status()
        assert hasattr(status, "message")

    def test_get_health_status_healthy_when_no_issues(self):
        """F28-UT010: 无问题时健康状态为healthy"""
        md = MonitoringDashboard()
        status = md.get_health_status()
        assert status.status == "healthy"


class TestLogIntegrityCheck:
    """测试日志完整性检查"""

    def test_check_log_integrity_returns_bool(self):
        """F28-UT011: 日志完整性检查返回布尔值"""
        md = MonitoringDashboard()
        result = md.check_log_integrity()
        assert isinstance(result, bool)

    def test_check_log_integrity_returns_true_for_valid_log(self):
        """F28-UT012: 有效日志返回True"""
        md = MonitoringDashboard()
        result = md.check_log_integrity()
        assert result is True


class TestWorkflowMetrics:
    """测试工作流指标"""

    def test_get_workflow_metrics_returns_workflow_metrics_type(self):
        """F28-UT013: 获取工作流指标返回WorkflowMetrics类型"""
        md = MonitoringDashboard()
        metrics = md.get_workflow_metrics()
        assert isinstance(metrics, WorkflowMetrics)

    def test_get_workflow_metrics_has_active_count_field(self):
        """F28-UT014: 工作流指标包含活跃数量字段"""
        md = MonitoringDashboard()
        metrics = md.get_workflow_metrics()
        assert hasattr(metrics, "active_count")

    def test_get_workflow_metrics_has_completed_count_field(self):
        """F28-UT015: 工作流指标包含完成数量字段"""
        md = MonitoringDashboard()
        metrics = md.get_workflow_metrics()
        assert hasattr(metrics, "completed_count")

    def test_get_workflow_metrics_has_failed_count_field(self):
        """F28-UT016: 工作流指标包含失败数量字段"""
        md = MonitoringDashboard()
        metrics = md.get_workflow_metrics()
        assert hasattr(metrics, "failed_count")


class TestAlerts:
    """测试告警功能"""

    def test_add_alert_creates_alert(self):
        """F28-UT017: 添加告警创建告警对象"""
        md = MonitoringDashboard()
        md.add_alert("warning", "CPU使用率过高", {"cpu": 95})
        assert len(md.alerts) == 1
        assert md.alerts[0].level == "warning"

    def test_add_alert_records_message(self):
        """F28-UT018: 添加告警记录消息"""
        md = MonitoringDashboard()
        md.add_alert("error", "内存不足", {})
        assert md.alerts[0].message == "内存不足"

    def test_add_alert_records_metadata(self):
        """F28-UT019: 添加告警记录元数据"""
        md = MonitoringDashboard()
        md.add_alert("critical", "服务不可用", {"service": "api", "count": 3})
        assert md.alerts[0].metadata["service"] == "api"

    def test_add_alert_records_timestamp(self):
        """F28-UT020: 添加告警记录时间戳"""
        md = MonitoringDashboard()
        md.add_alert("info", "测试告警", {})
        assert md.alerts[0].timestamp is not None


class TestMetricAggregation:
    """测试指标聚合"""

    def test_get_average_metric_returns_float(self):
        """F28-UT021: 获取平均指标返回浮点数"""
        md = MonitoringDashboard()
        md.record_metric("response_time", 100)
        md.record_metric("response_time", 200)
        avg = md.get_average_metric("response_time")
        assert isinstance(avg, float)

    def test_get_average_metric_calculates_correctly(self):
        """F28-UT022: 平均指标计算正确"""
        md = MonitoringDashboard()
        md.record_metric("response_time", 100)
        md.record_metric("response_time", 200)
        avg = md.get_average_metric("response_time")
        assert avg == 150.0

    def test_get_average_metric_returns_none_for_unknown(self):
        """F28-UT023: 获取未知指标平均返回None"""
        md = MonitoringDashboard()
        result = md.get_average_metric("unknown")
        assert result is None


class TestThresholdAlerting:
    """测试阈值告警"""

    def test_check_threshold_creates_alert_when_exceeded(self):
        """F28-UT024: 超过阈值时创建告警"""
        md = MonitoringDashboard()
        md.record_metric("cpu_usage", 95)
        md.check_threshold("cpu_usage", threshold=80, level="warning")
        assert len(md.alerts) >= 1

    def test_check_threshold_does_not_alert_when_below(self):
        """F28-UT025: 低于阈值时不告警"""
        md = MonitoringDashboard()
        md.record_metric("cpu_usage", 50)
        md.check_threshold("cpu_usage", threshold=80, level="warning")
        alert_levels = [a.level for a in md.alerts if a.message == "cpu_usage exceeded threshold"]
        assert "warning" not in alert_levels


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
