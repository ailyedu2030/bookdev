"""
Monitoring API Integration Tests

Tests for monitoring endpoints with proper admin authentication:
- GET /api/monitor/health - Health check
- GET /api/monitor/logs - Audit logs
- ImportError fallback paths
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys


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
        self, test_client,
    ):
        """Test health check includes component statuses"""
        response = test_client.get("/api/monitor/health")

        assert response.status_code == 200
        data = response.json()
        assert "components" in data


class TestLogsImportErrorFallbacks:
    """Tests for ImportError fallback paths in get_logs"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for logs endpoint"""
        user = MagicMock()
        user.id = "test-user"
        user.username = "testuser"
        return user

    def test_logs_fallback_no_immutable_log(self, mock_user):
        """Test logs returns empty list when f01_immutable_log not available"""
        from api.routes.monitor import get_logs
        import asyncio

        with patch.dict("sys.modules", {"f01_immutable_log": None, "f01_immutable_log.immutable_log": None}):
            result = asyncio.get_event_loop().run_until_complete(
                get_logs(page=1, per_page=50, event_type=None, user_id=None,
                         resource_type=None, start_date=None, end_date=None, user=mock_user)
            )
            assert isinstance(result, list)
            assert len(result) == 0


class TestAlertsImportErrorFallbacks:
    """Tests for ImportError fallback paths in get_alerts"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for alerts endpoint"""
        user = MagicMock()
        user.id = "test-user"
        user.username = "testuser"
        return user

    def test_alerts_fallback_no_monitoring_dashboard(self, mock_user):
        """Test alerts returns empty list when f28_monitoring_dashboard not available"""
        from api.routes.monitor import get_alerts
        import asyncio

        with patch.dict("sys.modules", {"f28_monitoring_dashboard": None, "f28_monitoring_dashboard.monitoring_dashboard": None}):
            result = asyncio.get_event_loop().run_until_complete(
                get_alerts(severity=None, resolved=None, user=mock_user)
            )
            assert result["success"] is True
            assert "alerts" in result
            assert len(result["alerts"]) == 0


class TestWorkflowStatsImportErrorFallbacks:
    """Tests for ImportError fallback paths in get_workflow_stats"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for workflow stats endpoint"""
        user = MagicMock()
        user.id = "test-user"
        user.username = "testuser"
        return user

    def test_workflow_stats_fallback_no_temporal_workflow(self, mock_user):
        """Test workflow stats uses default values when f04_temporal_workflow not available"""
        from api.routes.monitor import get_workflow_stats
        import asyncio

        with patch.dict("sys.modules", {"f04_temporal_workflow": None, "f04_temporal_workflow.workflows": None}):
            result = asyncio.get_event_loop().run_until_complete(
                get_workflow_stats(user=mock_user)
            )
            assert result["success"] is True
            assert "data" in result
            assert result["data"]["total_workflows"] == 0


class TestDashboardSummaryImportErrorFallbacks:
    """Tests for ImportError fallback paths in get_dashboard_summary"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for dashboard summary endpoint"""
        user = MagicMock()
        user.id = "test-user"
        user.username = "testuser"
        return user

    def test_dashboard_summary_fallback_no_monitoring_dashboard(self, mock_user):
        """Test dashboard summary uses fallback when f28_monitoring_dashboard not available"""
        from api.routes.monitor import get_dashboard_summary
        import asyncio

        with patch.dict("sys.modules", {"f28_monitoring_dashboard": None, "f28_monitoring_dashboard.monitoring_dashboard": None}):
            result = asyncio.get_event_loop().run_until_complete(
                get_dashboard_summary(user=mock_user)
            )
            assert result["success"] is True
            assert "data" in result
            assert result["data"]["total_projects"] == 0


class TestAppendLogImportErrorFallbacks:
    """Tests for ImportError fallback paths in append_log"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for append log endpoint"""
        user = MagicMock()
        user.id = "test-user"
        user.username = "testuser"
        return user

    def test_append_log_fallback_no_immutable_log(self, mock_user):
        """Test append log returns mock response when f01_immutable_log not available"""
        from api.routes.monitor import append_log
        import asyncio

        with patch.dict("sys.modules", {"f01_immutable_log": None, "f01_immutable_log.immutable_log": None}):
            result = asyncio.get_event_loop().run_until_complete(
                append_log(event_type="TEST_EVENT", details={"test": "data"}, user=mock_user)
            )
            assert result.success is True
            assert "Mock mode" in result.message


class TestHealthCheckDirectImportErrorCoverage:
    """Direct tests for ImportError fallback in health_check by patching __import__"""

    def test_health_check_f28_import_triggers_fallback(self):
        """Test that ImportError for f28 triggers fallback"""
        from api.routes import monitor
        import asyncio

        original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if "f28_monitoring_dashboard" in name:
                raise ImportError(f"No module named {name}")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = asyncio.get_event_loop().run_until_complete(monitor.health_check())
            assert "dashboard" in result.components

    def test_health_check_f01_import_triggers_fallback(self):
        """Test that ImportError for f01 triggers fallback"""
        from api.routes import monitor
        import asyncio

        original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if "f01_immutable_log" in name:
                raise ImportError(f"No module named {name}")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = asyncio.get_event_loop().run_until_complete(monitor.health_check())
            assert "immutable_log" in result.components

    def test_health_check_f02_import_triggers_fallback(self):
        """Test that ImportError for f02 triggers fallback"""
        from api.routes import monitor
        import asyncio

        original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if "f02_context_budget" in name:
                raise ImportError(f"No module named {name}")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = asyncio.get_event_loop().run_until_complete(monitor.health_check())
            assert "context_budget" in result.components


class TestLogsDirectImportErrorCoverage:
    """Direct tests for ImportError fallback in get_logs"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for logs endpoint"""
        user = MagicMock()
        user.id = "test-user"
        user.username = "testuser"
        return user

    def test_logs_f01_import_triggers_fallback(self, mock_user):
        """Test that ImportError for f01 triggers fallback"""
        from api.routes import monitor
        import asyncio

        original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if "f01_immutable_log" in name:
                raise ImportError(f"No module named {name}")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = asyncio.get_event_loop().run_until_complete(
                monitor.get_logs(page=1, per_page=50, event_type=None, user_id=None,
                                 resource_type=None, start_date=None, end_date=None, user=mock_user)
            )
            assert result == []


class TestAlertsDirectImportErrorCoverage:
    """Direct tests for ImportError fallback in get_alerts"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for alerts endpoint"""
        user = MagicMock()
        user.id = "test-user"
        user.username = "testuser"
        return user

    def test_alerts_f28_import_triggers_fallback(self, mock_user):
        """Test that ImportError for f28 triggers fallback"""
        from api.routes import monitor
        import asyncio

        original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if "f28_monitoring_dashboard" in name:
                raise ImportError(f"No module named {name}")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = asyncio.get_event_loop().run_until_complete(
                monitor.get_alerts(severity=None, resolved=None, user=mock_user)
            )
            assert result["success"] is True
            assert result["alerts"] == []


class TestWorkflowStatsDirectImportErrorCoverage:
    """Direct tests for ImportError fallback in get_workflow_stats"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for workflow stats endpoint"""
        user = MagicMock()
        user.id = "test-user"
        user.username = "testuser"
        return user

    def test_workflow_stats_f04_import_triggers_fallback(self, mock_user):
        """Test that ImportError for f04 triggers fallback"""
        from api.routes import monitor
        import asyncio

        original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if "f04_temporal_workflow" in name:
                raise ImportError(f"No module named {name}")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = asyncio.get_event_loop().run_until_complete(
                monitor.get_workflow_stats(user=mock_user)
            )
            assert result["success"] is True
            assert result["data"]["total_workflows"] == 0


class TestDashboardSummaryDirectImportErrorCoverage:
    """Direct tests for ImportError fallback in get_dashboard_summary"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for dashboard summary endpoint"""
        user = MagicMock()
        user.id = "test-user"
        user.username = "testuser"
        return user

    def test_dashboard_summary_f28_import_triggers_fallback(self, mock_user):
        """Test that ImportError for f28 triggers fallback"""
        from api.routes import monitor
        import asyncio

        original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if "f28_monitoring_dashboard" in name:
                raise ImportError(f"No module named {name}")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = asyncio.get_event_loop().run_until_complete(
                monitor.get_dashboard_summary(user=mock_user)
            )
            assert result["success"] is True
            assert result["data"]["total_projects"] == 0


class TestAppendLogDirectImportErrorCoverage:
    """Direct tests for ImportError fallback in append_log"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for append log endpoint"""
        user = MagicMock()
        user.id = "test-user"
        user.username = "testuser"
        return user

    def test_append_log_f01_import_triggers_fallback(self, mock_user):
        """Test that ImportError for f01 triggers fallback"""
        from api.routes import monitor
        import asyncio

        original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if "f01_immutable_log" in name:
                raise ImportError(f"No module named {name}")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = asyncio.get_event_loop().run_until_complete(
                monitor.append_log(event_type="TEST_EVENT", details={"test": "data"}, user=mock_user)
            )
            assert result.success is True


class TestHealthCheckMultipleImportErrorCoverage:
    """Test combinations of ImportError fallbacks"""

    def test_health_check_all_imports_fail(self):
        """Test health check when all three imports fail - status should be degraded since all are unknown"""
        from api.routes import monitor
        import asyncio

        original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if any(mod in name for mod in ["f28_monitoring_dashboard", "f01_immutable_log", "f02_context_budget"]):
                raise ImportError(f"No module named {name}")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = asyncio.get_event_loop().run_until_complete(monitor.health_check())
            assert result.components["dashboard"]["status"] == "unknown"
            assert result.components["immutable_log"]["status"] == "unknown"
            assert result.components["context_budget"]["status"] == "unknown"


class TestMetricsMultipleImportErrorCoverage:
    """Test combinations of ImportError fallbacks in metrics"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for metrics endpoint"""
        user = MagicMock()
        user.id = "test-user"
        user.username = "testuser"
        return user

    def test_metrics_all_imports_fail(self, mock_user):
        """Test metrics when all three imports fail"""
        from api.routes import monitor
        import asyncio

        original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if any(mod in name for mod in ["f28_monitoring_dashboard", "f31_minimax_client", "f02_context_budget"]):
                raise ImportError(f"No module named {name}")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = asyncio.get_event_loop().run_until_complete(monitor.get_metrics(user=mock_user))
            assert result.success is True
            assert result.data.get("llm_usage", {}).get("error") == "Module not available"
            assert result.data.get("context_budget", {}).get("error") == "Module not available"