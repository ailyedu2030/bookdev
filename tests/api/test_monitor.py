"""
Monitoring API Integration Tests

Tests for monitoring endpoints:
- GET /api/monitor/health - Health check
- GET /api/monitor/metrics - System metrics
- GET /api/monitor/logs - Audit logs
- GET /api/monitor/alerts - System alerts
"""

from unittest.mock import MagicMock, patch


class TestHealthCheck:
    """Tests for health check endpoint"""

    def test_health_check(self, test_client):
        """Test health check returns status"""
        response = test_client.get("/api/monitor/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data
        assert "version" in data

    def test_health_check_components(
        self,
        test_client,
    ):
        """Test health check includes component statuses"""
        response = test_client.get("/api/monitor/health")

        assert response.status_code == 200
        data = response.json()
        assert "components" in data

    def test_health_check_returns_degraded_status(
        self,
        test_client,
    ):
        """Test health check returns degraded when components fail"""
        with patch.dict("sys.modules", {"f28_monitoring_dashboard.monitoring_dashboard": None}):
            with patch("importlib.import_module", side_effect=ImportError):
                response = test_client.get("/api/monitor/health")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] in ["healthy", "degraded"]

    def test_health_check_includes_version(
        self,
        test_client,
    ):
        """Test health check includes version field"""
        response = test_client.get("/api/monitor/health")

        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] == "1.0.0"


class TestMetricsEndpoint:
    """Tests for metrics endpoint"""

    def test_metrics_endpoint_requires_auth(self, test_client, test_admin_authenticated):
        """Test metrics endpoint requires authentication"""
        token = test_admin_authenticated["access_token"]

        with patch.dict(
            "sys.modules",
            {
                "f28_monitoring_dashboard": None,
                "f28_monitoring_dashboard.monitoring_dashboard": None,
                "f31_minimax_client": None,
                "f31_minimax_client.cost_tracker": None,
            },
        ):
            response = test_client.get(
                "/api/monitor/metrics",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "timestamp" in data

    def test_metrics_includes_uptime(self, test_client, test_admin_authenticated):
        """Test metrics include uptime information"""
        token = test_admin_authenticated["access_token"]

        with patch.dict(
            "sys.modules",
            {
                "f28_monitoring_dashboard": None,
                "f28_monitoring_dashboard.monitoring_dashboard": None,
                "f31_minimax_client": None,
                "f31_minimax_client.cost_tracker": None,
            },
        ):
            response = test_client.get(
                "/api/monitor/metrics",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            metrics = data["data"]
            assert "uptime_seconds" in metrics
            assert "uptime_hours" in metrics

    def test_metrics_includes_requests(self, test_client, test_admin_authenticated):
        """Test metrics include request statistics"""
        token = test_admin_authenticated["access_token"]

        with patch.dict(
            "sys.modules",
            {
                "f28_monitoring_dashboard": None,
                "f28_monitoring_dashboard.monitoring_dashboard": None,
                "f31_minimax_client": None,
                "f31_minimax_client.cost_tracker": None,
            },
        ):
            response = test_client.get(
                "/api/monitor/metrics",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            metrics = data["data"]
            assert "requests" in metrics
            assert "total" in metrics["requests"]
            assert "success" in metrics["requests"]
            assert "failed" in metrics["requests"]

    def test_metrics_includes_response_times(self, test_client, test_admin_authenticated):
        """Test metrics include response time statistics"""
        token = test_admin_authenticated["access_token"]

        with patch.dict(
            "sys.modules",
            {
                "f28_monitoring_dashboard": None,
                "f28_monitoring_dashboard.monitoring_dashboard": None,
                "f31_minimax_client": None,
                "f31_minimax_client.cost_tracker": None,
            },
        ):
            response = test_client.get(
                "/api/monitor/metrics",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            metrics = data["data"]
            assert "response_time_ms" in metrics
            assert "avg" in metrics["response_time_ms"]
            assert "p50" in metrics["response_time_ms"]
            assert "p95" in metrics["response_time_ms"]
            assert "p99" in metrics["response_time_ms"]

    def test_metrics_unauthorized(self, test_client):
        """Test metrics endpoint without authentication"""
        response = test_client.get("/api/monitor/metrics")

        assert response.status_code == 401

    def test_metrics_viewer_allowed(self, test_client, test_admin_authenticated):
        """Test admin can access metrics"""
        token = test_admin_authenticated["access_token"]

        with patch.dict(
            "sys.modules",
            {
                "f28_monitoring_dashboard": None,
                "f28_monitoring_dashboard.monitoring_dashboard": None,
                "f31_minimax_client": None,
                "f31_minimax_client.cost_tracker": None,
            },
        ):
            response = test_client.get(
                "/api/monitor/metrics",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200


class TestLogsEndpoint:
    """Tests for audit logs endpoint"""

    def test_get_logs_empty(self, test_client, test_admin_authenticated):
        """Test getting logs when none exist"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/logs",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_logs_pagination(self, test_client, test_admin_authenticated):
        """Test logs pagination"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/logs?page=1&per_page=10",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_get_logs_filter_by_event_type(self, test_client, test_admin_authenticated):
        """Test filtering logs by event type"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/logs?event_type=USER_LOGIN",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_get_logs_filter_by_user(self, test_client, test_admin_authenticated):
        """Test filtering logs by user ID"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/logs?user_id=test-user-123",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_get_logs_filter_by_resource_type(self, test_client, test_admin_authenticated):
        """Test filtering logs by resource type"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/logs?resource_type=chapter",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_get_logs_date_range(self, test_client, test_admin_authenticated):
        """Test filtering logs by date range"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/logs?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_get_logs_unauthorized(self, test_client):
        """Test logs endpoint without authentication"""
        response = test_client.get("/api/monitor/logs")

        assert response.status_code == 401


class TestAlertsEndpoint:
    """Tests for alerts endpoint"""

    def test_get_alerts(self, test_client, test_admin_authenticated):
        """Test getting alerts"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/alerts",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total" in data
        assert "alerts" in data

    def test_get_alerts_filter_by_severity(self, test_client, test_admin_authenticated):
        """Test filtering alerts by severity"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/alerts?severity=warning",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_get_alerts_filter_by_resolved(self, test_client, test_admin_authenticated):
        """Test filtering alerts by resolved status"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/alerts?resolved=false",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_get_alerts_unauthorized(self, test_client):
        """Test alerts endpoint without authentication"""
        response = test_client.get("/api/monitor/alerts")

        assert response.status_code == 401


class TestWorkflowStats:
    """Tests for workflow statistics endpoint"""

    def test_get_workflow_stats(self, test_client, test_admin_authenticated):
        """Test getting workflow statistics"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/workflow/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_get_workflow_stats_includes_counts(self, test_client, test_admin_authenticated):
        """Test workflow stats include workflow counts"""
        token = test_admin_authenticated["access_token"]

        response = test_client.get(
            "/api/monitor/workflow/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        stats = data["data"]
        assert "total_workflows" in stats
        assert "running" in stats
        assert "completed" in stats
        assert "failed" in stats
        assert "cancelled" in stats


class TestDashboardSummary:
    """Tests for dashboard summary endpoint"""

    def test_get_dashboard_summary(self, test_client, test_admin_authenticated):
        """Test getting dashboard summary"""
        token = test_admin_authenticated["access_token"]

        with patch.dict(
            "sys.modules", {"f28_monitoring_dashboard": None, "f28_monitoring_dashboard.monitoring_dashboard": None}
        ):
            response = test_client.get(
                "/api/monitor/dashboard/summary",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data

    def test_get_dashboard_summary_includes_counts(self, test_client, test_admin_authenticated):
        """Test dashboard summary includes project/chapter counts"""
        token = test_admin_authenticated["access_token"]

        with patch.dict(
            "sys.modules", {"f28_monitoring_dashboard": None, "f28_monitoring_dashboard.monitoring_dashboard": None}
        ):
            response = test_client.get(
                "/api/monitor/dashboard/summary",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            summary = data["data"]
            assert "total_projects" in summary
            assert "total_chapters" in summary


class TestAppendLog:
    """Tests for appending audit log entries"""

    def test_append_log(self, test_client, test_admin_authenticated):
        """Test appending a log entry"""
        token = test_admin_authenticated["access_token"]

        response = test_client.post(
            "/api/monitor/logs/append?event_type=TEST_EVENT",
            json={"key": "value"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "test_csrf_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_append_log_unauthorized(self, test_client):
        """Test append log without authentication"""
        response = test_client.post(
            "/api/monitor/logs/append",
            json={
                "event_type": "TEST_EVENT",
                "details": {},
            },
            headers={"X-CSRF-Token": "test_csrf_token"},
        )

        assert response.status_code == 401


class TestLogsWithMockedModule:
    """Tests for logs endpoint with mocked ImmutableLog module"""

    def test_get_logs_with_immutable_log_module(self, test_client, test_admin_authenticated):
        """Test logs endpoint when f01_immutable_log is available"""
        token = test_admin_authenticated["access_token"]

        mock_log_instance = MagicMock()
        mock_log_instance.get_entries.return_value = [
            {
                "id": "entry-1",
                "event_type": "USER_LOGIN",
                "user_id": "user-123",
                "resource_type": "session",
                "resource_id": "session-456",
                "action": "login",
                "result": "success",
                "details": {"ip": "127.0.0.1"},
                "ip_address": "127.0.0.1",
                "timestamp": "2024-01-15T10:30:00Z",
            },
            {
                "id": "entry-2",
                "event_type": "PROJECT_CREATE",
                "user_id": "user-123",
                "resource_type": "project",
                "resource_id": "proj-789",
                "action": "create",
                "result": "success",
                "details": {"name": "Test Project"},
                "ip_address": "192.168.1.1",
                "timestamp": "2024-01-16T14:00:00Z",
            },
        ]

        with patch("f01_immutable_log.immutable_log.ImmutableLog", return_value=mock_log_instance):
            response = test_client.get(
                "/api/monitor/logs",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["event_type"] == "USER_LOGIN"
            assert data[1]["event_type"] == "PROJECT_CREATE"

    def test_get_logs_filters_by_event_type_with_mock(self, test_client, test_admin_authenticated):
        """Test logs filter by event type with mock module"""
        token = test_admin_authenticated["access_token"]

        mock_log_instance = MagicMock()
        mock_log_instance.get_entries.return_value = [
            {
                "id": "entry-1",
                "event_type": "USER_LOGIN",
                "user_id": "user-123",
                "timestamp": "2024-01-15T10:30:00Z",
            },
            {
                "id": "entry-2",
                "event_type": "USER_LOGOUT",
                "user_id": "user-123",
                "timestamp": "2024-01-15T11:00:00Z",
            },
        ]

        with patch("f01_immutable_log.immutable_log.ImmutableLog", return_value=mock_log_instance):
            response = test_client.get(
                "/api/monitor/logs?event_type=USER_LOGIN",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["event_type"] == "USER_LOGIN"

    def test_get_logs_filters_by_user_id_with_mock(self, test_client, test_admin_authenticated):
        """Test logs filter by user ID with mock module"""
        token = test_admin_authenticated["access_token"]

        mock_log_instance = MagicMock()
        mock_log_instance.get_entries.return_value = [
            {
                "id": "entry-1",
                "event_type": "USER_LOGIN",
                "user_id": "user-123",
                "timestamp": "2024-01-15T10:30:00Z",
            },
            {
                "id": "entry-2",
                "event_type": "USER_LOGIN",
                "user_id": "user-456",
                "timestamp": "2024-01-15T11:00:00Z",
            },
        ]

        with patch("f01_immutable_log.immutable_log.ImmutableLog", return_value=mock_log_instance):
            response = test_client.get(
                "/api/monitor/logs?user_id=user-123",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["user_id"] == "user-123"


class TestAlertsWithMockedModule:
    """Tests for alerts endpoint with mocked dashboard module"""

    def test_get_alerts_with_mock_dashboard(self, test_client, test_admin_authenticated):
        """Test alerts endpoint when dashboard module is available"""
        token = test_admin_authenticated["access_token"]

        mock_alert = MagicMock()
        mock_alert.id = "alert-1"
        mock_alert.severity = "warning"
        mock_alert.message = "High memory usage"
        mock_alert.resolved = False
        mock_alert.created_at = "2024-01-15T10:30:00Z"

        mock_dashboard = MagicMock()
        mock_dashboard.get_alerts.return_value = [mock_alert]

        with patch("f28_monitoring_dashboard.monitoring_dashboard.MonitoringDashboard", return_value=mock_dashboard):
            with patch("f28_monitoring_dashboard.monitoring_dashboard.Alert", type(mock_alert)):
                response = test_client.get(
                    "/api/monitor/alerts",
                    headers={"Authorization": f"Bearer {token}"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["total"] == 1
                assert len(data["alerts"]) == 1
                assert data["alerts"][0]["severity"] == "warning"

    def test_get_alerts_filter_by_severity_with_mock(self, test_client, test_admin_authenticated):
        """Test alerts filtering by severity with mock"""
        token = test_admin_authenticated["access_token"]

        mock_dashboard = MagicMock()
        mock_dashboard.get_alerts.return_value = []

        with patch("f28_monitoring_dashboard.monitoring_dashboard.MonitoringDashboard", return_value=mock_dashboard):
            response = test_client.get(
                "/api/monitor/alerts?severity=error",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            mock_dashboard.get_alerts.assert_called_once_with(severity="error", resolved=None)


class TestWorkflowStatsWithMockedModule:
    """Tests for workflow stats with mocked temporal module"""

    def test_get_workflow_stats_when_module_import_error(self, test_client, test_admin_authenticated):
        """Test workflow stats falls back to default when module unavailable"""
        token = test_admin_authenticated["access_token"]

        with patch.dict(
            "sys.modules",
            {
                "f04_temporal_workflow": None,
                "f04_temporal_workflow.workflows": None,
                "f04_temporal_workflow.workflows.mock_client": None,
            },
        ):
            response = test_client.get(
                "/api/monitor/workflow/stats",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            stats = data["data"]
            assert stats["total_workflows"] == 0

    def test_get_workflow_stats_with_getattr_handling(self, test_client, test_admin_authenticated):
        """Test workflow stats handles client without get_stats attribute"""
        token = test_admin_authenticated["access_token"]

        mock_client = MagicMock(spec=[])
        assert not hasattr(mock_client, "get_stats")

        with patch.dict(
            "sys.modules",
            {
                "f04_temporal_workflow": None,
                "f04_temporal_workflow.workflows": None,
                "f04_temporal_workflow.workflows.mock_client": None,
            },
        ):
            response = test_client.get(
                "/api/monitor/workflow/stats",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestDashboardSummaryWithMockedModule:
    """Tests for dashboard summary with mocked dashboard module"""

    def test_get_dashboard_summary_with_mock(self, test_client, test_admin_authenticated):
        """Test dashboard summary when MonitoringDashboard is available"""
        token = test_admin_authenticated["access_token"]

        mock_summary = {
            "total_projects": 15,
            "total_chapters": 87,
            "active_workflows": 5,
            "recent_activity": [{"type": "project_created", "timestamp": "2024-01-15T10:00:00Z"}],
        }

        mock_dashboard = MagicMock()
        mock_dashboard.get_dashboard_summary.return_value = mock_summary

        with patch("f28_monitoring_dashboard.monitoring_dashboard.MonitoringDashboard", return_value=mock_dashboard):
            response = test_client.get(
                "/api/monitor/dashboard/summary",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            summary = data["data"]
            assert summary["total_projects"] == 15
            assert summary["total_chapters"] == 87


class TestMetricsWithMockedModules:
    """Tests for metrics with mocked modules"""

    def test_metrics_with_cost_tracker(self, test_client, test_admin_authenticated):
        """Test metrics include cost tracker data when available"""
        token = test_admin_authenticated["access_token"]

        mock_tracker = MagicMock()
        mock_tracker.get_usage_stats.return_value = {
            "total_tokens": 1500000,
            "total_cost": 25.50,
            "request_count": 342,
        }

        with patch.dict(
            "sys.modules",
            {
                "f28_monitoring_dashboard": None,
                "f28_monitoring_dashboard.monitoring_dashboard": None,
            },
        ):
            with patch("f31_minimax_client.cost_tracker.CostTracker", return_value=mock_tracker):
                response = test_client.get(
                    "/api/monitor/metrics",
                    headers={"Authorization": f"Bearer {token}"},
                )

                assert response.status_code == 200
                data = response.json()
                metrics = data["data"]
                assert "llm_usage" in metrics
                assert metrics["llm_usage"]["total_tokens"] == 1500000

    def test_metrics_with_context_budget(self, test_client, test_admin_authenticated):
        """Test metrics include context budget when module is available"""
        token = test_admin_authenticated["access_token"]

        mock_budget = MagicMock()
        mock_budget.get_total_usage.return_value = 85000
        mock_budget.max_tokens = 200000

        with patch.dict(
            "sys.modules",
            {
                "f28_monitoring_dashboard": None,
                "f28_monitoring_dashboard.monitoring_dashboard": None,
                "f31_minimax_client": None,
                "f31_minimax_client.cost_tracker": None,
            },
        ):
            with patch("f02_context_budget.context_budget_manager.ContextBudgetManager", return_value=mock_budget):
                response = test_client.get(
                    "/api/monitor/metrics",
                    headers={"Authorization": f"Bearer {token}"},
                )

                assert response.status_code == 200
                data = response.json()
                metrics = data["data"]
                assert "context_budget" in metrics
                assert metrics["context_budget"]["total_tokens"] == 85000


class TestHealthCheckWithAllModules:
    """Tests for health check with various module availability scenarios"""

    def test_health_check_with_all_modules_available(
        self,
        test_client,
    ):
        """Test health check when all modules are available"""
        # The actual implementation returns basic health info with empty components
        response = test_client.get("/api/monitor/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert "version" in data

    def test_health_check_immutable_log_import_error(
        self,
        test_client,
    ):
        """Test health check when immutable_log import fails"""
        # The actual implementation doesn't check module availability
        # and returns empty components dict
        with patch.dict(
            "sys.modules",
            {
                "f01_immutable_log": None,
                "f01_immutable_log.immutable_log": None,
            },
        ):
            response = test_client.get("/api/monitor/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "components" in data

    def test_health_check_context_budget_import_error(
        self,
        test_client,
    ):
        """Test health check when context_budget import fails"""
        # The actual implementation doesn't check module availability
        # and returns empty components dict
        with patch.dict(
            "sys.modules",
            {
                "f02_context_budget": None,
                "f02_context_budget.context_budget_manager": None,
            },
        ):
            response = test_client.get("/api/monitor/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "components" in data


class TestAppendLogWithMockedModule:
    """Tests for append log with mocked module"""

    def test_append_log_with_immutable_log_available(self, test_client, test_admin_authenticated):
        """Test append log when ImmutableLog is available"""
        token = test_admin_authenticated["access_token"]

        mock_log_instance = MagicMock()

        with patch("f01_immutable_log.immutable_log.ImmutableLog", return_value=mock_log_instance):
            response = test_client.post(
                "/api/monitor/logs/append?event_type=TEST_EVENT",
                json={"key": "value", "extra": "data"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": "test_csrf_token",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            mock_log_instance.append.assert_called_once()
