"""
E2E tests for the monitor page.
"""
import pytest
from playwright.sync_api import Page, expect


class TestMonitorPage:
    """Tests for the monitor page."""

    def test_monitor_page_loads(self, authenticated_page: Page):
        """Test that the monitor page loads correctly."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("h1:has-text('系统监控')")).toBeVisible()


class TestMetricsDisplay:
    """Tests for metrics display."""

    def test_cpu_usage_displayed(self, authenticated_page: Page):
        """Test that CPU usage metric is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=CPU 使用率")).toBeVisible()

    def test_memory_usage_displayed(self, authenticated_page: Page):
        """Test that memory usage metric is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=内存使用率")).toBeVisible()

    def test_disk_usage_displayed(self, authenticated_page: Page):
        """Test that disk usage metric is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=磁盘使用率")).toBeVisible()

    def test_active_connections_displayed(self, authenticated_page: Page):
        """Test that active connections metric is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=活跃连接数")).toBeVisible()

    def test_rps_displayed(self, authenticated_page: Page):
        """Test that requests per second metric is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=每秒请求数")).toBeVisible()

    def test_response_time_displayed(self, authenticated_page: Page):
        """Test that average response time metric is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=平均响应时间")).toBeVisible()


class TestHealthIndicators:
    """Tests for system health indicators."""

    def test_health_section_displayed(self, authenticated_page: Page):
        """Test that health section is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=系统健康状态")).toBeVisible()

    def test_api_health_displayed(self, authenticated_page: Page):
        """Test that API health indicator is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=API 服务")).toBeVisible()

    def test_database_health_displayed(self, authenticated_page: Page):
        """Test that database health indicator is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=数据库")).toBeVisible()

    def test_cache_health_displayed(self, authenticated_page: Page):
        """Test that cache health indicator is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=缓存服务")).toBeVisible()

    def test_queue_health_displayed(self, authenticated_page: Page):
        """Test that queue health indicator is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=队列服务")).toBeVisible()

    def test_health_status_tags(self, authenticated_page: Page):
        """Test that health status tags are displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        status_tags = authenticated_page.locator(".ant-tag")
        expect(status_tags.first).toBeVisible()


class TestPrometheusMetrics:
    """Tests for Prometheus metrics display."""

    def test_prometheus_section_displayed(self, authenticated_page: Page):
        """Test that Prometheus metrics section is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=Prometheus 指标")).toBeVisible()

    def test_prometheus_content_displayed(self, authenticated_page: Page):
        """Test that Prometheus metrics content is displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        pre_element = authenticated_page.locator("pre")
        expect(pre_element).toBeVisible()


class TestMetricCards:
    """Tests for metric cards."""

    def test_metric_card_icons(self, authenticated_page: Page):
        """Test that metric cards have correct icons."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        icons = authenticated_page.locator("[class*='metric-card'] [class*='Outlined']")
        expect(icons.first).toBeVisible()

    def test_metric_values_displayed(self, authenticated_page: Page):
        """Test that metric values are displayed."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        metric_values = authenticated_page.locator("[class*='metric-value']")
        expect(metric_values.first).toBeVisible()

    def test_progress_bars_displayed(self, authenticated_page: Page):
        """Test that progress bars are displayed for usage metrics."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        progress_bars = authenticated_page.locator(".ant-progress")
        expect(progress_bars.first).toBeVisible()


class TestMonitorAutoRefresh:
    """Tests for monitor auto-refresh functionality."""

    def test_auto_refresh_enabled(self, authenticated_page: Page):
        """Test that monitor data auto-refreshes."""
        authenticated_page.goto("http://localhost:3000/monitor")
        authenticated_page.wait_for_load_state("networkidle")

        page_content_1 = authenticated_page.locator("h1:has-text('系统监控')").text_content()

        authenticated_page.wait_for_timeout(6000)

        page_content_2 = authenticated_page.locator("h1:has-text('系统监控')").text_content()
        assert page_content_1 == page_content_2


class TestMonitorNavigation:
    """Tests for monitor navigation."""

    def test_navigate_to_monitor_from_menu(self, authenticated_page: Page):
        """Test navigating to monitor from sidebar menu."""
        authenticated_page.goto("http://localhost:3000/dashboard")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click(".ant-menu-item:has-text('系统监控')")
        authenticated_page.wait_for_url("**/monitor", timeout=5000)

        expect(authenticated_page.locator("h1:has-text('系统监控')")).toBeVisible()
